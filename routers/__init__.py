#!/usr/bin/env python
from routers.auth_routes import auth_router
from routers.game_routes import game_router
from routers.pages_routes import pages_router
from routers.legal_routes import legal_router
from routers.subscription_routes import subscription_router
from routers.user_routes import user_router

routers = [
    auth_router,
    game_router,
    pages_router,
    legal_router,
    subscription_router,
    user_router,
]
