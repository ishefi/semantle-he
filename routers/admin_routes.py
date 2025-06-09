import datetime
import random

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session
from sqlmodel import select

from common import tables
from common.consts import FIRST_DATE
from common.session import hs_transaction
from logic.game_logic import CacheSecretLogic
from logic.game_logic import SecretLogic
from model import GensimModel
from routers.base import render
from routers.base import super_admin

TOP_SAMPLE = 10000

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(super_admin)])


@admin_router.get("/set-secret", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request) -> HTMLResponse:
    model = request.app.state.model
    secret_logic = SecretLogic(request.app.state.session)
    all_secrets = [
        secret[0] for secret in await secret_logic.get_all_secrets(with_future=True)
    ]
    potential_secrets: list[str] = []
    while len(potential_secrets) < 45:
        secret = await get_random_word(model)  # todo: in batches
        if secret not in all_secrets:
            potential_secrets.append(secret)

    return render(
        name="set_secret.html", request=request, potential_secrets=potential_secrets
    )


@admin_router.get("/model", include_in_schema=False)
async def get_word_data(
    request: Request, word: str
) -> dict[str, list[str] | datetime.date | int]:
    session = request.app.state.session
    model = request.app.state.model
    logic = CacheSecretLogic(
        session=session,
        secret=word,
        dt=await get_date(session),
        model=model,
    )
    try:
        await logic.simulate_set_secret(force=False)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    cache = await logic.get_cache()
    return {
        "date": logic.date_,
        "game_number": (logic.date_ - FIRST_DATE).days + 1,
        "data": cache[::-1],
    }


class SetSecretRequest(BaseModel):
    secret: str
    clues: list[str]


@admin_router.post("/set-secret", include_in_schema=False)
async def set_new_secret(request: Request, set_secret: SetSecretRequest) -> str:
    session = request.app.state.session
    model = request.app.state.model
    logic = CacheSecretLogic(
        session=session,
        secret=set_secret.secret,
        dt=await get_date(session),
        model=model,
    )
    await logic.simulate_set_secret(force=False)
    await logic.do_populate(set_secret.clues)
    return f"Set '{set_secret.secret}' with clues '{set_secret.clues}' on {logic.date_}"


# TODO: everything below here should be in a separate file, and set_secret script should be updated to use it
async def get_random_word(model: GensimModel) -> str:
    rand_index = random.randint(0, TOP_SAMPLE)
    word: str = model.model.index_to_key[rand_index]
    return word


async def get_date(session: Session) -> datetime.date:
    query = select(tables.SecretWord.game_date)  # type: ignore
    query = query.order_by(tables.SecretWord.game_date.desc())  # type: ignore
    with hs_transaction(session) as s:
        latest: datetime.date = s.exec(query).first()

    dt = latest + datetime.timedelta(days=1)
    return dt
