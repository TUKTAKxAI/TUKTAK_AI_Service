from pathlib import Path
from typing import Any

import numpy as np

from app.core.constants import IMAGE_SIMILARITY_THRESHOLDS
from app.rag.vector_store import get_chroma_settings
from app.services.image_embedding_service import ImageEmbeddingService


METADATA_FIELDS = ("main_category", "object_label", "problem_label", "repair_task")
IMAGE_CATEGORY_RULES = (
    ("ceiling_leak_stain", ("천장", "ceiling"), ("누수", "얼룩", "leak", "stain", "water")),
    ("floor_surface_damage", ("바닥", "floor"), ("손상", "파손", "damage", "scratch")),
    ("mold_contamination", ("곰팡이", "오염", "mold", "contamination", "stain"), ()),
    ("tile_crack_damage", ("타일", "tile"), ("균열", "금감", "깨짐", "crack", "broken", "damage")),
    ("wall_crack", ("벽", "wall"), ("균열", "크랙", "갈라짐", "crack")),
    ("wallpaper_lift_tear", ("도배", "벽지", "wallpaper"), ("들뜸", "찢어짐", "tear", "lift")),
    ("screen_damage", ("방충망", "screen"), ("파손", "찢어짐", "damage", "tear")),
)


class RepairCaseRetriever:
    def __init__(self, collection: Any | None = None, image_embedding_service: ImageEmbeddingService | None = None):
        self._collection = collection
        self._image_embedding_service = image_embedding_service or ImageEmbeddingService()

    def search_text_cases(self, state: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
        collection = self._get_collection()
        where = build_metadata_filter(state)
        if collection is None or where is None:
            return []

        result = collection.get(
            where=where,
            limit=top_k,
            include=["metadatas", "documents"],
        )
        return _format_chroma_get_result(result)

    def search_text_and_image_cases(self, state: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
        collection = self._get_collection()
        where = build_metadata_filter(state)
        image_path = _first_existing_image_path(state.get("image_paths") or [])
        image_category = state.get("image_similarity_category") or get_image_similarity_category(state)
        threshold = get_image_similarity_threshold(image_category)
        if collection is None or where is None or image_path is None or threshold is None:
            return []

        query_embedding = self._image_embedding_service.embed_image_path(image_path)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(top_k * 4, top_k),
            where=where,
            include=["metadatas", "documents", "distances"],
        )
        cases = _format_chroma_query_result(result)
        passed_cases = [
            case
            for case in cases
            if case.get("image_similarity") is not None and case["image_similarity"] >= threshold
        ]
        return passed_cases[:top_k]

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
        except ImportError:
            return None

        chroma_settings = get_chroma_settings()
        client = chromadb.PersistentClient(path=chroma_settings["path"])
        self._collection = client.get_or_create_collection(name=chroma_settings["repair_cases"])
        return self._collection


def build_metadata_filter(state: dict[str, Any]) -> dict[str, Any] | None:
    conditions = [
        {field: state[field]}
        for field in METADATA_FIELDS
        if state.get(field) not in {None, ""}
    ]
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def get_image_similarity_category(state: dict[str, Any]) -> str | None:
    text = _normalize_metadata_text(
        " ".join(str(state.get(field) or "") for field in METADATA_FIELDS)
    )
    for category, primary_terms, secondary_terms in IMAGE_CATEGORY_RULES:
        if _has_any(text, primary_terms) and (not secondary_terms or _has_any(text, secondary_terms)):
            return category
    return None


def get_image_similarity_threshold(category: str | None) -> float | None:
    if not category:
        return None
    return IMAGE_SIMILARITY_THRESHOLDS.get(category)


def _first_existing_image_path(image_paths: list[str]) -> str | None:
    for image_path in image_paths:
        if Path(image_path).exists():
            return image_path
    return None


def _format_chroma_get_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    ids = result.get("ids") or []
    metadatas = result.get("metadatas") or []
    documents = result.get("documents") or []
    return [
        _format_case(ids[index], _safe_get(metadatas, index), _safe_get(documents, index), None)
        for index in range(len(ids))
    ]


def _format_chroma_query_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    ids = _first_query_list(result.get("ids"))
    metadatas = _first_query_list(result.get("metadatas"))
    documents = _first_query_list(result.get("documents"))
    distances = _first_query_list(result.get("distances"))
    return [
        _format_case(
            ids[index],
            _safe_get(metadatas, index),
            _safe_get(documents, index),
            _cosine_similarity_from_distance(_safe_get(distances, index)),
        )
        for index in range(len(ids))
    ]


def _format_case(
    case_id: str,
    metadata: dict[str, Any] | None,
    document: str | None,
    image_similarity: float | None,
) -> dict[str, Any]:
    metadata = metadata or {}
    case = {
        "case_id": case_id,
        "document": document,
        "metadata": metadata,
        "price": _first_int(metadata, "price", "final_price", "total_price", "amount"),
        "duration_minutes": _first_int(metadata, "duration_minutes", "work_minutes", "estimated_minutes"),
    }
    if image_similarity is not None:
        case["image_similarity"] = image_similarity
    for field in METADATA_FIELDS:
        if field in metadata:
            case[field] = metadata[field]
    return case


def _cosine_similarity_from_distance(distance: Any) -> float | None:
    if distance is None:
        return None
    return float(1 - distance)


def _normalize_metadata_text(value: str) -> str:
    return value.lower().replace(" ", "").replace("_", "").replace("-", "")


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(_normalize_metadata_text(term) in text for term in terms)


def _first_query_list(value: Any) -> list[Any]:
    if not value:
        return []
    return value[0] if isinstance(value[0], list) else value


def _safe_get(items: list[Any], index: int) -> Any | None:
    return items[index] if index < len(items) else None


def _first_int(metadata: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = metadata.get(key)
        if value is not None and value != "":
            return int(float(value))
    return None


def cosine_similarity(left: list[float], right: list[float]) -> float:
    left_array = np.asarray(left, dtype=np.float32)
    right_array = np.asarray(right, dtype=np.float32)
    denominator = float(np.linalg.norm(left_array) * np.linalg.norm(right_array))
    if denominator == 0:
        return 0.0
    return float(np.dot(left_array, right_array) / denominator)
