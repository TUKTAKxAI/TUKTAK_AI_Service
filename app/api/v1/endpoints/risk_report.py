from fastapi import APIRouter

from app.schemas.risk_report import RiskReportRequest, RiskReportResponse
from app.services.risk_service import RiskReportService

router = APIRouter(prefix="/ai", tags=["Risk Report"])


@router.post("/risk-reports", response_model=RiskReportResponse)
async def create_risk_report(payload: RiskReportRequest) -> RiskReportResponse:
    return RiskReportService().create_risk_report(payload)

