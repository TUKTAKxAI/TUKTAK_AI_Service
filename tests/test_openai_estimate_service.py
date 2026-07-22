from pathlib import Path

from app.graphs.nodes import calculate_estimate
from app.graphs.nodes.calculate_estimate import calculate_estimate_with_base_price_and_llm


class FakeOpenAIEstimateService:
    def can_generate(self, state):
        return True

    def generate_estimate(self, state):
        return {
            "expected_price_min": 110000,
            "expected_price_max": 210000,
            "expected_duration_minutes": 120,
            "confidence_score": 0.86,
            "estimate_items": [
                {"name": "visit_fee", "price_min": 20000, "price_max": 30000},
                {"name": "repair_labor", "price_min": 70000, "price_max": 130000},
                {"name": "materials", "price_min": 20000, "price_max": 50000},
            ],
            "summary": "사진과 설명 기준으로 부분 보수 가능성이 높습니다.",
            "warnings": ["현장 상태에 따라 추가 비용이 발생할 수 있습니다."],
        }


def test_calculate_base_price_estimate_applies_gpt5_mini_result(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "repair.jpg"
    image_path.write_bytes(b"fake-image")
    monkeypatch.setattr(calculate_estimate, "OpenAIEstimateService", FakeOpenAIEstimateService)

    state = {
        "description": "벽에 균열이 생겨 보수가 필요합니다.",
        "validity_label": "valid_repair_request",
        "main_category": "도배/벽면",
        "object_label": "벽",
        "problem_label": "균열",
        "repair_task": "벽면 보수",
        "image_paths": [str(image_path)],
        "warnings": [],
        "similar_cases": [],
        "base_price_rule": {
            "base_price_min": 100000,
            "base_price_max": 250000,
            "base_duration_minutes": 150,
            "visit_fee_min": 15000,
            "visit_fee_max": 25000,
            "labor_cost_min": 60000,
            "labor_cost_max": 140000,
            "material_cost_min": 20000,
            "material_cost_max": 80000,
        },
    }

    result = calculate_estimate_with_base_price_and_llm(state)

    assert result["llm_used"] is True
    assert result["estimate_method"] == "gpt5_mini_final_estimate"
    assert result["min_price"] == 128000
    assert result["max_price"] == 192000
    assert result["duration_minutes"] == 120
    assert result["confidence"] == 0.86
    assert result["llm_summary"] == "사진과 설명 기준으로 부분 보수 가능성이 높습니다."
    assert result["warnings"] == [
        "현장 상태에 따라 추가 비용이 발생할 수 있습니다.",
        "Estimate price range was narrowed to stay within 1.5x.",
    ]
