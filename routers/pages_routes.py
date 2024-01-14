#!/usr/bin/env python
from __future__ import annotations

import json
import random
import urllib.parse
from datetime import timedelta

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import HTMLResponse

from common.consts import FIRST_DATE
from logic.game_logic import VectorLogic
from logic.user_logic import UserClueLogic
from logic.user_logic import UserHistoryLogic
from logic.user_logic import UserLogic
from logic.user_logic import UserStatisticsLogic
from routers.base import get_date
from routers.base import get_logics
from routers.base import render

pages_router = APIRouter()


@pages_router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request) -> Response:
    logic, cache_logic = await get_logics(app=request.app)
    cache = await cache_logic.cache
    closest1 = await logic.get_similarity(cache[-2])
    closest10 = await logic.get_similarity(cache[-12])
    closest1000 = await logic.get_similarity(cache[0])

    date = get_date(delta=request.app.state.days_delta)
    number = (date - FIRST_DATE).days + 1

    yestersecret = await VectorLogic(
        session=request.app.state.session,
        model=request.app.state.model,
        dt=date - timedelta(days=1),
    ).secret_logic.get_secret()

    if request.state.user:
        history_logic = UserHistoryLogic(
            request.app.state.mongo,
            request.app.state.session,
            request.state.user,
            get_date(request.app.state.days_delta),
        )
        history = json.dumps(
            [historia.dict() for historia in await history_logic.get_history()]
        )
    else:
        history = ""

    quotes = request.app.state.quotes
    quote = random.choices(
        quotes, weights=[0.5] + [0.5 / (len(quotes) - 1)] * (len(quotes) - 1)
    )[0]

    if request.state.user:
        secret = await logic.secret_logic.get_secret()
        if secret is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        clue_logic = UserClueLogic(
            mongo=request.app.state.mongo,
            session=request.app.state.session,
            user=request.state.user,
            secret=secret,
            date=date,
        )
        used_clues = await clue_logic.get_all_clues_used()
    else:
        used_clues = []

    return render(
        name="index.html",
        request=request,
        number=number,
        closest1=closest1,
        closest10=closest10,
        closest1000=closest1000,
        yesterdays_secret=yestersecret,
        quote=quote,
        guesses=history,
        notification=request.app.state.notification,
        clues=used_clues,
    )


@pages_router.get(
    "/yesterday-top-1000", response_class=HTMLResponse, include_in_schema=False
)
async def yesterday_top(request: Request) -> Response:
    return render(
        name="closest1000.html",
        request=request,
        yesterday=(["נראה שהמילים הקרובות מעצבנות יותר מדי אנשים, אז העמוד הוסר", 0],),
    )


@pages_router.get("/secrets", response_class=HTMLResponse)
async def secrets(request: Request, with_future: bool = False) -> Response:
    if with_future:
        user = request.state.user
        if not user or not UserLogic.has_permissions(user, UserLogic.SUPER_ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    logic, _ = await get_logics(app=request.app)
    all_secrets = await logic.secret_logic.get_all_secrets(with_future=with_future)

    return render(
        name="all_secrets.html",
        request=request,
        secrets=sorted(all_secrets, key=lambda ws: ws[1], reverse=True),
    )


@pages_router.get("/faq", response_class=HTMLResponse, include_in_schema=False)
async def faq(request: Request) -> Response:
    # _, cache_logic = await get_logics(app=request.app, delta=timedelta(days=1))
    # cache = await cache_logic.cache
    return render(
        name="faq.html",
        request=request,
        # yesterday=cache[-11:]
        yesterday=[],
    )


@pages_router.get("/videos", response_class=HTMLResponse, include_in_schema=False)
async def videos(request: Request) -> Response:
    return render(name="videos.html", request=request, videos=request.app.state.videos)


@pages_router.get("/api/menu", response_class=HTMLResponse, include_in_schema=False)
async def menu(request: Request) -> Response:
    return render(
        name="menu.html",
        request=request,
        google_auth_client_id=request.app.state.google_app["client_id"],
        next_page=urllib.parse.urlparse(request.headers.get("referer")).path,
    )


@pages_router.get("/statistics", response_class=HTMLResponse, include_in_schema=False)
async def get_statistics(request: Request) -> Response:
    if request.state.user is not None:
        logic = UserStatisticsLogic(request.app.state.mongo, request.state.user)
        statistics = await logic.get_statistics()
    else:
        statistics = None
    return render(
        name="statistics.html",
        request=request,
        statistics=statistics,
        google_auth_client_id=request.app.state.google_app["client_id"],
    )
