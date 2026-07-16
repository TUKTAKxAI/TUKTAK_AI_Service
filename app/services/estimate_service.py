from app.graphs.estimate_graph import estimate_graph
from app.core.constants import ValidityLabel
from app.schemas.estimate import (
    EstimateError,
    EstimateRequest,
    EstimateResponse,
    EstimateResponseStatus,
    EstimateResult,
)


VALIDATION_FAILURE_LABELS = {
    ValidityLabel.TOO_SHORT.value,
    ValidityLabel.TOO_VAGUE.value,
    ValidityLabel.NOT_REPAIR_RELATED.value,
    ValidityLabel.SPAM_OR_GIBBERISH.value,
    ValidityLabel.UNSAFE_INPUT.value,
    ValidityLabel.PRICE_ONLY.value,
    ValidityLabel.IMAGE_REQUIRED.value,
}


class EstimateService:
    def create_estimate(self, payload: EstimateRequest) -> EstimateResponse:
        try:
            state = estimate_graph.invoke(
                {
                    "request_id": payload.request_id or "",
                    "description": payload.description,
                    "image_urls": payload.image_urls,
                    "image_paths": payload.image_paths,
                    "main_category": payload.main_category_hint,
                    "missing_info": [],
                    "warnings": [],
                    "similar_cases": [],
                }
            )
        except Exception as exc:
            return EstimateResponse(
                success=False,
                status=EstimateResponseStatus.SERVICE_ERROR,
                code="ESTIMATE_SERVICE_ERROR",
                message="AI estimate service failed while processing the request.",
                estimate=None,
                error=EstimateError(
                    code="ESTIMATE_SERVICE_ERROR",
                    validity_label="service_error",
                    message=str(exc),
                    missing_info=[],
                ),
            )

        if state.get("error_message"):
            status = self._classify_error_status(state)
            code = self._response_code(status, state.get("validity_label", "unknown"))
            return EstimateResponse(
                success=False,
                status=status,
                code=code,
                message=state["error_message"],
                estimate=None,
                error=EstimateError(
                    code=code,
                    validity_label=state.get("validity_label", "unknown"),
                    message=state["error_message"],
                    missing_info=state.get("missing_info", []),
                ),
            )

        return EstimateResponse(
            success=True,
            status=EstimateResponseStatus.COMPLETED,
            code="ESTIMATE_COMPLETED",
            message="Estimate completed successfully.",
            estimate=EstimateResult(
                main_category=state.get("main_category"),
                object_label=state.get("object_label"),
                problem_label=state.get("problem_label"),
                repair_task=state.get("repair_task"),
                expected_price_min=state.get("min_price"),
                expected_price_max=state.get("max_price"),
                expected_duration_minutes=state.get("duration_minutes"),
                confidence_score=state.get("confidence"),
                validity_label=state.get("validity_label", "valid_repair_request"),
                missing_info=state.get("missing_info", []),
                estimate_method=state.get("estimate_method"),
                llm_used=state.get("llm_used", False),
                estimate_items=state.get("estimate_items", []),
                warnings=state.get("warnings", []),
                similar_cases=state.get("similar_cases", []),
                base_price_rule=state.get("base_price_rule"),
            ),
            error=None,
        )

    def _classify_error_status(self, state: dict) -> EstimateResponseStatus:
        validity_label = state.get("validity_label")
        if validity_label in VALIDATION_FAILURE_LABELS:
            return EstimateResponseStatus.VALIDATION_FAILED
        if state.get("missing_info"):
            return EstimateResponseStatus.NEEDS_MORE_INFO
        return EstimateResponseStatus.SERVICE_ERROR

    def _response_code(self, status: EstimateResponseStatus, validity_label: str) -> str:
        if status == EstimateResponseStatus.VALIDATION_FAILED:
            return f"ESTIMATE_VALIDATION_{validity_label.upper()}"
        if status == EstimateResponseStatus.NEEDS_MORE_INFO:
            return "ESTIMATE_NEEDS_MORE_INFO"
        if status == EstimateResponseStatus.SERVICE_ERROR:
            return "ESTIMATE_SERVICE_ERROR"
        return "ESTIMATE_COMPLETED"
