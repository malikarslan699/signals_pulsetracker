from fastapi import APIRouter

from app.api.v1 import auth, signals, scanner, pairs, alerts, subscriptions, websocket
from app.api.v1.admin import users as admin_users, analytics as admin_analytics, config as admin_config, packages as admin_packages, qa as admin_qa

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(signals.router)
api_router.include_router(scanner.router)
api_router.include_router(pairs.router)
api_router.include_router(alerts.router)
api_router.include_router(subscriptions.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_analytics.router)
api_router.include_router(admin_config.router)
api_router.include_router(admin_packages.router)
api_router.include_router(admin_qa.router)

ws_router = APIRouter()
ws_router.include_router(websocket.router)
