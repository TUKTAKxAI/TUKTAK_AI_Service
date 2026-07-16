from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_estimate_with_base_price_reference() -> None:
    response = client.post(
        "/api/v1/ai/estimates",
        json={
            "description": "벽지가 찢어져서 부분 보수가 필요해요.",
            "image_urls": ["https://example.com/wallpaper.jpg"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["status"] == "completed"
    assert body["code"] == "ESTIMATE_COMPLETED"
    assert body["estimate"]["repair_task"] == "wallpaper_partial_repair"
    assert body["estimate"]["expected_price_min"] == 50000
    assert body["estimate"]["expected_price_max"] == 90000


def test_create_estimate_rejects_too_short_description() -> None:
    response = client.post("/api/v1/ai/estimates", json={"description": "ㅋ"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["status"] == "validation_failed"
    assert body["code"] == "ESTIMATE_VALIDATION_TOO_SHORT"
    assert body["error"]["validity_label"] == "too_short"


def test_create_estimate_returns_needs_more_info() -> None:
    response = client.post("/api/v1/ai/estimates", json={"description": "벽지"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["status"] == "needs_more_info"
    assert body["code"] == "ESTIMATE_NEEDS_MORE_INFO"
    assert body["error"]["validity_label"] == "missing_symptom"
    assert body["error"]["missing_info"] == ["repair_symptom"]
