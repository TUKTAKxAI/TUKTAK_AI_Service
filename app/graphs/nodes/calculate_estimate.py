from statistics import mean

from app.core.constants import ValidityLabel
from app.graphs.state import EstimateState


def calculate_estimate_from_similar_cases(state: EstimateState) -> EstimateState:
    cases = state.get("similar_cases") or []
    prices = [int(case["price"]) for case in cases if case.get("price") is not None]
    durations = [int(case["duration_minutes"]) for case in cases if case.get("duration_minutes") is not None]
    state["min_price"] = min(prices)
    state["max_price"] = max(prices)
    state["duration_minutes"] = int(mean(durations))
    state["confidence"] = 0.82
    state["estimate_method"] = "similar_case_based"
    state["llm_used"] = False
    state["estimate_items"] = [{"name": "유사 사례 기반 견적", "price_min": min(prices), "price_max": max(prices)}]
    return state


def calculate_estimate_with_base_price_and_llm(state: EstimateState) -> EstimateState:
    rule = state.get("base_price_rule")
    warnings = list(state.get("warnings") or [])
    if rule:
        state["min_price"] = int(rule["base_price_min"])
        state["max_price"] = int(rule["base_price_max"])
        state["duration_minutes"] = int(rule["base_duration_minutes"])
        state["confidence"] = 0.68
        state["estimate_method"] = "base_price_reference"
        state["llm_used"] = False
        state["estimate_items"] = [
            {"name": "출장비", "price_min": int(rule["visit_fee_min"]), "price_max": int(rule["visit_fee_max"])},
            {"name": "작업비", "price_min": int(rule["labor_cost_min"]), "price_max": int(rule["labor_cost_max"])},
            {"name": "자재비", "price_min": int(rule["material_cost_min"]), "price_max": int(rule["material_cost_max"])},
        ]
    else:
        state["min_price"] = None
        state["max_price"] = None
        state["duration_minutes"] = None
        state["confidence"] = 0.3
        state["estimate_method"] = "needs_llm_or_price_reference"
        state["llm_used"] = False
        state["missing_info"] = list(set((state.get("missing_info") or []) + ["base_price_rule"]))
        warnings.append("기준 단가표와 유사사례가 부족하여 실제 모델 연동 후 보정이 필요합니다.")
    state["warnings"] = warnings
    return state


def validate_estimate_result(state: EstimateState) -> EstimateState:
    if state.get("validity_label") != ValidityLabel.VALID_REPAIR_REQUEST.value:
        return state
    required = ["main_category", "object_label", "problem_label", "repair_task"]
    missing = [field for field in required if not state.get(field)]
    if missing:
        state["missing_info"] = list(set((state.get("missing_info") or []) + missing))
        state["error_message"] = "견적 산정에 필요한 정보가 부족합니다."
    return state

