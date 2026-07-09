from app.graphs.estimate_graph import estimate_graph
from app.schemas.estimate import EstimateError, EstimateRequest, EstimateResponse, EstimateResult


class EstimateService:
    def create_estimate(self, payload: EstimateRequest) -> EstimateResponse:
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

        if state.get("error_message"):
            return EstimateResponse(
                success=False,
                estimate=None,
                error=EstimateError(
                    validity_label=state.get("validity_label", "unknown"),
                    message=state["error_message"],
                    missing_info=state.get("missing_info", []),
                ),
            )

        return EstimateResponse(
            success=True,
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
        )

