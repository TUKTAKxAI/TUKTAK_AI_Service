from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router, root_router
from app.core.config import settings
from app.services.warmup_service import start_background_warmup


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.warmup_on_startup:
        start_background_warmup()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="TukTak AI estimate and RAG risk analysis service.",
    lifespan=lifespan,
)

app.include_router(root_router)
app.include_router(api_router)
