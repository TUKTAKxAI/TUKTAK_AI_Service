from app.graphs.state import EstimateState
from app.services.text_validation_service import TextValidationService


def validate_text(state: EstimateState) -> EstimateState:
    result = TextValidationService().validate(state.get("description", ""))
    state["text_validation_result"] = result
    state["validity_label"] = result["validity_label"]
    state["missing_info"] = result.get("missing_info", [])
    if not result["is_valid"]:
        state["error_message"] = result["message"]
    return state

