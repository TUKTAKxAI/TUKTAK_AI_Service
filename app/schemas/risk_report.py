from pydantic import BaseModel, Field


class RiskReportRequest(BaseModel):
    estimate_id: int | None = None
    main_category: str | None = None
    object_label: str | None = None
    problem_label: str | None = None
    repair_task: str | None = None
    expected_price_min: int | None = None
    expected_price_max: int | None = None
    description: str = ""


class RiskReportResult(BaseModel):
    risk_level: str
    risk_score: int
    summary: str
    price_risk: str
    additional_cost_risk: list[str] = Field(default_factory=list)
    contract_checklist: list[str] = Field(default_factory=list)
    sources: list[dict[str, str | int | float | None]] = Field(default_factory=list)


class RiskReportResponse(BaseModel):
    success: bool
    risk_report: RiskReportResult

