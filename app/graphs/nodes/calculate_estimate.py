from collections import Counter
from statistics import mean

from app.core.constants import SIMILAR_CASE_PRICE_MARGIN_RATE, ValidityLabel
from app.graphs.state import EstimateState


CATEGORICAL_ESTIMATE_FIELDS = ("main_category", "object_label", "problem_label", "repair_task")


def calculate_estimate_from_similar_cases(state: EstimateState) -> EstimateState:
    cases = state.get("similar_cases") or []
    prices = [int(case["price"]) for case in cases if case.get("price") is not None]
    durations = [int(case["duration_minutes"]) for case in cases if case.get("duration_minutes") is not None]

    for field in CATEGORICAL_ESTIMATE_FIELDS:
        representative_value = _most_common_case_value(cases, field)
        if representative_value:
            state[field] = representative_value

    price_min = _apply_price_margin(min(prices), -SIMILAR_CASE_PRICE_MARGIN_RATE)
    price_max = _apply_price_margin(max(prices), SIMILAR_CASE_PRICE_MARGIN_RATE)
    duration_mean = int(mean(durations))

    state["min_price"] = price_min
    state["max_price"] = price_max
    state["duration_minutes"] = duration_mean
    state["confidence"] = 0.82
    state["estimate_method"] = "similar_case_based"
    state["llm_used"] = False
    state["estimate_items"] = [
        {
            "name": "similar_case_based_estimate",
            "price_min": price_min,
            "price_max": price_max,
        }
    ]
    state["similar_case_stats"] = {
        "case_count": len(cases),
        "raw_price_min": min(prices),
        "raw_price_max": max(prices),
        "price_margin_rate": SIMILAR_CASE_PRICE_MARGIN_RATE,
        "duration_min": min(durations),
        "duration_max": max(durations),
        "duration_mean": duration_mean,
        "representative_fields": {
            field: state.get(field)
            for field in CATEGORICAL_ESTIMATE_FIELDS
        },
    }
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
            {"name": "visit_fee", "price_min": int(rule["visit_fee_min"]), "price_max": int(rule["visit_fee_max"])},
            {"name": "labor_cost", "price_min": int(rule["labor_cost_min"]), "price_max": int(rule["labor_cost_max"])},
            {"name": "material_cost", "price_min": int(rule["material_cost_min"]), "price_max": int(rule["material_cost_max"])},
        ]
    else:
        state["min_price"] = None
        state["max_price"] = None
        state["duration_minutes"] = None
        state["confidence"] = 0.3
        state["estimate_method"] = "needs_llm_or_price_reference"
        state["llm_used"] = False
        state["missing_info"] = list(set((state.get("missing_info") or []) + ["base_price_rule"]))
        warnings.append("Base price rule and similar cases are not enough. LLM or fallback data is required.")
    state["warnings"] = warnings
    return state


def validate_estimate_result(state: EstimateState) -> EstimateState:
    if state.get("validity_label") != ValidityLabel.VALID_REPAIR_REQUEST.value:
        return state
    required = ["main_category", "object_label", "problem_label", "repair_task"]
    missing = [field for field in required if not state.get(field)]
    if missing:
        state["missing_info"] = list(set((state.get("missing_info") or []) + missing))
        state["error_message"] = "Required structured fields are missing for estimate calculation."
    return state


def _most_common_case_value(cases: list[dict], field: str) -> str | None:
    values = []
    for case in cases:
        value = case.get(field)
        if value is None and isinstance(case.get("metadata"), dict):
            value = case["metadata"].get(field)
        if value:
            values.append(str(value))
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def _apply_price_margin(price: int, margin_rate: float) -> int:
    adjusted = int(price * (1 + margin_rate))
    return max(0, round(adjusted / 1000) * 1000)
