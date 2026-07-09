from fastapi import APIRouter

from app.schemas.estimate import EstimateRequest, EstimateResponse
from app.services.estimate_service import EstimateService

router = APIRouter(prefix="/ai", tags=["AI Estimate"])


@router.post("/estimates", response_model=EstimateResponse)
async def create_estimate(payload: EstimateRequest) -> EstimateResponse:
    return EstimateService().create_estimate(payload)

