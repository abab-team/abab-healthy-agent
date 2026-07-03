from fastapi import APIRouter

from app.modules.family.api import router as family_router
from app.modules.identity.api import router as identity_router
from app.modules.permissions.api import router as permissions_router


api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(identity_router)
api_v1_router.include_router(family_router)
api_v1_router.include_router(permissions_router)
