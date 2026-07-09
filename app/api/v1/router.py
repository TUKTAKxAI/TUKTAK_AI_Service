from fastapi import APIRouter

from app.api.v1.endpoints import estimate, health, rag, risk_report

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(estimate.router)
api_router.include_router(risk_report.router)
api_router.include_router(rag.router)

root_router = APIRouter()
root_router.include_router(health.router)

