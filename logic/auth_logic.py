#!/usr/bin/env python
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import jwt
from google.auth.transport import requests
from google.oauth2 import id_token

from common import config
from logic.user_logic import UserLogic

if TYPE_CHECKING:
    from typing import Any

    from sqlmodel import Session

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days


class AuthLogic:
    def __init__(self, session: Session, auth_client_id: str) -> None:
        self.user_logic = UserLogic(session)
        self.auth_client_id = auth_client_id

    async def jwt_from_credential(self, credential: str) -> str:
        user_info = self._verify_credential(credential)
        email = user_info["email"]
        user = await self.user_logic.get_user(email)
        if user is None:
            user = await self.user_logic.create_user(user_info)
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        return jwt.encode(
            {"sub": user.email, "exp": expire},
            key=config.jwt_key,
            algorithm=config.jwt_algorithm,
        )

    def _verify_credential(self, credential: str) -> dict[str, Any]:
        try:
            id_info: dict[str, Any] = id_token.verify_oauth2_token(  #  type: ignore[no-untyped-call]
                credential,
                requests.Request(),  # type: ignore[no-untyped-call]
                self.auth_client_id,
            )
            return id_info
        except ValueError:
            raise ValueError("Invalid credential", 401324)
