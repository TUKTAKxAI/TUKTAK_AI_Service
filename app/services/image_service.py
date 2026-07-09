from pathlib import Path
from typing import Any

from app.core.constants import BRIGHT_THRESH, DARK_THRESH, MAX_EXPOSURE_RATIO, MIN_BLUR


class ImageQualityService:
    def check_paths(self, image_paths: list[str]) -> dict[str, Any]:
        if not image_paths:
            return {
                "image_quality_valid": True,
                "image_validation_result": {"checked": False, "reason": "no_local_image_paths"},
            }

        results = [self.check_path(path) for path in image_paths]
        return {
            "image_quality_valid": all(item["image_quality_valid"] for item in results),
            "image_validation_result": {"images": results},
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

        path = Path(image_path)
        image = cv2.imread(str(path))
        if image is None:
            return {
                "image_quality_valid": False,
                "image_validation_result": {"path": image_path, "error": "image_read_failed"},
            }

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness_mean = float(np.mean(gray))
        dark_pixel_ratio = float(np.mean(gray < DARK_THRESH))
        bright_pixel_ratio = float(np.mean(gray > BRIGHT_THRESH))
        exposure_outlier_ratio = dark_pixel_ratio + bright_pixel_ratio
        result = {
            "path": image_path,
            "blur_score": round(blur_score, 2),
            "brightness_mean": round(brightness_mean, 2),
            "dark_pixel_ratio": round(dark_pixel_ratio, 4),
            "bright_pixel_ratio": round(bright_pixel_ratio, 4),
            "exposure_outlier_ratio": round(exposure_outlier_ratio, 4),
            "is_blurry": blur_score < MIN_BLUR,
            "is_too_dark": brightness_mean < DARK_THRESH,
            "is_too_bright": brightness_mean > BRIGHT_THRESH,
            "is_bad_exposure": exposure_outlier_ratio > MAX_EXPOSURE_RATIO,
        }
        valid = not (
            result["is_blurry"]
            or result["is_too_dark"]
            or result["is_too_bright"]
            or result["is_bad_exposure"]
        )
        return {"image_quality_valid": valid, "image_validation_result": result}

