from typing import Any

from pydantic import BaseModel, Field


class RiskReportRequest(BaseModel):
    estimate_id: int | None = None
    main_category: str | None = None
    object_label: str | None = None
    problem_label: str | None = None
    repair_task: str | None = None
    expected_price_min: int | None = None
    expected_price_max: int | None = None
    expected_duration_minutes: int | None = None
    description: str = ""
    ai_summary: str | None = None


class RiskReportResult(BaseModel):
    report_status: str = "COMPLETED"
    failure_reason: str | None = None
    risk_level: str | None = None
    risk_score: int | None = None
    summary: str
    risk_items: list[dict[str, Any]] = Field(default_factory=list)
    checklist: list[dict[str, Any]] = Field(default_factory=list)
    additional_cost_risks: list[dict[str, Any]] = Field(default_factory=list)
    safety_risks: list[dict[str, Any]] = Field(default_factory=list)
    contract_risks: list[dict[str, Any]] = Field(default_factory=list)
    field_variable_risks: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, str | int | float | None]] = Field(default_factory=list)
    model_name: str | None = None
    model_version: str | None = None
    evidence_status: dict[str, str] = Field(default_factory=dict)


class RiskReportResponse(BaseModel):
    success: bool
    status: str = "completed"
    code: str = "RISK_REPORT_COMPLETED"
    message: str = "Risk report completed successfully."
    risk_report: RiskReportResult
