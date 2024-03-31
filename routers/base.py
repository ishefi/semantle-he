#!/usr/bin/env python
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import status
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from logic.game_logic import CacheSecretLogic
from logic.game_logic import VectorLogic
from logic.user_logic import UserLogic

templates = Jinja2Templates(directory="templates")

if TYPE_CHECKING:
    from typing import Any

    from fastapi import Request


def get_date(delta: datetime.timedelta) -> datetime.date:
    return datetime.datetime.utcnow().date() - delta


# TODO: replace this with a dependency
async def get_logics(
    app: FastAPI, delta: datetime.timedelta = datetime.timedelta()
) -> tuple[VectorLogic, CacheSecretLogic]:
    delta += app.state.days_delta
    date = get_date(delta)
    logic = VectorLogic(app.state.session, dt=date, model=app.state.model)
    secret = await logic.secret_logic.get_secret()
    if secret is None:
        raise Exception("No secret found!")  # TODO: better exception
    cache_logic = CacheSecretLogic(
        app.state.session,
        app.state.redis,
        secret=secret,
        dt=date,
        model=app.state.model,
    )
    return logic, cache_logic


def super_admin(request: Request) -> None:
    user = request.state.user
    if not user or not UserLogic.has_permissions(user, UserLogic.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


def render(name: str, request: Request, **kwargs: Any) -> HTMLResponse:
    kwargs["js_version"] = request.app.state.js_version
    kwargs["css_version"] = request.app.state.css_version
    kwargs["request"] = request
    kwargs["enumerate"] = enumerate
    kwargs["google_auth_client_id"] = request.app.state.google_app["client_id"]
    return templates.TemplateResponse(name, context=kwargs)
