from __future__ import annotations

import datetime
import hashlib
import os
import time
from collections import defaultdict
from typing import TYPE_CHECKING

import jwt
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from common import config
from common.error import HSError
from common.session import get_model
from common.session import get_session
from logic.user_logic import UserLogic
from routers import routers
from routers.base import get_logics

if TYPE_CHECKING:
    from typing import Awaitable
    from typing import Callable

STATIC_FOLDER = "static"
js_hasher = hashlib.sha3_256()
with open(STATIC_FOLDER + "/semantle.js", "rb") as f:
    js_hasher.update(f.read())
JS_VERSION = js_hasher.hexdigest()[:6]

css_hasher = hashlib.sha3_256()
with open(STATIC_FOLDER + "/styles.css", "rb") as f:
    css_hasher.update(f.read())
CSS_VERSION = css_hasher.hexdigest()[:6]

app = FastAPI()
app.state.limit = int(os.environ.get("LIMIT", getattr(config, "limit", 10)))
app.state.period = int(os.environ.get("PERIOD", getattr(config, "period", 20)))
app.state.videos = config.videos
app.state.current_timeframe = 0
app.state.usage = defaultdict(int)
app.state.quotes = config.quotes
app.state.notification = config.notification
app.state.js_version = JS_VERSION
app.state.css_version = CSS_VERSION
app.state.model = get_model()
app.state.google_app = config.google_app
app.state.session = get_session()


try:
    date = datetime.datetime.strptime(
        os.environ.get("GAME_DATE", ""), "%Y-%m-%d"
    ).date()
    delta = (datetime.datetime.now(datetime.UTC).date() - date).days
except ValueError:
    delta = 0
app.state.days_delta = datetime.timedelta(days=delta)
app.mount(f"/{STATIC_FOLDER}", StaticFiles(directory=STATIC_FOLDER), name=STATIC_FOLDER)
for router in routers:
    app.include_router(router)


def request_is_limited(key: str) -> bool:
    now = int(time.time())
    current = now - now % app.state.period
    if app.state.current_timeframe != current:
        app.state.current_timeframe = current
        for ip, usage in app.state.usage.items():
            if usage > app.state.limit * 0.75:
                app.state.usage[ip] = usage // 2
            else:
                app.state.usage[ip] = 0
        app.state.usage = defaultdict(
            int, {ip: usage for ip, usage in app.state.usage.items() if usage > 0}
        )
    app.state.usage[key] += 1
    if app.state.usage[key] > app.state.limit:
        return True
    else:
        return False


def get_idenitifier(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    else:
        return "unknown"


@app.middleware("http")
async def is_limited(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    identifier = get_idenitifier(request)
    if request_is_limited(key=identifier):
        return JSONResponse(content="", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    response = await call_next(request)
    return response


@app.middleware("http")
async def get_user(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    access_token = request.cookies.get("access_token")
    if access_token is not None:
        try:
            payload = jwt.decode(
                access_token, config.jwt_key, algorithms=[config.jwt_algorithm]
            )
            user_logic = UserLogic(request.app.state.session)
            user = await user_logic.get_user(payload["sub"])
            if user is not None:
                request.state.user = user
                if expiry := user_logic.get_subscription_expiry(request.state.user):
                    is_active = expiry > datetime.datetime.now(datetime.UTC)
                    request.state.has_active_subscription = is_active
                    request.state.expires_at = str(expiry.date())
        except jwt.exceptions.ExpiredSignatureError:
            request.state.user = None
    else:
        request.state.user = None
    return await call_next(request)


@app.middleware("http")
async def catch_known_errors(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        return await call_next(request)
    except HSError as e:
        return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/health")
async def health() -> JSONResponse:
    try:
        await get_logics(app=app)
    except (ValueError, HSError) as ex:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(ex)
        )
    return JSONResponse(content="OK", status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    uvicorn.run("app:app", port=5001, reload=getattr(config, "reload", False))
