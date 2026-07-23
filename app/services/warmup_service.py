import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from app.core.config import settings


_warmup_lock = threading.Lock()
_warmup_status: dict[str, Any] = {
    "status": "not_started",
    "started_at": None,
    "finished_at": None,
    "duration_seconds": None,
    "steps": {},
    "error": None,
}


def get_warmup_status() -> dict[str, Any]:
    return dict(_warmup_status)


def start_background_warmup() -> dict[str, Any]:
    if _warmup_status["status"] == "running":
        return get_warmup_status()

    thread = threading.Thread(target=warmup_models, daemon=True)
    thread.start()
    return get_warmup_status()


def warmup_models() -> dict[str, Any]:
    if not _warmup_lock.acquire(blocking=False):
        return get_warmup_status()

    started_at = time.time()
    _warmup_status.update(
        {
            "status": "running",
            "started_at": started_at,
            "finished_at": None,
            "duration_seconds": None,
            "steps": {},
            "error": None,
        }
    )
    try:
        _run_step("nlp_structuring", _warmup_nlp_structuring)
        _run_step("image_embedding", _warmup_image_embedding)
        if settings.warmup_risk_embedding:
            _run_step("risk_embedding", _warmup_risk_embedding)
        else:
            _warmup_status["steps"]["risk_embedding"] = {
                "status": "skipped",
                "started_at": None,
                "duration_seconds": 0,
                "error": None,
            }
        _warmup_status["status"] = "completed"
    except Exception as exc:
        _warmup_status["status"] = "failed"
        _warmup_status["error"] = str(exc)
    finally:
        finished_at = time.time()
        _warmup_status["finished_at"] = finished_at
        _warmup_status["duration_seconds"] = round(finished_at - started_at, 3)
        _warmup_lock.release()
    return get_warmup_status()


def _run_step(name: str, func) -> None:
    step_started_at = time.time()
    _warmup_status["steps"][name] = {
        "status": "running",
        "started_at": step_started_at,
        "duration_seconds": None,
        "error": None,
    }
    try:
        func()
        _warmup_status["steps"][name]["status"] = "completed"
    except Exception as exc:
        _warmup_status["steps"][name]["status"] = "failed"
        _warmup_status["steps"][name]["error"] = str(exc)
        raise
    finally:
        _warmup_status["steps"][name]["duration_seconds"] = round(time.time() - step_started_at, 3)


def _warmup_nlp_structuring() -> None:
    from app.services.nlp_structure_service import NLPStructureService

    NLPStructureService().analyze("벽지가 찢어져서 부분 보수가 필요합니다. 피해 면적은 1평 이하입니다.")


def _warmup_image_embedding() -> None:
    from PIL import Image

    from app.services.image_embedding_service import ImageEmbeddingService

    with tempfile.TemporaryDirectory(prefix="tuktak-warmup-image-") as temp_dir:
        image_path = Path(temp_dir) / "warmup.jpg"
        Image.new("RGB", (128, 128), color=(128, 128, 128)).save(image_path)
        ImageEmbeddingService().embed_image_path(str(image_path))


def _warmup_risk_embedding() -> None:
    from app.rag.embeddings import get_risk_embedding_service

    get_risk_embedding_service().embed_text("계약 전 추가 비용과 작업 범위를 확인합니다.")
