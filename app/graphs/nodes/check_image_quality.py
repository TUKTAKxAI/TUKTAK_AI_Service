from app.core.constants import ValidityLabel
from app.graphs.state import EstimateState
from app.services.image_service import ImageQualityService


def check_image_quality(state: EstimateState) -> EstimateState:
    result = ImageQualityService().check_paths(state.get("image_paths") or [])
    state["image_quality_valid"] = result["image_quality_valid"]
    state["image_validation_result"] = result["image_validation_result"]
    if not result["image_quality_valid"]:
        state["validity_label"] = ValidityLabel.IMAGE_QUALITY_INVALID.value
        state["missing_info"] = result["image_validation_result"].get("invalid_reasons", ["valid_image"])
        state["error_message"] = "Uploaded image quality is not sufficient for repair estimation."
    return state
