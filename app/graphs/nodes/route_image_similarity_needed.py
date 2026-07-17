from app.core.constants import ValidityLabel
from app.graphs.state import EstimateState
from app.rag.retriever import get_image_similarity_category


def mark_image_similarity_route(state: EstimateState) -> EstimateState:
    if state.get("validity_label") != ValidityLabel.VALID_REPAIR_REQUEST.value:
        state["use_image_similarity"] = False
        return state
    state["image_similarity_category"] = get_image_similarity_category(state)
    state["use_image_similarity"] = state["image_similarity_category"] is not None
    return state
