#!/usr/bin/env python
import datetime


class UserLogic:
    def __init__(self, mongo):
        self.mongo = mongo

    async def create_user(self, user_info):
        user = {
                "email": user_info["email"],
                "user_type": "User",
                "active": True,
                "picture": user_info["picture"],
                "given_name": user_info["given_name"],
                "family_name": user_info.get("family_name", ""),
                "first_login": datetime.datetime.utcnow(),
            }
        await self.mongo.users.insert_one(user)
        return user

    async def get_user(self, email):
        return await self.mongo.users.find_one({"email": email})

