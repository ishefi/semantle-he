from datetime import timedelta, datetime
import random
from typing import Optional
from fastapi import Request, HTTPException, FastAPI
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from common.consts import FIRST_DATE
from logic import EasterEggLogic, CacheSecretLogic, VectorLogic

from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_date(delta: timedelta):
    return datetime.utcnow().date() - delta


def get_logics(app: FastAPI, delta: timedelta):
    date = get_date(delta)
    logic = VectorLogic(app.state.mongo, date)
    secret = logic.secret_logic.get_secret()
    cache_logic = CacheSecretLogic(
        app.state.mongo, app.state.redis, secret=secret, dt=date
    )
    return logic, cache_logic


class DistanceResponse(BaseModel):
    similarity: float
    distance: int
    egg: Optional[str] = None


@router.get("/health")
async def health():
    return {"message": "Healthy!"}


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    delta = request.app.state.days_delta
    logic, cache_logic = get_logics(app=request.app, delta=delta)
    cache = await cache_logic.cache
    closest1 = await logic.get_similarity(cache[-2])
    closest10 = await logic.get_similarity(cache[-12])
    closest1000 = await logic.get_similarity(cache[0])

    date = get_date(delta=delta)
    number = (date - FIRST_DATE).days + 1

    yestersecret = await VectorLogic(
        request.app.state.mongo, date - timedelta(days=1)
    ).secret_logic.get_secret()

    if random.random() >= 0.5:
        quote = request.app.state.main_quote
    else:
        quote = random.choice(request.app.state.quotes)

    return templates.TemplateResponse(
        'index.html',
        context=dict(request=request,
            number=number,
            closest1=closest1,
            closest10=closest10,
            closest1000=closest1000,
            yesterdays_secret=yestersecret,
            quote=quote)
    )


@router.get("/api/distance/")
async def get(word: str, request: Request) -> DistanceResponse:
    word = word.replace("'", "")
    if egg := EasterEggLogic.get_easter_egg(word):
        reply = DistanceResponse(similarity=99.99,
                                 distance=-1,
                                 egg=egg)

    else:
        logic, cache_logic = get_logics(app=request.app, delta=request.app.state.days_delta)
        sim = await logic.get_similarity(word)
        cache_score = await cache_logic.get_cache_score(word)
        reply = DistanceResponse(
            similarity=sim,
            distance=cache_score
        )
    return reply


@router.get("/yesterday-top-1000/", response_class=HTMLResponse)
async def yesterday_top(request: Request):
    delta = request.app.state.days_delta + timedelta(days=1)
    logic, cache_logic = get_logics(app=request.app, delta=delta)
    cache = await cache_logic.cache
    yesterday_sims = await logic.get_similarities(cache)
    return templates.TemplateResponse(
        'closest1000.html',
        context=dict(request=request,yesterday=sorted(yesterday_sims.items(), key=lambda ws: ws[1], reverse=1)))


@router.get("/secrets/", response_class=HTMLResponse)
async def secrets(request: Request, api_key: Optional[str] = None):
    logic, _ = get_logics(app=request.app, delta=request.app.state.days_delta)
    secrets = await logic.secret_logic.get_all_secrets()
    if api_key != request.app.state.api_key:
        raise HTTPException(status_code=403)

    return templates.TemplateResponse(
        'all_secrets.html',
        context=dict(request=request,secrets=sorted(secrets, key=lambda ws: ws[1], reverse=True)),
    )


@router.get("/faq/", response_class=HTMLResponse)
async def faq(request: Request):
    _, cache_logic = get_logics(app=request.app, delta=timedelta(days=1))
    cache = await cache_logic.cache
    return templates.TemplateResponse(
        'faq.html',
        context=dict(request=request,yesterday=cache[-11:])
    )


@router.get("/videos/", response_class=HTMLResponse)
async def videos(request: Request):
    return templates.TemplateResponse(
        'videos.html',
        context=(dict(videos=request.app.state.videos)),
    )
