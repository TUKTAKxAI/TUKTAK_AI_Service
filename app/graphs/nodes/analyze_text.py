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
    return state

