#!/usr/bin/env python
from __future__ import annotations

import datetime
import hashlib
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from sqlmodel import asc
from sqlmodel import col
from sqlmodel import select

from common import config
from common import schemas
from common import tables
from common.session import hs_transaction

if TYPE_CHECKING:
    from typing import Awaitable
    from typing import Callable

    from sqlmodel import Session
    from sqlmodel.sql.expression import SelectOfScalar


class UserLogic:
    USER = "User"
    SUPER_ADMIN = config.super_admin

    PERMISSIONS = (  # TODO: enum
        USER,
        SUPER_ADMIN,
    )

    def __init__(self, session: Session) -> None:
        self.session = session

    async def create_user(self, user_info: dict[str, str]) -> tables.User:
        user = {
            "email": user_info["email"],
            "user_type": self.USER,
            "active": True,
            "picture": user_info.get(
                "picture", "https://www.ishefi.com/images/favicon.ico"
            ),
            "given_name": user_info["given_name"],
            "family_name": user_info.get("family_name", ""),
            "first_login": datetime.datetime.utcnow(),
        }
        with hs_transaction(self.session, expire_on_commit=False) as session:
            db_user = tables.User(**user)
            session.add(db_user)
            return db_user

    async def get_user(self, email: str) -> tables.User | None:
        with hs_transaction(self.session, expire_on_commit=False) as session:
            query = select(tables.User).where(tables.User.email == email)
            return session.exec(query).one_or_none()

    @staticmethod
    def has_permissions(user: tables.User, permission: str) -> bool:
        return UserLogic.PERMISSIONS.index(
            user.user_type
        ) >= UserLogic.PERMISSIONS.index(permission)

    async def subscribe(self, subscription: schemas.Subscription) -> bool:
        # TODO: change logic to use sql
        user = await self.get_user(subscription.email)
        if user is None:
            return False

        with hs_transaction(self.session) as session:
            query = select(tables.UserSubscription)
            query = query.where(tables.UserSubscription.uuid == subscription.message_id)
            if session.exec(query).one_or_none() is None:
                session.add(
                    tables.UserSubscription(
                        user_id=user.id,
                        amount=subscription.amount,
                        tier_name=subscription.tier_name,
                        uuid=subscription.message_id,
                        timestamp=subscription.timestamp,
                    )
                )
                return True
            else:
                return False

    def get_subscription_expiry(self, user: tables.User) -> datetime.datetime | None:
        with hs_transaction(self.session, expire_on_commit=False) as session:
            query = select(tables.UserSubscription)
            query = query.where(tables.UserSubscription.user_id == user.id)
            query = query.order_by(asc(tables.UserSubscription.timestamp))
            subscriptions = session.exec(query).all()

        expiry = None
        now = datetime.datetime.utcnow()
        for subscription in subscriptions:
            if expiry is None:
                expiry = subscription.timestamp
            expiry += self._get_subscription_duration(subscription)
            if expiry < now:
                expiry = None
        return expiry

    @staticmethod
    def _get_subscription_duration(
        subscription: tables.UserSubscription,
    ) -> relativedelta:
        round_amount = round(subscription.amount)
        return relativedelta(
            months=round_amount // 3,  # one month per 3$
            days=10 * (round_amount % 3),  # 10 days per 1$ reminder
        )


