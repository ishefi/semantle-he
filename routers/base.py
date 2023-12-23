#!/usr/bin/env python
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from logic.game_logic import CacheSecretLogic
from logic.game_logic import VectorLogic

templates = Jinja2Templates(directory="templates")

if TYPE_CHECKING:
    from typing import Any
    from fastapi.responses import Response
    from fastapi import Request


def get_date(delta: datetime.timedelta) -> datetime.date:
    return datetime.datetime.utcnow().date() - delta


# TODO: replace this with a dependency
async def get_logics(app: FastAPI, delta: datetime.timedelta = datetime.timedelta()) -> tuple[VectorLogic, CacheSecretLogic]:
    delta += app.state.days_delta
    date = get_date(delta)
    logic = VectorLogic(app.state.mongo.word2vec2, dt=date, model=app.state.model)
    secret = await logic.secret_logic.get_secret()
    if secret is None:
        raise Exception("No secret found!")  # TODO: better exception
    cache_logic = CacheSecretLogic(
        app.state.mongo.word2vec2,
        app.state.redis,
        secret=secret,
        dt=date,
        model=app.state.model,
    )
    return logic, cache_logic


def render(name: str, request: Request, **kwargs: Any) -> Response:
    kwargs['js_version'] = request.app.state.js_version
    kwargs['css_version'] = request.app.state.css_version
    kwargs['request'] = request
    kwargs['enumerate'] = enumerate
    return templates.TemplateResponse(
        name,
        context=kwargs
    )
