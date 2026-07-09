from app.schemas.risk_report import RiskReportRequest, RiskReportResponse, RiskReportResult


class RiskReportService:
    def create_risk_report(self, payload: RiskReportRequest) -> RiskReportResponse:
        return RiskReportResponse(
            success=True,
            risk_report=RiskReportResult(
                risk_level="LOW",
                risk_score=28,
                summary="MVP mock 리스크 리포트입니다. 실제 RAG 검색과 LLM 생성은 다음 단계에서 연결합니다.",
                price_risk="기준 단가표 범위와 실제 시공자 견적의 차이를 확인해야 합니다.",
                additional_cost_risk=[
                    "출장비 별도 청구 가능성",
                    "자재비 포함 여부 미확정",
                    "현장 확인 후 작업 범위 확대 가능성",
                ],
                contract_checklist=[
                    "출장비 포함 여부 확인",
                    "자재비 포함 여부 확인",
                    "작업 범위 확인",
                    "AS 가능 기간 확인",
                ],
                sources=[],
            ),
        )

