from app.schemas.estimate import EstimateRequest
import app.services.estimate_service as estimate_service
from app.services.estimate_service import EstimateService


def test_estimate_service_adds_downloaded_s3_images_to_graph(monkeypatch) -> None:
    captured = {}

    class DownloadSessionStub:
        def __init__(self, image_s3_keys):
            self.image_s3_keys = image_s3_keys

        def __enter__(self):
            return ["/tmp/downloaded-image.jpg"]

        def __exit__(self, exc_type, exc, tb):
            return False

    class GraphStub:
        def invoke(self, state):
            captured["state"] = state
            return {
                "main_category": "REPAIR",
                "object_label": "wall",
                "problem_label": "tear",
                "repair_task": "wallpaper",
                "min_price": 120000,
                "max_price": 180000,
                "duration_minutes": 120,
                "confidence": 0.9,
                "validity_label": "valid_repair_request",
            }

    monkeypatch.setattr(estimate_service, "S3ImageDownloadSession", DownloadSessionStub)
    monkeypatch.setattr(estimate_service, "estimate_graph", GraphStub())

    response = EstimateService().create_estimate(
        EstimateRequest(
            description="wallpaper repair",
            image_paths=["/tmp/local-image.jpg"],
            image_s3_keys=["ai-estimates/1/123/image.jpg"],
        )
    )

    assert response.success is True
    assert captured["state"]["image_paths"] == ["/tmp/local-image.jpg", "/tmp/downloaded-image.jpg"]
