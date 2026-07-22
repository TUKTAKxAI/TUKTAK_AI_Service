from app.core.constants import MAX_ESTIMATE_PRICE_RANGE_RATIO


def constrain_price_range(
    price_min: int | None,
    price_max: int | None,
    max_ratio: float = MAX_ESTIMATE_PRICE_RANGE_RATIO,
) -> tuple[int | None, int | None, bool]:
    if price_min is None or price_max is None:
        return price_min, price_max, False

    normalized_min = max(0, int(price_min))
    normalized_max = max(0, int(price_max))
    if normalized_min > normalized_max:
        normalized_min, normalized_max = normalized_max, normalized_min

    if normalized_min <= 0 or normalized_max <= normalized_min * max_ratio:
        return normalized_min, normalized_max, False

    midpoint = (normalized_min + normalized_max) / 2
    adjusted_min = _round_to_thousand((2 * midpoint) / (1 + max_ratio))
    adjusted_max = _round_to_thousand(adjusted_min * max_ratio)

    if adjusted_max > adjusted_min * max_ratio:
        adjusted_max = int(adjusted_min * max_ratio)

    return max(0, adjusted_min), max(adjusted_min, adjusted_max), True


def _round_to_thousand(value: float) -> int:
    return int(round(value / 1000) * 1000)
