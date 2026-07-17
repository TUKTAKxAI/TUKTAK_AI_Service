from app.graphs.nodes.calculate_estimate import calculate_estimate_from_similar_cases
from app.graphs.nodes.search_similar_cases import evaluate_similar_cases
from app.graphs.routes import route_similar_cases_enough


def test_evaluate_similar_cases_accepts_three_complete_cases_when_thresholds_are_unset() -> None:
    state = {
        "similar_cases": [
            {"price": 100000, "duration_minutes": 60},
            {"price": 120000, "duration_minutes": 80},
            {"price": 150000, "duration_minutes": 100},
        ]
    }

    result = evaluate_similar_cases(state)

    assert result["similar_cases_enough"] is True
    assert route_similar_cases_enough(result) == "calculate_estimate_from_similar_cases"


def test_evaluate_similar_cases_without_cases_falls_back_to_next_estimate_step() -> None:
    state = {"similar_cases": []}

    result = evaluate_similar_cases(state)

    assert result["similar_cases_enough"] is False
    assert route_similar_cases_enough(result) == "calculate_estimate_with_base_price_and_llm"


def test_calculate_estimate_from_similar_cases_uses_mode_labels_and_buffered_price_range() -> None:
    state = {
        "main_category": "UNKNOWN",
        "object_label": "unknown",
        "problem_label": "unknown",
        "repair_task": "unknown",
        "similar_cases": [
            {
                "main_category": "INTERIOR",
                "object_label": "wall",
                "problem_label": "crack",
                "repair_task": "wall_crack_repair",
                "price": 100000,
                "duration_minutes": 60,
            },
            {
                "main_category": "INTERIOR",
                "object_label": "wall",
                "problem_label": "crack",
                "repair_task": "wall_crack_repair",
                "price": 120000,
                "duration_minutes": 90,
            },
            {
                "main_category": "INTERIOR",
                "object_label": "tile",
                "problem_label": "crack",
                "repair_task": "tile_crack_repair",
                "price": 150000,
                "duration_minutes": 120,
            },
        ],
    }

    result = calculate_estimate_from_similar_cases(state)

    assert result["main_category"] == "INTERIOR"
    assert result["object_label"] == "wall"
    assert result["problem_label"] == "crack"
    assert result["repair_task"] == "wall_crack_repair"
    assert result["min_price"] == 90000
    assert result["max_price"] == 165000
    assert result["duration_minutes"] == 90
    assert result["estimate_items"] == [
        {"name": "similar_case_based_estimate", "price_min": 90000, "price_max": 165000}
    ]
    assert result["similar_case_stats"]["raw_price_min"] == 100000
    assert result["similar_case_stats"]["raw_price_max"] == 150000
