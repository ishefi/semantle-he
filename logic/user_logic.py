#!/usr/bin/env python
from __future__ import annotations

import datetime
import hashlib
import sys
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from sqlmodel import select

from common import config
from common import schemas
from common import tables
from common.logger import logger
from common.session import hs_transaction

if TYPE_CHECKING:
    from typing import Any
    from typing import Awaitable
    from typing import Callable

    import motor.core
    from sqlmodel import Session


class UserLogic:
    USER = "User"
    SUPER_ADMIN = config.super_admin

    PERMISSIONS = (  # TODO: enum
        USER,
        SUPER_ADMIN,
    )

    def __init__(
        self, mongo: motor.core.AgnosticDatabase[Any], session: Session
    ) -> None:
        self.mongo = mongo
        self.session = session

    async def create_user(self, user_info: dict[str, str]) -> dict[str, Any]:
        user = {
            "email": user_info["email"],
            "user_type": self.USER,
            "active": True,
            "picture": user_info["picture"],
            "given_name": user_info["given_name"],
            "family_name": user_info.get("family_name", ""),
            "first_login": datetime.datetime.utcnow(),
        }
        await self.mongo.users.insert_one(user)
        with hs_transaction(self.session) as session:
            session.add(tables.User(**user))
        return user

    async def get_user(self, email: str) -> dict[str, Any] | None:
        user: dict[str, Any] | None = await self.mongo.users.find_one(
            {"email": email}, {"history": 0}
        )
        if not user:
            return None
        subscription_expiry = user.get(
            "subscription_expiry", datetime.datetime.utcnow()
        )
        user["has_active_subscription"] = (
            subscription_expiry > datetime.datetime.utcnow()
        )
        return user

    @staticmethod
    def has_permissions(user: dict[str, Any], permission: str) -> bool:
        return UserLogic.PERMISSIONS.index(
            user["user_type"]
        ) >= UserLogic.PERMISSIONS.index(permission)

    async def subscribe(self, subscription: schemas.Subscription) -> bool:
        user = await self.get_user(subscription.email)  # TODO: deal with unknown users
        if user is None:
            return False
        if subscription.message_id in user.get("subscription_ids", []):
            return False
        now = datetime.datetime.utcnow()
        expiry = user.get("subscription_expiry", now)
        expiry = max(expiry, now)
        expiry += relativedelta(
            months=subscription.amount // 3,  # one month per 3$
            days=10 * (subscription.amount % 3),  # 10 days per 1$ reminder
        )
        await self.mongo.users.update_one(
            {"email": subscription.email},
            {
                "$set": {"subscription_expiry": expiry},
                "$push": {"subscription_ids": subscription.message_id},
            },
        )
        return True


class UserHistoryLogic:
    def __init__(
        self,
        mongo: motor.core.AgnosticDatabase[Any],
        session: Session,
        user: dict[str, Any],
        date: datetime.date,
    ):
        self.mongo = mongo
        self.session = session
        self.user = user
        self.dt = date  # TODO: use this
        self.date = str(date)

    @property
    def projection(self) -> dict[str, str]:
        return {"history": f"$history.{self.date}"}

    @property
    def user_filter(self) -> dict[str, str]:
        return {"email": self.user["email"]}

    async def update_and_get_history(
        self, guess: schemas.DistanceResponse
    ) -> list[schemas.DistanceResponse]:
        history = await self.get_history()
        if guess.similarity is not None:
            history.append(guess)
            with hs_transaction(self.session) as session:
                user_query = select(tables.User).where(
                    tables.User.email == self.user["email"]
                )
                user = session.exec(user_query).first()
                if user is None:
                    logger.warning("User not found")
                else:
                    session.add(
                        tables.UserHistory(
                            user_id=user.id,
                            guess=guess.guess,
                            similarity=guess.similarity,
                            distance=guess.distance,
                            egg=guess.egg,
                            game_date=self.dt,
                            solver_count=guess.solver_count,
                        )
                    )
            return await self._fix_history(history, update_db=True)
        else:
            return [guess] + history

    async def get_history(self) -> list[schemas.DistanceResponse]:
        user_data = await self.mongo.users.find_one(
            self.user_filter, projection=self.projection
        )
        if user_data is None:
            raise ValueError("User not found")  # TODO: use our own error
        raw_history = user_data.get("history", [])
        history = []
        guesses = set()
        for document in raw_history:
            historia = schemas.DistanceResponse(**document)
            if historia.guess not in guesses:
                guesses.add(historia.guess)
                history.append(historia)
        return await self._fix_history(
            history, update_db=len(history) != len(raw_history)
        )

    async def _fix_history(
        self, history: list[schemas.DistanceResponse], update_db: bool
    ) -> list[schemas.DistanceResponse]:
        for i, historia in enumerate(history, start=1):
            historia.guess_number = i
        if update_db:
            # fix duplicates
            await self.mongo.users.update_one(
                self.user_filter,
                {
                    "$set": {
                        f"history.{self.date}": [
                            historia.model_dump() for historia in history
                        ]
                    }
                },
            )
        return history


