#!/usr/bin/env python
import urllib.parse
from typing import Annotated

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse

from logic.auth_logic import AuthLogic

auth_router = APIRouter()


@auth_router.post("/login")
async def login(
    request: Request,
    credential: Annotated[str, Form()],
    state: Annotated[str, Form()] = "",
) -> RedirectResponse:
    try:
        parsed_state = urllib.parse.parse_qs(state)
        auth_logic = AuthLogic(
            request.app.state.mongo,
            request.app.state.session,
            request.app.state.google_app["client_id"],
        )
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


@auth_router.get("/logout")
async def logout(
    request: Request,
    session_id: str | None = Cookie(None),
) -> RedirectResponse:
    auth_logic = AuthLogic(
        request.app.state.mongo,
        request.app.state.session,
        request.app.state.google_app["client_id"],
    )
    if session_id is not None:
        await auth_logic.logout(session_id)
    redirect = urllib.parse.urlparse(request.headers.get("referer"))
    if isinstance(redirect.path, bytes):
        path = redirect.path.decode()
    else:
        path = redirect.path
    response = RedirectResponse(path, status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="session_id")
    return response
