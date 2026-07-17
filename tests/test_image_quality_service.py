from pathlib import Path

import pytest

from app.core.constants import ValidityLabel
from app.graphs.nodes.check_image_quality import check_image_quality
from app.graphs.routes import route_image_quality_result
from app.services.image_service import BLUR_DEFECT, EXPOSURE_DEFECT, NORMAL_PHOTO, ImageQualityService


cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")


def _write_image(path: Path, image) -> str:
    ok = cv2.imwrite(str(path), image)
    assert ok
    return str(path)


def test_image_quality_accepts_normal_photo(tmp_path: Path) -> None:
    rng = np.random.default_rng(42)
    image = rng.integers(90, 170, size=(128, 128, 3), dtype=np.uint8)
    image_path = _write_image(tmp_path / "normal.png", image)

    result = ImageQualityService().check_path(image_path)
    validation = result["image_validation_result"]

    print("\n[normal]", validation)
    assert result["image_quality_valid"] is True
    assert validation["defect_type"] == NORMAL_PHOTO
    assert validation["quality_label"] == "정상 사진"


def test_image_quality_rejects_exposure_defect(tmp_path: Path) -> None:
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    image_path = _write_image(tmp_path / "dark.png", image)

    result = ImageQualityService().check_path(image_path)
    validation = result["image_validation_result"]

    print("\n[exposure_defect]", validation)
    assert result["image_quality_valid"] is False
    assert validation["defect_type"] == EXPOSURE_DEFECT
    assert validation["quality_label"] == "노출 불량"
    assert validation["rejection_reasons"] == ["proper_exposure_image"]


def test_image_quality_rejects_blur_defect(tmp_path: Path) -> None:
    image = np.full((128, 128, 3), 128, dtype=np.uint8)
    image_path = _write_image(tmp_path / "flat.png", image)

    result = ImageQualityService().check_path(image_path)
    validation = result["image_validation_result"]

    print("\n[blur_defect]", validation)
    assert result["image_quality_valid"] is False
    assert validation["defect_type"] == BLUR_DEFECT
    assert validation["quality_label"] == "초점 불량"
    assert validation["rejection_reasons"] == ["clear_focus_image"]


def test_check_image_quality_sets_error_and_route_end(tmp_path: Path) -> None:
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    image_path = _write_image(tmp_path / "dark.png", image)
    state = {
        "image_paths": [image_path],
        "missing_info": [],
    }

    result = check_image_quality(state)

    assert result["image_quality_valid"] is False
    assert result["validity_label"] == ValidityLabel.IMAGE_QUALITY_INVALID.value
    assert result["missing_info"] == ["proper_exposure_image"]
    assert result["error_message"] == "Uploaded image quality is not sufficient for repair estimation."
    assert route_image_quality_result(result) == "end"
