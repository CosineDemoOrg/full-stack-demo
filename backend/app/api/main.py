from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.api.routes.orgs import router as orgs_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(orgs_router)
api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
