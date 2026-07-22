from app.services.estimate_price_range_service import constrain_price_range


def test_constrain_price_range_keeps_range_when_ratio_is_small_enough() -> None:
    price_min, price_max, changed = constrain_price_range(100000, 140000)

    assert price_min == 100000
    assert price_max == 140000
    assert changed is False


def test_constrain_price_range_narrows_range_around_midpoint() -> None:
    price_min, price_max, changed = constrain_price_range(80000, 220000)

    assert price_min == 120000
    assert price_max == 180000
    assert price_max <= price_min * 1.5
    assert changed is True
