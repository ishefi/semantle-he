#!/usr/bin/env python
from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from google.auth.transport import requests
from google.oauth2 import id_token

from logic.user_logic import UserLogic

if TYPE_CHECKING:
    from typing import Any

    import motor.core


class AuthLogic:
    def __init__(
        self, mongo: motor.core.AgnosticDatabase[Any], auth_client_id: str
    ) -> None:
        self.user_logic = UserLogic(mongo)
        self.sessions = mongo.sessions
        self.auth_client_id = auth_client_id

    async def session_id_from_credential(self, credential: str) -> str:
        user_info = self._verify_credential(credential)
        email = user_info["email"]
        user = await self.user_logic.get_user(email)
        if user is None:
            user = await self.user_logic.create_user(user_info)
        session_id = uuid.uuid4().hex
        await self.sessions.insert_one(
            {
                "session_id": session_id,
                "user_email": user["email"],
                "session_start": datetime.datetime.utcnow(),
            }
        )
        return session_id

    def _verify_credential(self, credential: str) -> dict[str, Any]:
        try:
            id_info: dict[str, Any] = id_token.verify_oauth2_token(
                credential, requests.Request(), self.auth_client_id
            )
            return id_info
        except ValueError:
            raise ValueError("Invalid credential", 401324)

    async def logout(self, session_id: str) -> None:
        await self.sessions.delete_one({"session_id": session_id})
