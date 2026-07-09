from app.core.constants import IMAGE_SIMILARITY_REQUIRED_CATEGORIES, ValidityLabel
from app.graphs.state import EstimateState


def mark_image_similarity_route(state: EstimateState) -> EstimateState:
    if state.get("validity_label") != ValidityLabel.VALID_REPAIR_REQUEST.value:
        state["use_image_similarity"] = False
        return state
    state["use_image_similarity"] = (state.get("main_category") or "") in IMAGE_SIMILARITY_REQUIRED_CATEGORIES
    return state

