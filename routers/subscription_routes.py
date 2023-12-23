#!/usr/bin/env python
import datetime
import hmac
import json
from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi import status
import requests

from common import config
from common import schemas
from logic.user_logic import UserLogic

subscription_router = APIRouter(prefix="/api/subscribe")


@subscription_router.post("/ko-fi")
async def subscribe(
        request: Request,
        data: Annotated[str, Form()]
) -> dict[str, str]:
    subscription = schemas.Subscription(**json.loads(data))
    is_valid_token = hmac.compare_digest(
        subscription.verification_token, config.kofi_verification_token
    )
    message_dt = subscription.timestamp.replace(tzinfo=None)
    is_new_message = message_dt > datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    if not is_valid_token or not is_new_message:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    logic = UserLogic(mongo=request.app.state.mongo)
    success = await logic.subscribe(subscription)
    success_message = "Success :smile:" if success else "Failed :rage:"
    requests.post(config.alerts_webhook, json={
        "text": f"New Ko-fi subscription: {subscription.email} ({subscription.amount}$) - {success_message}",
    })
    return {"status": "ok"}
