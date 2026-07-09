from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="TukTak AI 견적 및 RAG 리스크 분석 서비스",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.app_name,
    }