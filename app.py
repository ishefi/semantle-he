import os
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

import uvicorn
from starlette.staticfiles import StaticFiles
from common import config
from common.session import get_mongo, get_redis, get_model

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from handlers import router

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
app.state.js_version = uuid.uuid4().hex[:6]
app.state.model = get_model(mongo=app.state.mongo, has_model=hasattr(config, "model_zip_id"))

try:
    date = datetime.strptime(os.environ.get("GAME_DATE", ""), '%Y-%m-%d').date()
    delta = (datetime.utcnow().date() - date).days
except ValueError:
    delta = 0
app.state.days_delta = timedelta(days=delta)
app.mount("/static", StaticFiles(directory="static"), name="static")
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
