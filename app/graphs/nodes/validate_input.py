from app.core.constants import ValidityLabel
from app.graphs.state import EstimateState


def validate_input(state: EstimateState) -> EstimateState:
    description = state.get("description", "").strip()
    image_urls = state.get("image_urls") or []
    image_paths = state.get("image_paths") or []
    if not description and not image_urls and not image_paths:
        state["validity_label"] = ValidityLabel.IMAGE_REQUIRED.value
        state["missing_info"] = ["description", "images"]
        state["error_message"] = "설명 또는 이미지가 필요합니다."
    return state

