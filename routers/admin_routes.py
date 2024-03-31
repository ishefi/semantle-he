import datetime
import random

from fastapi import APIRouter
from fastapi import Depends
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session

from common.session import hs_transaction
from logic.game_logic import SecretLogic, CacheSecretLogic
from model import GensimModel
from routers.base import render
from routers.base import super_admin
from sqlmodel import select
from common import tables

TOP_SAMPLE = 10000

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(super_admin)])


@admin_router.get("/set-secret", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request) -> HTMLResponse:
    model = request.app.state.model
    secret_logic = SecretLogic(request.app.state.session)
    all_secrets = await secret_logic.get_all_secrets(with_future=True)
    potential_secrets = []
    while len(potential_secrets) < 45:
        secret = await get_random_word(model)  # todo: in batches
        if secret not in all_secrets:
            potential_secrets.append(secret)

    return render(name="set_secret.html", request=request, potential_secrets=potential_secrets)


@admin_router.get("/model", include_in_schema=False)
async def get_word_data(request: Request, word: str) -> dict[str, list[str] | datetime.date]:
    session = request.app.state.session
    redis = request.app.state.redis
    model = request.app.state.model
    logic = CacheSecretLogic(session=session, redis=redis, secret=word, dt=await get_date(session), model=model)
    await logic.simulate_set_secret(force=False)
    cache = await logic.cache
    return {
        "date": logic.date_,
        "data": cache[::-1],
    }

class SetSecretRequest(BaseModel):
    secret: str
    clues: list[str]

@admin_router.post("/set-secret", include_in_schema=False)
async def set_new_secret(request: Request, set_secret: SetSecretRequest):
    session = request.app.state.session
    redis = request.app.state.redis
    model = request.app.state.model
    logic = CacheSecretLogic(session=session, redis=redis, secret=set_secret.secret, dt=await get_date(session), model=model)
    await logic.simulate_set_secret(force=False)
    await logic.do_populate(set_secret.clues)
    return f"Set '{set_secret.secret}' with clues '{set_secret.clues}' on {logic.date_}"



# TODO: everything below here should be in a separate file, and set_secret script should be updated to use it
async def get_random_word(model: GensimModel) -> str:
    rand_index = random.randint(0, TOP_SAMPLE)
    return model.model.index_to_key[rand_index]


async def get_date(session: Session) -> datetime.date:
    query = select(tables.SecretWord.game_date)  # type: ignore
    query = query.order_by(tables.SecretWord.game_date.desc())  # type: ignore
    with hs_transaction(session) as s:
        latest: datetime.date = s.exec(query).first()

    dt = latest + datetime.timedelta(days=1)
    return dt