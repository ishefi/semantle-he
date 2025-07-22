#!/usr/bin/env python
from __future__ import annotations

import datetime
import hashlib

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from fastapi.requests import Request

from common import config
from logic.user_logic import UserLogic
from logic.user_logic import UserStatisticsLogic

user_router = APIRouter(prefix="/api/user")


@user_router.get("/info")
async def get_user_info(
    request: Request,
) -> dict[str, str | datetime.datetime | int | None]:
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        user_logic = UserLogic(request.app.state.session)
        stats_logic = UserStatisticsLogic(request.app.state.session, user)
        hasher = hashlib.sha3_256()
        # TODO: make this consistent
        hasher.update(user.email.encode() + config.secret_key.encode())
        return {
            "id": hasher.hexdigest()[:8],
            "email": user.email,
            "picture": user.picture,
            "name": f"{user.given_name} {user.family_name}",
            "subscription_expiry": user_logic.get_subscription_expiry(user),
            # TODO: consider adding more statistics in the future
            "game_streak": (await stats_logic.get_statistics()).game_streak,
        }
