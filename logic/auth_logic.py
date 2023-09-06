#!/usr/bin/env python
from __future__ import annotations

import datetime
import uuid

from google.oauth2 import id_token
from google.auth.transport import requests
from typing import TYPE_CHECKING

from logic.user_logic import UserLogic

if TYPE_CHECKING:
    import pymongo.database


class AuthLogic:
    def __init__(self, mongo: pymongo.database.Database, auth_client_id: str) -> None:
        self.user_logic = UserLogic(mongo)
        self.sessions = mongo.sessions
        self.auth_client_id = auth_client_id

    async def session_id_from_credential(self, credential) -> str:
        user_info = self._verify_credential(credential)
        email = user_info["email"]
        user = await self.user_logic.get_user(email)
        if user is None:
            user = await self.user_logic.create_user(user_info)
        session_id = uuid.uuid4().hex
        await self.sessions.insert_one({
            "session_id": session_id,
            "user_email": user["email"],
            "session_start": datetime.datetime.utcnow(),
        })
        return session_id

    def _verify_credential(self, credential):
        try:
            return id_token.verify_oauth2_token(
                credential, requests.Request(), self.auth_client_id
            )
        except ValueError:
            raise ValueError("Invalid credential", 401324)

    async def logout(self, session_id):
        await self.sessions.delete_one({"session_id": session_id})
