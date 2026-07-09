from typing import Any

from pydantic import BaseModel, Field


class EstimateRequest(BaseModel):
    request_id: str | None = None
    description: str = Field(..., min_length=1)
    image_urls: list[str] = Field(default_factory=list)
    image_paths: list[str] = Field(default_factory=list)
    main_category_hint: str | None = None
    region_code: str | None = None


class EstimateItem(BaseModel):
    name: str
    price_min: int
    price_max: int


class EstimateResult(BaseModel):
    main_category: str | None
    object_label: str | None
    problem_label: str | None
    repair_task: str | None
    expected_price_min: int | None
    expected_price_max: int | None
    expected_duration_minutes: int | None
    confidence_score: float | None
    validity_label: str
    missing_info: list[str] = Field(default_factory=list)
    estimate_method: str | None = None
    llm_used: bool = False
    estimate_items: list[EstimateItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    similar_cases: list[dict[str, Any]] = Field(default_factory=list)
    base_price_rule: dict[str, Any] | None = None


class EstimateError(BaseModel):
    validity_label: str
    message: str
    missing_info: list[str] = Field(default_factory=list)


class EstimateResponse(BaseModel):
    success: bool
    estimate: EstimateResult | None = None
    error: EstimateError | None = None

