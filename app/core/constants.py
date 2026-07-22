from enum import StrEnum


class ValidityLabel(StrEnum):
    VALID_REPAIR_REQUEST = "valid_repair_request"
    TOO_SHORT = "too_short"
    TOO_VAGUE = "too_vague"
    NOT_REPAIR_RELATED = "not_repair_related"
    MISSING_OBJECT = "missing_object"
    MISSING_SYMPTOM = "missing_symptom"
    SPAM_OR_GIBBERISH = "spam_or_gibberish"
    UNSAFE_INPUT = "unsafe_input"
    PRICE_ONLY = "price_only"
    IMAGE_REQUIRED = "image_required"
    IMAGE_QUALITY_INVALID = "image_quality_invalid"


TOP_K_SIMILAR_CASES = 3
SIMILAR_CASE_PRICE_MARGIN_RATE = 0.10
MAX_ESTIMATE_PRICE_RANGE_RATIO = 1.5

# TODO: 팀 기준 확정 후 None 값을 실제 기준으로 교체한다.
SIMILARITY_THRESHOLD: float | None = None
PRICE_VARIANCE_THRESHOLD: float | None = None
DURATION_VARIANCE_THRESHOLD: float | None = None
IMAGE_SIMILARITY_REQUIRED_CATEGORIES: list[str] = [
    "ceiling_leak_stain",
    "floor_surface_damage",
    "mold_contamination",
    "tile_crack_damage",
    "wall_crack",
    "wallpaper_lift_tear",
    "screen_damage",
]
IMAGE_SIMILARITY_THRESHOLDS: dict[str, float] = {
    "ceiling_leak_stain": 0.907773,
    "floor_surface_damage": 0.813472,
    "mold_contamination": 0.815195,
    "tile_crack_damage": 0.933618,
    "wall_crack": 0.833714,
    "wallpaper_lift_tear": 0.846475,
    "screen_damage": 0.794690,
}
IMAGE_SIMILARITY_THRESHOLD: float | None = None
TEXT_IMAGE_SIMILARITY_WEIGHT: float | None = None

MIN_BLUR = 90.0
BLUR_SCORE_THRESH = 0.15
DARK_THRESH = 60
BRIGHT_THRESH = 225
MAX_EXPOSURE_RATIO = 0.40
EXPOSURE_FORMULA = "max"
