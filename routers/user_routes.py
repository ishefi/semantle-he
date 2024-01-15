#!/usr/bin/env python
from __future__ import annotations

import datetime
import hashlib

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from fastapi.requests import Request

from common import config

user_router = APIRouter(prefix="/api/user")


@user_router.get("/info")
async def get_user_info(request: Request) -> dict[str, str | datetime.datetime | None]:
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        hasher = hashlib.sha3_256()
        # TODO: make this consistent
        hasher.update(user.email.encode() + config.secret_key.encode())
        return {
            "id": hasher.hexdigest()[:8],
            "email": user.email,
            "picture": user.picture,
            "name": f"{user.given_name} {user.family_name}",
            "subscription_expiry": user.subscription_expiry,
        }
