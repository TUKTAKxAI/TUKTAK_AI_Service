from app.graphs.state import EstimateState


def route_image_similarity_needed(state: EstimateState) -> str:
    return "text_and_image_similarity_search" if state.get("use_image_similarity") else "text_similarity_search"


def route_text_validation_result(state: EstimateState) -> str:
    if state.get("error_message"):
        return "end"
    return "analyze_text"


def route_text_analysis_result(state: EstimateState) -> str:
    if state.get("error_message"):
        return "end"
    return "lookup_base_price_rule"


def route_similar_cases_enough(state: EstimateState) -> str:
    if state.get("similar_cases_enough"):
        return "calculate_estimate_from_similar_cases"
    return "calculate_estimate_with_base_price_and_llm"
