from app.graphs.nodes import analyze_text as analyze_text_module
from app.graphs.routes import route_text_analysis_result, route_text_validation_result


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


def test_route_text_analysis_result_stops_on_missing_info() -> None:
    state = {
        "error_message": "Additional structured repair information is required before creating an estimate.",
        "validity_label": "valid_repair_request",
        "missing_info": ["브랜드/모델명"],
    }

    assert route_text_analysis_result(state) == "end"


def test_route_text_analysis_result_continues_when_structure_is_complete() -> None:
    state = {
        "validity_label": "valid_repair_request",
        "missing_info": [],
    }

    assert route_text_analysis_result(state) == "lookup_base_price_rule"


def test_analyze_text_sets_error_when_nlp_structure_has_missing_info(monkeypatch) -> None:
    class FakeTextAnalysisService:
        def analyze(self, description: str, main_category_hint: str | None = None) -> dict:
            return {
                "main_category": "가전",
                "object_label": "세탁기",
                "problem_label": "소음",
                "repair_task": "가전 점검",
                "validity_label": "valid_repair_request",
                "missing_info": ["브랜드/모델명"],
            }

    monkeypatch.setattr(analyze_text_module, "TextAnalysisService", FakeTextAnalysisService)

    state = {
        "description": "집 세탁기에 소음 문제가 생겼어요.",
        "validity_label": "valid_repair_request",
        "missing_info": [],
    }

    result = analyze_text_module.analyze_text(state)

    assert result["missing_info"] == ["브랜드/모델명"]
    assert result["error_message"] == (
        "Additional structured repair information is required before creating an estimate."
    )
