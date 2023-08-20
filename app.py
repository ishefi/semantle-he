import hashlib
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

import uvicorn
from fastapi.staticfiles import StaticFiles
from common import config
from common.session import get_mongo, get_redis, get_model

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from handlers import router

STATIC_FOLDER = "static"
js_hasher = hashlib.sha3_256()
with open(STATIC_FOLDER + "/semantle.js", "rb") as f:
    js_hasher.update(f.read())
JS_VERSION = js_hasher.hexdigest()[:8]

css_hasher = hashlib.sha3_256()
with open(STATIC_FOLDER + "/styles.css", "rb") as f:
    css_hasher.update(f.read())
CSS_VERSION = css_hasher.hexdigest()[:8]

app = FastAPI()
app.state.mongo = get_mongo()
app.state.redis = get_redis()
app.state.limit = int(os.environ.get("LIMIT", getattr(config, 'limit', 10)))
app.state.period = int(os.environ.get("PERIOD", getattr(config, 'period', 20)))
app.state.videos = config.videos
app.state.current_timeframe = 0
app.state.usage = defaultdict(int)
app.state.api_key = config.api_key
app.state.quotes = config.quotes
app.state.notification = config.notification
app.state.js_version = JS_VERSION
app.state.css_version = CSS_VERSION
app.state.model = get_model(mongo=app.state.mongo, has_model=hasattr(config, "model_zip_id"))

try:
    date = datetime.strptime(os.environ.get("GAME_DATE", ""), '%Y-%m-%d').date()
    delta = (datetime.utcnow().date() - date).days
except ValueError:
    delta = 0
app.state.days_delta = timedelta(days=delta)
app.mount(f"/{STATIC_FOLDER}", StaticFiles(directory=STATIC_FOLDER), name=STATIC_FOLDER)
app.include_router(router)


def request_is_limited(key: str):
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
    return app.state.usage[key] > app.state.limit


def get_idenitifier(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host


@app.middleware("http")
async def is_limited(request: Request, call_next):
    identifier = get_idenitifier(request)
    if request_is_limited(key=identifier):
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    response = await call_next(request)
    return response


if __name__ == "__main__":
    uvicorn.run('app:app', port=5001, reload=getattr(config, 'reload', False))