class UserStatisticsLogic:
    def __init__(self, mongo: motor.core.AgnosticDatabase[Any], user: dict[str, Any]):
        self.mongo = mongo
        self.user = user

    async def get_statistics(self) -> schemas.UserStatistics:
        # TODO: for now this is good enough, but we can do it with aggregation.
        # we should probably change the way we save the data - instead of having
        # saving history as an object with dates as its members, it should consist of
        # list with dates as its members.
        user = await self.mongo.users.find_one(
            {"email": self.user["email"]}, projection={"history": 1}
        )
        if user is None:
            raise ValueError("User not found")  # TODO: use our own error
        user_history = user.get("history", {})
        user_history = {
            date: [schemas.DistanceResponse(**guess) for guess in history]
            for date, history in user_history.items()
            if history
        }

        game_streak = self._get_game_streak(user_history.keys())

        highest_rank = None
        total_games_won = 0
        total_guesses = 0
        for historia in user_history.values():
            for guess in historia:
                if guess.similarity == 100:
                    total_games_won += 1
                    highest_rank = min(highest_rank or sys.maxsize, guess.solver_count)
                    total_guesses += guess.guess_number

        return schemas.UserStatistics(
            game_streak=game_streak,
            highest_rank=highest_rank,
            total_games_played=len(user_history),
            total_games_won=total_games_won,
            average_guesses=total_guesses / total_games_won if total_games_won else 0,
        )

    def _get_game_streak(self, game_dates: list[str]) -> int:
        game_dates = sorted(game_dates, reverse=True)
        date = datetime.datetime.utcnow().date()
        game_streak = 0
        for game_date in game_dates:
            if str(date) == game_date:
                game_streak += 1
                date -= datetime.timedelta(days=1)
            else:
                break
        return game_streak


class UserClueLogic:
    CLUE_CHAR_FORMAT = 'המילה הסודית מכילה את האות "{clue_char}"'
    CLUE_LEN_FORMAT = "המילה הסודית מכילה {clue_len} אותיות"
    NO_MORE_CLUES_STR = "אין יותר רמזים"
    CLUE_COOLDOWN_FOR_UNSUBSCRIBED = datetime.timedelta(days=7)

    def __init__(
        self,
        mongo: motor.core.AgnosticDatabase[Any],
        session: Session,
        user: dict[str, Any],
        secret: str,
        date: datetime.date,
    ):
        self.mongo = mongo
        self.session = session
        self.user = user
        self.secret = secret
        self.date = date

    @property
    def clues(self) -> list[Callable[[], Awaitable[str]]]:
        return [
            self._get_clue_char,
            self._get_secret_len,
        ]

    @property
    def clues_used(self) -> int:
        user_clues: dict[str, int] = self.user.get("clues", {})
        return user_clues.get(str(self.date), 0)

    async def get_clue(self) -> str | None:
        if self.clues_used < len(self.clues):
            await self._update_clue_usage()
            return await self.clues[self.clues_used]()
        else:
            return None

    async def get_all_clues_used(self) -> list[str]:
        clues = []
        for i in range(self.clues_used):
            clues.append(await self.clues[i]())
        return clues

    async def _used_max_clues_for_inactive(self) -> bool:
        clues = self.user.get("clues")
        if clues is None:
            return False
        max_date = datetime.datetime.fromisoformat(max(clues)).date()
        if max_date + self.CLUE_COOLDOWN_FOR_UNSUBSCRIBED > self.date:
            return True
        else:
            return False

    async def _update_clue_usage(self) -> None:
        await self.mongo.users.update_one(
            {"email": self.user["email"]}, {"$inc": {f"clues.{self.date}": 1}}
        )
        with hs_transaction(self.session) as session:
            user_query = select(tables.User).where(
                tables.User.email == self.user["email"]
            )
            user = session.exec(user_query).first()
            if user is None:
                logger.warning("User not found")
                return
            else:
                clue_count_query = select(tables.UserClueCount).where(
                    tables.UserClueCount.user_id == user.id,
                    tables.UserClueCount.game_date == self.date,
                )
                clue_count = session.exec(clue_count_query).first()
                if clue_count is None:
                    clue_count = tables.UserClueCount(
                        user_id=user.id,
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
