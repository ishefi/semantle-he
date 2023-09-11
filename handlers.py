import json
import urllib.parse
from datetime import datetime
from datetime import timedelta
import random
from typing import Optional, Union
from typing import Annotated

from fastapi import APIRouter, Cookie, Header
from fastapi import Form
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import status
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from common import schemas
from common.consts import FIRST_DATE
from logic.auth_logic import AuthLogic
from logic.game_logic import CacheSecretLogic
from logic.game_logic import EasterEggLogic
from logic.game_logic import VectorLogic
from logic.user_logic import UserHistoryLogic

router = APIRouter()
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


@router.get("/health")
async def health():
    return {"message": "Healthy!"}


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    logic, cache_logic = get_logics(app=request.app)
    cache = await cache_logic.cache
    closest1 = await logic.get_similarity(cache[-2])
    closest10 = await logic.get_similarity(cache[-12])
    closest1000 = await logic.get_similarity(cache[0])

    date = get_date(delta=request.app.state.days_delta)
    number = (date - FIRST_DATE).days + 1

    yestersecret = await VectorLogic(
        mongo=request.app.state.mongo.word2vec2,model=request.app.state.model, dt=date - timedelta(days=1)
    ).secret_logic.get_secret()

    if request.state.user:
        history_logic = UserHistoryLogic(
            request.app.state.mongo,
            request.state.user,
            get_date(request.app.state.days_delta)
        )
        history = json.dumps([
            historia.dict() for historia in await history_logic.get_history()
        ])
    else:
        history = []

    quotes = request.app.state.quotes
    quote = random.choices(quotes, weights=[0.5] + [0.5 / (len(quotes) - 1)] * (len(quotes) - 1))[0]

    return render(
        name='index.html',
        request=request,
        number=number,
        closest1=closest1,
        closest10=closest10,
        closest1000=closest1000,
        yesterdays_secret=yestersecret,
        quote=quote,
        guesses=history,
        notification=request.app.state.notification,
    )


@router.get("/api/distance")
async def distance(
        request: Request,
        word: str = Query(default=..., min_length=2, max_length=24, regex=r"^[א-ת ']+$"),
) -> Union[schemas.DistanceResponse, list[schemas.DistanceResponse]]:
    word = word.replace("'", "")
    if egg := EasterEggLogic.get_easter_egg(word):
        response = schemas.DistanceResponse(
            guess=word, similarity=99.99, distance=-1, egg=egg
        )
    else:
        logic, cache_logic = get_logics(app=request.app)
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
    if request.headers.get("x-sh-version", "2022-02-20") >= "2023-09-10":
        if request.state.user:
            history_logic = UserHistoryLogic(
                request.app.state.mongo,
                request.state.user,
                get_date(request.app.state.days_delta)
            )
            return await history_logic.update_and_get_history(response)
        else:
            return [response]
    return response



@router.get("/yesterday-top-1000", response_class=HTMLResponse, include_in_schema=False)
async def yesterday_top(request: Request):
    # logic, cache_logic = get_logics(app=request.app, delta=timedelta(days=1))
    # cache = await cache_logic.cache
    # yesterday_sims = await logic.get_similarities(cache)
    return render(
        name='closest1000.html',
        request=request,
        # yesterday=sorted(yesterday_sims.items(), key=lambda ws: ws[1], reverse=True)
        yesterday=(["נראה שהמילים הקרובות מעצבנות יותר מדי אנשים, אז העמוד הוסר", 0],),
    )


@router.get("/secrets", response_class=HTMLResponse)
async def secrets(request: Request, api_key: Optional[str] = None, with_future: bool = False):
    if api_key != request.app.state.api_key and with_future:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    logic, _ = get_logics(app=request.app)
    all_secrets = await logic.secret_logic.get_all_secrets(with_future=with_future)

    return render(
        name='all_secrets.html',
        request=request,
        secrets=sorted(all_secrets, key=lambda ws: ws[1], reverse=True),
    )


@router.get("/faq", response_class=HTMLResponse, include_in_schema=False)
async def faq(request: Request):
    _, cache_logic = get_logics(app=request.app, delta=timedelta(days=1))
    cache = await cache_logic.cache
    return render(
        name='faq.html',
        request=request,
        # yesterday=cache[-11:]
        yesterday=[],
    )


@router.get("/videos", response_class=HTMLResponse, include_in_schema=False)
async def videos(request: Request):
    return render(
        name='videos.html',
        request=request,
        videos=request.app.state.videos
    )


@router.get("/api/menu", response_class=HTMLResponse, include_in_schema=False)
async def menu(request: Request):
    return render(
        name="menu.html",
        request=request,
        google_auth_client_id=request.app.state.google_app["client_id"],
        user=request.state.user
    )


@router.post("/login")
async def login(
        request: Request,
        credential: Annotated[str, Form()],
        state: Annotated[str, Form()] = "",
):
    try:
        parsed_state = urllib.parse.parse_qs(state)
        auth_logic = AuthLogic(request.app.state.mongo, request.app.state.google_app["client_id"])
        session_id = await auth_logic.session_id_from_credential(credential)
        if state is None or "next" not in parsed_state:
            next_uri = "/"
        else:
            next_uri = parsed_state["next"][0]
        response = RedirectResponse(next_uri, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="session_id",
            value=session_id,
            secure=True,
            httponly=True,
        )
        return response
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


@router.get("/logout")
async def logout(
        request: Request,
        session_id: Union[str, None] = Cookie(None),
):
    auth_logic = AuthLogic(request.app.state.mongo, request.app.state.google_app["client_id"])
    await auth_logic.logout(session_id)
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="session_id")
    return response
