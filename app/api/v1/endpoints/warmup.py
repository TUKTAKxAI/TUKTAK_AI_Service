from fastapi import APIRouter

from app.services.warmup_service import get_warmup_status, start_background_warmup, warmup_models

router = APIRouter(prefix="/warmup", tags=["Warmup"])


@router.get("")
def warmup_status() -> dict:
    return get_warmup_status()


@router.post("")
def trigger_warmup(wait: bool = False) -> dict:
    if wait:
        return warmup_models()
    return start_background_warmup()