class UserHistoryLogic:
    def __init__(
        self,
        session: Session,
        user: tables.User,
        date: datetime.date,
    ):
        self.session = session
        self.user = user
        self.dt = date  # TODO: use this
        self.date = str(date)

    @property
    def projection(self) -> dict[str, str]:
        return {"history": f"$history.{self.date}"}

    @property
    def user_filter(self) -> dict[str, str]:
        return {"email": self.user.email}

    async def update_and_get_history(
        self, guess: schemas.DistanceResponse
    ) -> list[schemas.DistanceResponse]:
        history = await self.get_history()
        if guess.similarity is not None:
            history.append(guess)
            with hs_transaction(self.session) as session:
                session.add(
                    tables.UserHistory(
                        user_id=self.user.id,
                        guess=guess.guess,
                        similarity=guess.similarity,
                        distance=guess.distance,
                        egg=guess.egg,
                        game_date=self.dt,
                        solver_count=guess.solver_count,
                    )
                )
            return history
        else:
            return [guess] + history

    async def get_history(self) -> list[schemas.DistanceResponse]:
        with hs_transaction(self.session, expire_on_commit=False) as session:
            history_query = select(tables.UserHistory)
            history_query = history_query.where(
                tables.UserHistory.user_id == self.user.id
            )
            history_query = history_query.where(
                tables.UserHistory.game_date == self.date
            )
            history_query = history_query.order_by(col(tables.UserHistory.id))
            history = session.exec(history_query).all()
        return [
            schemas.DistanceResponse(
                guess=historia.guess,
                similarity=historia.similarity,
                distance=historia.distance,
                egg=historia.egg,
                solver_count=historia.solver_count,
                guess_number=i,
            )
            for i, historia in enumerate(history, start=1)
        ]


class UserStatisticsLogic:
    def __init__(self, session: Session, user: tables.User):
        self.session = session
        self.user = user

    async def get_statistics(self) -> schemas.UserStatistics:
        stats_subquery = select(
            tables.UserHistory.similarity,
            tables.UserHistory.solver_count,
            func.row_number()
            .over(
                partition_by=[col(tables.UserHistory.game_date)],
                order_by=col(tables.UserHistory.id),
            )
            .label("guess_number"),
        )
        stats_subquery = stats_subquery.select_from(tables.UserHistory)
        stats_subquery = stats_subquery.where(
            tables.UserHistory.user_id == self.user.id
        )
        stats_sub = stats_subquery.subquery()
        stats_query = select(
            func.count(),
            func.min(stats_sub.c.solver_count),
            func.avg(stats_sub.c.guess_number),
        )
        stats_query = stats_query.select_from(stats_sub)
        stats_query = stats_query.where(stats_sub.c.similarity == 100)

        with hs_transaction(self.session, expire_on_commit=False) as session:
            stats = session.exec(stats_query).one_or_none()

        if stats is None:
            total_games_won, highest_rank, avg_guesses = 0, None, 0
        else:
            total_games_won, highest_rank, avg_guesses = stats

        game_streak, total_games_played = self._get_game_streak_and_total()

        return schemas.UserStatistics(
            game_streak=game_streak,
            highest_rank=highest_rank,
            total_games_played=total_games_played,
            total_games_won=total_games_won,
            average_guesses=avg_guesses,
        )

    def _get_game_streak_and_total(self) -> tuple[int, int]:
        dates_query = select(col(tables.UserHistory.game_date))
        dates_query = dates_query.where(tables.UserHistory.user_id == self.user.id)
        dates_query = dates_query.group_by(col(tables.UserHistory.game_date))
        dates_query = dates_query.order_by(col(tables.UserHistory.game_date).desc())
        with hs_transaction(session=self.session, expire_on_commit=False) as session:
            game_dates = session.exec(dates_query).all()

        date = datetime.datetime.utcnow().date()
        game_streak = 0
        for game_date in game_dates:
            if date == game_date:
                game_streak += 1
                date -= datetime.timedelta(days=1)
            else:
                break
        return game_streak, len(game_dates)


