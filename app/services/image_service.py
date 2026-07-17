from pathlib import Path
from typing import Any

from app.core.constants import (
    BLUR_SCORE_THRESH,
    BRIGHT_THRESH,
    DARK_THRESH,
    EXPOSURE_FORMULA,
    MAX_EXPOSURE_RATIO,
    MIN_BLUR,
)


NORMAL_PHOTO = "normal_photo"
BLUR_DEFECT = "blur_defect"
EXPOSURE_DEFECT = "exposure_defect"


class ImageQualityService:
    def check_paths(self, image_paths: list[str]) -> dict[str, Any]:
        if not image_paths:
            return {
                "image_quality_valid": True,
                "image_validation_result": {"checked": False, "reason": "no_local_image_paths"},
            }

        results = [self.check_path(path) for path in image_paths]
        invalid_results = [item for item in results if not item["image_quality_valid"]]
        return {
            "image_quality_valid": not invalid_results,
            "image_validation_result": {
                "checked": True,
                "images": results,
                "invalid_count": len(invalid_results),
                "invalid_reasons": sorted(
                    {
                        reason
                        for item in invalid_results
                        for reason in item["image_validation_result"].get("rejection_reasons", [])
                    }
                ),
            },
        }

    def check_path(self, image_path: str) -> dict[str, Any]:
        try:
            import cv2
            import numpy as np
        except ImportError:
            return {
                "image_quality_valid": True,
                "image_validation_result": {"checked": False, "reason": "opencv_not_installed"},
            }

        image = self._read_image(image_path, cv2, np)
        if image is None:
            return {
                "image_quality_valid": False,
                "image_validation_result": {
                    "path": image_path,
                    "error": "image_read_failed",
                    "defect_type": "image_read_failed",
                    "rejection_reasons": ["readable_image"],
                },
            }

        result = self._inspect_image(image, image_path, cv2, np)
        return {
            "image_quality_valid": result["defect_type"] == NORMAL_PHOTO,
            "image_validation_result": result,
        }

    def _read_image(self, image_path: str, cv2, np):
        path = Path(image_path)
        try:
            image_bytes = np.fromfile(str(path), dtype=np.uint8)
            if image_bytes.size == 0:
                return None
            return cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        except OSError:
            return None

    def _inspect_image(self, image, image_path: str, cv2, np) -> dict[str, Any]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        total_pixels = gray.size

        dark_ratio = float(np.sum(gray < DARK_THRESH) / total_pixels)
        bright_ratio = float(np.sum(gray > BRIGHT_THRESH) / total_pixels)
        if EXPOSURE_FORMULA == "max":
            exposure_score = max(dark_ratio, bright_ratio)
        else:
            exposure_score = dark_ratio + bright_ratio

        blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blur_score = max(0.0, (MIN_BLUR - blur_var) / MIN_BLUR)
        brightness_mean = float(np.mean(gray))

        if exposure_score > MAX_EXPOSURE_RATIO and exposure_score >= blur_score:
            defect_type = EXPOSURE_DEFECT
            quality_label = "노출 불량"
            rejection_reasons = ["proper_exposure_image"]
        elif blur_score > BLUR_SCORE_THRESH:
            defect_type = BLUR_DEFECT
            quality_label = "초점 불량"
            rejection_reasons = ["clear_focus_image"]
        else:
            defect_type = NORMAL_PHOTO
            quality_label = "정상 사진"
            rejection_reasons = []

        return {
            "path": image_path,
            "quality_label": quality_label,
            "defect_type": defect_type,
            "image_quality_valid": defect_type == NORMAL_PHOTO,
            "blur_var": round(blur_var, 4),
            "blur_score": round(blur_score, 4),
            "brightness_mean": round(brightness_mean, 2),
            "dark_ratio": round(dark_ratio, 4),
            "bright_ratio": round(bright_ratio, 4),
            "exposure_score": round(exposure_score, 4),
            "exposure_formula": EXPOSURE_FORMULA,
            "thresholds": {
                "min_blur": MIN_BLUR,
                "blur_score_thresh": BLUR_SCORE_THRESH,
                "dark_thresh": DARK_THRESH,
                "bright_thresh": BRIGHT_THRESH,
                "max_exposure_ratio": MAX_EXPOSURE_RATIO,
            },
            "is_blurry": defect_type == BLUR_DEFECT,
            "is_bad_exposure": defect_type == EXPOSURE_DEFECT,
            "rejection_reasons": rejection_reasons,
        }
