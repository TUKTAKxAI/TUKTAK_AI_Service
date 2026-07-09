from statistics import mean

from app.core.constants import (
    DURATION_VARIANCE_THRESHOLD,
    PRICE_VARIANCE_THRESHOLD,
    TOP_K_SIMILAR_CASES,
)
from app.graphs.state import EstimateState
from app.rag.retriever import RepairCaseRetriever


def text_similarity_search(state: EstimateState) -> EstimateState:
    state["similar_cases"] = RepairCaseRetriever().search_text_cases(state, top_k=TOP_K_SIMILAR_CASES)
    return state


def text_and_image_similarity_search(state: EstimateState) -> EstimateState:
    state["similar_cases"] = RepairCaseRetriever().search_text_and_image_cases(state, top_k=TOP_K_SIMILAR_CASES)
    return state


def evaluate_similar_cases(state: EstimateState) -> EstimateState:
    cases = state.get("similar_cases") or []
    if len(cases) < TOP_K_SIMILAR_CASES:
        state["similar_cases_enough"] = False
        return state

    prices = [case.get("price") for case in cases if case.get("price") is not None]
    durations = [case.get("duration_minutes") for case in cases if case.get("duration_minutes") is not None]
    if len(prices) < TOP_K_SIMILAR_CASES or len(durations) < TOP_K_SIMILAR_CASES:
        state["similar_cases_enough"] = False
        return state

    price_spread = max(prices) - min(prices)
    duration_spread = max(durations) - min(durations)
    price_ok = PRICE_VARIANCE_THRESHOLD is not None and price_spread <= PRICE_VARIANCE_THRESHOLD
    duration_ok = DURATION_VARIANCE_THRESHOLD is not None and duration_spread <= DURATION_VARIANCE_THRESHOLD
    state["similar_cases_enough"] = price_ok and duration_ok
    state["similar_case_stats"] = {
        "price_min": min(prices),
        "price_max": max(prices),
        "duration_mean": int(mean(durations)),
        "price_spread": price_spread,
        "duration_spread": duration_spread,
    }
    return state

