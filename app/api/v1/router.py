# API router entrypoint
from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.organizations import router as organization_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.agents import router as agent_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(organization_router)
api_router.include_router(auth_router)
api_router.include_router(agent_router)
