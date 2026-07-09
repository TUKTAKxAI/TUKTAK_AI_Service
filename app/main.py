from fastapi import FastAPI

from app.api.v1.router import api_router, root_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="TukTak AI 견적 및 RAG 리스크 분석 서비스",
)

app.include_router(root_router)
app.include_router(api_router)
