from app.graphs.routes import route_text_validation_result


def test_route_text_validation_result_stops_on_validation_error() -> None:
    state = {
        "error_message": "Additional repair details are required before creating an estimate.",
        "validity_label": "missing_symptom",
        "missing_info": ["repair_symptom"],
    }

    assert route_text_validation_result(state) == "end"


def test_route_text_validation_result_continues_when_text_is_valid() -> None:
    state = {
        "validity_label": "valid_repair_request",
        "missing_info": [],
    }

    assert route_text_validation_result(state) == "analyze_text"
