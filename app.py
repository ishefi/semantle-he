from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from common import config
from common.session import get_model
from common.session import get_mongo
from common.session import get_redis
from common.session import get_session
from logic.user_logic import UserLogic
from routers import routers

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
app.state.mongo = get_mongo()
app.state.redis = get_redis()
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
    date = datetime.strptime(os.environ.get("GAME_DATE", ""), "%Y-%m-%d").date()
    delta = (datetime.utcnow().date() - date).days
except ValueError:
    delta = 0
app.state.days_delta = timedelta(days=delta)
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
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    if session_id := request.cookies.get("session_id"):
        mongo = request.app.state.mongo
        session = await mongo.sessions.find_one({"session_id": session_id})
        if session is None:
            request.state.user = None
        else:
            user_logic = UserLogic(request.app.state.session)
            user = await user_logic.get_user(session["user_email"])
            if user is not None:
                request.state.user = user
                if expiry := user_logic.get_subscription_expiry(request.state.user):
                    is_active = expiry > datetime.utcnow()
                    request.state.has_active_subscription = is_active
    else:
        request.state.user = None
    return await call_next(request)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"message": "Healthy!"}


if __name__ == "__main__":
    uvicorn.run("app:app", port=5001, reload=getattr(config, "reload", False))
