#!/usr/bin/env python
import datetime
import sys
from typing import Optional

from common import config
from common import schemas


class UserLogic:
    USER = "User"
    SUPER_ADMIN = config.super_admin

    PERMISSIONS = (
        USER,
        SUPER_ADMIN,
    )

    def __init__(self, mongo):
        self.mongo = mongo

    async def create_user(self, user_info):
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
        return user

    async def get_user(self, email):
        return await self.mongo.users.find_one({"email": email}, {"history": 0})

    @staticmethod
    def has_permissions(user, permission):
        return UserLogic.PERMISSIONS.index(
            user["user_type"]
        ) >= UserLogic.PERMISSIONS.index(permission)


class UserHistoryLogic:
    def __init__(self, mongo, user, date):
        self.mongo = mongo
        self.user = user
        self.date = str(date)

    @property
    def projection(self):
        return {"history": f"$history.{self.date}"}

    @property
    def user_filter(self):
        return {"email": self.user["email"]}

    async def update_and_get_history(self, guess: schemas.DistanceResponse):
        history = await self.get_history()
        if guess.similarity is not None:
            history.append(guess)
            return await self._fix_history(history, update_db=True)
        else:
            return [guess] + history

    async def get_history(self):
        raw_history = (
            await self.mongo.users.find_one(
                self.user_filter, projection=self.projection
            )
        ).get("history", [])
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

    async def _fix_history(self, history, update_db: bool):
        for i, historia in enumerate(history, start=1):
            historia.guess_number = i
        if update_db:
            # fix duplicates
            await self.mongo.users.update_one(
                self.user_filter,
                {
                    "$set": {
                        f"history.{self.date}": [
                            historia.dict() for historia in history
                        ]
                    }
                },
            )
        return history


class UserStatisticsLogic:
    def __init__(self, mongo, user):
        self.mongo = mongo
        self.user = user

    async def get_statistics(self) -> schemas.UserStatistics:
        # TODO: for now this is good enough, but we can do it with aggregation.
        # we should probably change the way we save the data - instead of having
        # saving history as an object with dates as its members, it should consist of
        # list with dates as its members.
        user_history = (
            await self.mongo.users.find_one(
                {"email": self.user["email"]}, projection={"history": 1}
            )
        ).get("history", {})
        user_history = {
            date: [schemas.DistanceResponse(**guess) for guess in history]
            for date, history in user_history.items() if history
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

    def _get_game_streak(self, game_dates):
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