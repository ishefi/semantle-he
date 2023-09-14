#!/usr/bin/env python
from datetime import datetime
from datetime import timedelta

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from logic.game_logic import CacheSecretLogic
from logic.game_logic import VectorLogic

templates = Jinja2Templates(directory="templates")


def get_date(delta: timedelta):
    return datetime.utcnow().date() - delta


def get_logics(app: FastAPI, delta: timedelta = timedelta()):
    delta += app.state.days_delta
    date = get_date(delta)
    logic = VectorLogic(app.state.mongo.word2vec2, dt=date, model=app.state.model)
    secret = logic.secret_logic.get_secret()
    cache_logic = CacheSecretLogic(
        app.state.mongo.word2vec2, app.state.redis, secret=secret, dt=date, model=app.state.model
    )
    return logic, cache_logic


def render(name: str, request, **kwargs):
    kwargs['js_version'] = request.app.state.js_version
    kwargs['css_version'] = request.app.state.css_version
    kwargs['request'] = request
    kwargs['enumerate'] = enumerate
    return templates.TemplateResponse(
        name,
        context=kwargs
    )
