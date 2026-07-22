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
            "description": (
                "\ubcbd\uc9c0\uac00 \ucc22\uc5b4\uc838\uc11c \ubd80\ubd84 \ubcf4\uc218\uac00 "
                "\ud544\uc694\ud574\uc694.\n\n"
                "\ucd94\uac00 \uc815\ubcf4:\n"
                "\ud53c\ud574 \uba74\uc801: 1\ud3c9 \uc774\ud558"
            ),
            "image_urls": ["https://example.com/wallpaper.jpg"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["status"] == "completed"
    assert body["code"] == "ESTIMATE_COMPLETED"
    assert body["estimate"]["repair_task"] == "\ub3c4\ubc30"
    assert body["estimate"]["expected_price_min"] == 120000
    assert body["estimate"]["expected_price_max"] == 180000


def test_create_estimate_rejects_too_short_description() -> None:
    response = client.post("/api/v1/ai/estimates", json={"description": "ㅋ"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["status"] == "validation_failed"
    assert body["code"] == "ESTIMATE_VALIDATION_TOO_SHORT"
    assert body["error"]["validity_label"] == "too_short"


def test_create_estimate_returns_needs_more_info() -> None:
    response = client.post("/api/v1/ai/estimates", json={"description": "\ubcbd\uc9c0"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["status"] == "needs_more_info"
    assert body["code"] == "ESTIMATE_NEEDS_MORE_INFO"
    assert body["error"]["validity_label"] == "missing_symptom"
    assert body["error"]["missing_info"] == ["repair_symptom"]