class UserClueLogic:
    CLUE_CHAR_FORMAT = 'המילה הסודית מכילה את האות "{clue_char}"'
    CLUE_LEN_FORMAT = "המילה הסודית מכילה {clue_len} אותיות"
    HOT_CLUE_FORMAT = "המילה '{hot_clue}' קרובה למילה הסודית"
    NO_MORE_CLUES_STR = "אין יותר רמזים"
    CLUE_COOLDOWN_FOR_UNSUBSCRIBED = datetime.timedelta(days=7)
    MAX_CLUES_DURING_COOLDOWN = 1
    HOT_CLUES_CACHE: dict[str, list[str]] = {}

    def __init__(
        self,
        session: Session,
        user: tables.User,
        secret: str,
        date: datetime.date,
    ):
        self.session = session
        self.user = user
        self.secret = secret
        self.date = date

    @property
    def clues(self) -> list[Callable[[], Awaitable[str]]]:
        return [
            self._get_clue_char,
            self._get_secret_len,
            *self._get_hot_clue_funcs(),
        ]

    @property
    def clues_used(self) -> int:
        with hs_transaction(self.session) as session:
            query = select(tables.UserClueCount.clue_count)
            query = query.where(tables.UserClueCount.user_id == self.user.id)
            query = query.where(tables.UserClueCount.game_date == self.date)
            return session.exec(query).one_or_none() or 0

    async def get_clue(self) -> str | None:
        if self.clues_used < len(self.clues):
            clue = await self.clues[self.clues_used]()
            await self._update_clue_usage()
            return clue
        else:
            return None

    async def get_all_clues_used(self) -> list[str]:
        clues = []
        for i in range(self.clues_used):
            clues.append(await self.clues[i]())
        return clues

    async def _used_max_clues_for_inactive(self) -> bool:
        # TODO: verify this logic is correct
        with hs_transaction(self.session) as session:
            query: SelectOfScalar[int] = select(
                func.sum(tables.UserClueCount.clue_count)
            )
            query = query.where(tables.UserClueCount.user_id == self.user.id)
            query = query.where(
                tables.UserClueCount.game_date
                > self.date - self.CLUE_COOLDOWN_FOR_UNSUBSCRIBED
            )
            used_clues = session.exec(query).one()
            return used_clues > self.MAX_CLUES_DURING_COOLDOWN

    async def _update_clue_usage(self) -> None:
        with hs_transaction(self.session) as session:
            clue_count_query = select(tables.UserClueCount).where(
                tables.UserClueCount.user_id == self.user.id,
                tables.UserClueCount.game_date == self.date,
            )
            clue_count = session.exec(clue_count_query).first()
            if clue_count is None:
                clue_count = tables.UserClueCount(
                    user_id=self.user.id,
                    game_date=self.date,
                    clue_count=1,
                )
            else:
                clue_count.clue_count += 1
            session.add(clue_count)

    async def _get_clue_char(self) -> str:
        digest = hashlib.md5(self.secret.encode()).hexdigest()
        clue_index = int(digest, 16) % len(self.secret)
        # TODO: deal with final letters?
        return self.CLUE_CHAR_FORMAT.format(clue_char=self.secret[clue_index])

    async def _get_secret_len(self) -> str:
        return self.CLUE_LEN_FORMAT.format(clue_len=len(self.secret))

    def _get_hot_clue_funcs(self) -> list[Callable[[], Awaitable[str]]]:
        def hot_clue_func_generator(hot_clue: str) -> Callable[[], Awaitable[str]]:
            async def get_hot_clue() -> str:
                return self.HOT_CLUE_FORMAT.format(hot_clue=hot_clue)

            return get_hot_clue

        hot_clues = self._get_hot_clues()
        return [hot_clue_func_generator(clue) for clue in hot_clues]

    def _get_hot_clues(self) -> list[str]:
        if self.secret not in self.HOT_CLUES_CACHE:
            with hs_transaction(self.session) as session:
                query = (
                    select(tables.HotClue)
                    .join(tables.SecretWord)
                    .where(tables.SecretWord.game_date == self.date)
                )
                hot_clues = session.exec(query).all()
                self.HOT_CLUES_CACHE[self.secret] = [
                    hot_clue.clue for hot_clue in hot_clues
                ]
        return self.HOT_CLUES_CACHE[self.secret]
