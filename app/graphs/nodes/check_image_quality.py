from app.graphs.state import EstimateState
from app.services.image_service import ImageQualityService


def check_image_quality(state: EstimateState) -> EstimateState:
    result = ImageQualityService().check_paths(state.get("image_paths") or [])
    state["image_quality_valid"] = result["image_quality_valid"]
    state["image_validation_result"] = result["image_validation_result"]
    return state

