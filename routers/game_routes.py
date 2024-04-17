#!/usr/bin/env python
from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import status

from common import schemas
from common.error import HSError
from logic.game_logic import EasterEggLogic
from logic.user_logic import UserClueLogic
from logic.user_logic import UserHistoryLogic
from routers.base import get_date
from routers.base import get_logics

game_router = APIRouter()


@game_router.get("/api/distance")
async def distance(
    request: Request,
    word: str = Query(default=..., min_length=2, max_length=24, regex=r"^[א-ת ']+$"),
) -> list[schemas.DistanceResponse]:
    word = word.replace("'", "")
    if egg := EasterEggLogic.get_easter_egg(word):
        response = schemas.DistanceResponse(
            guess=word, similarity=99.99, distance=-1, egg=egg
        )
    else:
        logic, cache_logic = await get_logics(app=request.app)
        sim = await logic.get_similarity(word)
        cache_score = await cache_logic.get_cache_score(word)
        if cache_score == 1000:
            solver_count = await logic.get_and_update_solver_count()
        else:
            solver_count = None
        response = schemas.DistanceResponse(
            guess=word,
            similarity=sim,
            distance=cache_score,
            solver_count=solver_count,
        )
    if request.state.user:
        history_logic = UserHistoryLogic(
            request.app.state.session,
            request.state.user,
            get_date(request.app.state.days_delta),
        )
        return await history_logic.update_and_get_history(response)
    else:
        return [response]


@game_router.get("/api/clue")
async def get_clue(request: Request) -> dict[str, str]:
    if not request.state.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        logic, _ = await get_logics(app=request.app)
        try:
            secret = await logic.secret_logic.get_secret()
        except HSError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        user_logic = UserClueLogic(
            session=request.app.state.session,
            user=request.state.user,
            secret=secret,
            date=get_date(request.app.state.days_delta),
        )
        try:
            clue = await user_logic.get_clue()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED)
        if clue is None:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        else:
            return {"clue": clue}
