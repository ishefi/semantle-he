#!/usr/bin/env python
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse

from common import config
from routers.base import render


legal_router = APIRouter(prefix="/legal")


@legal_router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_policy(request: Request):
    return render(
        "privacy.html", request=request, privacy_sections=config.privacy_policy
    )