from app.core.constants import ValidityLabel
from app.graphs.state import EstimateState
from app.services.text_service import TextAnalysisService


def analyze_text(state: EstimateState) -> EstimateState:
    if state.get("validity_label") != ValidityLabel.VALID_REPAIR_REQUEST.value:
        return state
    result = TextAnalysisService().analyze(
        description=state.get("description", ""),
        main_category_hint=state.get("main_category"),
    )
    state.update(result)
    missing_info = state.get("missing_info") or []
    if missing_info:
        state["error_message"] = "Additional structured repair information is required before creating an estimate."
        return state
    if state.get("validity_label") != ValidityLabel.VALID_REPAIR_REQUEST.value:
        state["error_message"] = "Structured repair request analysis did not classify this as a valid repair request."
    return state
