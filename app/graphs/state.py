from typing import Any, TypedDict


class EstimateState(TypedDict, total=False):
    request_id: str
    description: str
    image_urls: list[str]
    image_paths: list[str]
    image_quality_valid: bool
    image_validation_result: dict[str, Any]
    text_validation_result: dict[str, Any]
    validity_label: str
    main_category: str | None
    object_label: str | None
    problem_label: str | None
    repair_task: str | None
    missing_info: list[str]
    base_price_rule: dict[str, Any] | None
    base_price_found: bool
    similar_cases: list[dict[str, Any]]
    similar_cases_enough: bool
    use_image_similarity: bool
    image_similarity_category: str | None
    min_price: int | None
    max_price: int | None
    duration_minutes: int | None
    confidence: float | None
    estimate_method: str | None
    llm_used: bool
    llm_summary: str | None
    estimate_items: list[dict[str, Any]]
    risk_summary: str | None
    warnings: list[str]
    error_message: str | None
