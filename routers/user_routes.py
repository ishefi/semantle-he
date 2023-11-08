#!/usr/bin/env python
import datetime
import hashlib
import hmac
import json
from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi import status

from common import config
user_router = APIRouter(prefix="/api/user")

@user_router.get("/info")
async def get_user_info(request: Request):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        hasher = hashlib.sha3_256()
        # TODO: make this consistent
        hasher.update(user["email"].encode() + config.secret_key.encode())
        return {
            "id": hasher.hexdigest()[:8],
            "email": user["email"],
            "picture": user["picture"],
            "name": f"{user['given_name']} {user['family_name']}",
            "subscription_expiry": user.get("subscription_expiry"),
        }
