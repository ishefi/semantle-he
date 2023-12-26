#!/usr/bin/env python
from __future__ import annotations

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response

from common import config
from routers.base import render

legal_router = APIRouter(prefix="/legal")


@legal_router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_policy(request: Request) -> Response:
    return render(
        "privacy.html", request=request, privacy_sections=config.privacy_policy
    )
