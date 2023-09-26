#!/usr/bin/env python
import datetime

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
