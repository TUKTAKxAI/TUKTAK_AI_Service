from typing import Any

from app.core.config import settings
from app.rag.document_loader import RiskDocument, load_risk_documents
from app.rag.embeddings import RiskEmbeddingService, get_risk_embedding_service
from app.rag.vector_store import get_chroma_settings


RISK_CATEGORIES = ("PRICE", "EXTRA_COST", "SAFETY", "CONTRACT", "FIELD")
RISK_THRESHOLDS = {
    "PRICE": lambda: settings.risk_rag_price_threshold,
    "EXTRA_COST": lambda: settings.risk_rag_extra_cost_threshold,
    "SAFETY": lambda: settings.risk_rag_safety_threshold,
    "CONTRACT": lambda: settings.risk_rag_contract_threshold,
    "FIELD": lambda: settings.risk_rag_field_threshold,
}


class RiskDocumentRetriever:
    def __init__(
        self,
        collection: Any | None = None,
        embedding_service: RiskEmbeddingService | None = None,
        documents: list[RiskDocument] | None = None,
    ) -> None:
        self._collection = collection
        self._embedding_service = embedding_service or get_risk_embedding_service()
        self._documents = documents

    def search(self, payload: dict[str, Any], risk_category: str) -> list[dict[str, Any]]:
        risk_category = risk_category.upper()
        if self._documents is not None and self._collection is None:
            return self._search_in_memory(payload, risk_category)
        collection = self._get_collection()
        if collection is None:
            return self._search_in_memory(payload, risk_category)

        self._ensure_collection_loaded(collection)
        query = _build_query_text(payload, risk_category)
        query_embedding = self._embedding_service.embed_text(query)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(settings.risk_rag_top_k * 5, settings.risk_rag_top_k),
            where={"risk_category": risk_category},
            include=["metadatas", "documents", "distances"],
        )
        docs = _format_chroma_result(result)
        docs = _filter_by_category(docs, payload.get("main_category"))
        if risk_category == "PRICE":
            docs = [doc for doc in docs if doc.get("document_type") != "STAT_DATA"]
        threshold = _threshold(risk_category)
        passed_docs = [doc for doc in docs if doc["relevance_score"] >= threshold]
        if passed_docs:
            return passed_docs[: settings.risk_rag_top_k]
        return [_mark_supporting_evidence(doc, threshold) for doc in docs[: settings.risk_rag_top_k]]

    def _search_in_memory(self, payload: dict[str, Any], risk_category: str) -> list[dict[str, Any]]:
        documents = self._documents if self._documents is not None else load_risk_documents()
        candidates = [doc for doc in documents if doc.metadata.get("risk_category") == risk_category]
        category_candidates = [
            doc
            for doc in candidates
            if _category_matches(doc.metadata.get("category"), payload.get("main_category"))
        ]
        candidates = category_candidates or candidates
        if risk_category == "PRICE":
            candidates = [doc for doc in candidates if doc.metadata.get("document_type") != "STAT_DATA"]
        if not candidates:
            return []

        query_embedding = self._embedding_service.embed_text(_build_query_text(payload, risk_category))
        candidate_embeddings = self._embedding_service.embed_texts([doc.text for doc in candidates])
        scored = []
        below_threshold = []
        threshold = _threshold(risk_category)
        for doc, embedding in zip(candidates, candidate_embeddings, strict=False):
            score = _dot(query_embedding, embedding)
            formatted = _format_document(doc, score)
            if score >= threshold:
                scored.append(formatted)
            else:
                below_threshold.append(formatted)
        if not scored:
            below_threshold.sort(key=lambda item: item["relevance_score"], reverse=True)
            return [
                _mark_supporting_evidence(doc, threshold)
                for doc in below_threshold[: settings.risk_rag_top_k]
            ]
        scored.sort(key=lambda item: item["relevance_score"], reverse=True)
        return scored[: settings.risk_rag_top_k]

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
        except ImportError:
            return None
        chroma_settings = get_chroma_settings()
        client = chromadb.PersistentClient(path=chroma_settings["path"])
        self._collection = client.get_or_create_collection(
            name=chroma_settings["risk_documents"],
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def _ensure_collection_loaded(self, collection: Any) -> None:
        try:
            if collection.count() > 0:
                return
        except Exception:
            return
        documents = self._documents if self._documents is not None else load_risk_documents()
        if not documents:
            return
        texts = [doc.text for doc in documents]
        embeddings = self._embedding_service.embed_texts(texts)
        collection.upsert(
            ids=[doc.document_id for doc in documents],
            documents=texts,
            metadatas=[_chroma_metadata(doc.metadata) for doc in documents],
            embeddings=embeddings,
        )


def _build_query_text(payload: dict[str, Any], risk_category: str) -> str:
    return " ".join(
        str(value or "")
        for value in [
            risk_category,
            payload.get("main_category"),
            payload.get("object_label"),
            payload.get("problem_label"),
            payload.get("repair_task"),
            payload.get("description"),
            payload.get("ai_summary"),
        ]
    )


def _format_chroma_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    ids = _first(result.get("ids"))
    metadatas = _first(result.get("metadatas"))
    documents = _first(result.get("documents"))
    distances = _first(result.get("distances"))
    formatted = []
    for index, doc_id in enumerate(ids):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else 1.0
        formatted.append(
            {
                "document_id": str(doc_id),
                "text": documents[index] if index < len(documents) else "",
                "relevance_score": float(1 - distance),
                **(metadata or {}),
            }
        )
    return formatted


def _filter_by_category(docs: list[dict[str, Any]], main_category: str | None) -> list[dict[str, Any]]:
    matched = [doc for doc in docs if _category_matches(doc.get("category"), main_category)]
    return matched or docs


def _category_matches(document_category: Any, main_category: str | None) -> bool:
    if not main_category:
        return True
    category = str(document_category or "")
    if category == "공통":
        return True
    normalized_doc = _normalize(category)
    normalized_main = _normalize(main_category)
    if normalized_doc in normalized_main or normalized_main in normalized_doc:
        return True
    return bool(_category_aliases(normalized_main) & _category_aliases(normalized_doc))


def _category_aliases(value: str) -> set[str]:
    aliases = set()
    if any(term in value for term in ["도배", "벽지", "벽면", "벽", "천장", "페인트"]):
        aliases.update({"벽", "천장", "벽지", "도배", "페인트", "실내건축"})
    if any(term in value for term in ["타일", "바닥", "욕실", "주방", "싱크"]):
        aliases.update({"타일", "바닥", "욕실", "주방", "실내건축"})
    if any(term in value for term in ["배관", "누수", "방수", "수도", "하수"]):
        aliases.update({"누수", "방수", "배관", "욕실", "주방", "설비"})
    if any(term in value for term in ["창호", "문", "샷시", "샤시", "창문", "발코니"]):
        aliases.update({"창호", "문", "발코니", "실내건축"})
    if any(term in value for term in ["전기", "조명", "배선", "콘센트"]):
        aliases.update({"전기", "조명"})
    if any(term in value for term in ["가전", "에어컨", "보일러", "난방", "세탁기", "냉장고"]):
        aliases.update({"가전", "설비", "보일러", "난방"})
    if any(term in value for term in ["가구", "설치", "수납", "장롱", "붙박이"]):
        aliases.update({"가구", "설치", "실내건축"})
    if "공통" in value:
        aliases.add("공통")
    return aliases


def _threshold(risk_category: str) -> float:
    return float(RISK_THRESHOLDS.get(risk_category, lambda: 0.6)())


def _format_document(document: RiskDocument, relevance_score: float) -> dict[str, Any]:
    return {
        "document_id": document.document_id,
        "text": document.text,
        "relevance_score": relevance_score,
        **document.metadata,
    }


def _mark_supporting_evidence(doc: dict[str, Any], threshold: float) -> dict[str, Any]:
    marked = dict(doc)
    marked["supporting_evidence"] = True
    marked["threshold"] = threshold
    return marked


def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    chroma_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            chroma_metadata[key] = value
        elif isinstance(value, list):
            chroma_metadata[key] = ", ".join(str(item) for item in value)
        else:
            chroma_metadata[key] = str(value)
    return chroma_metadata


def _first(value: Any) -> list[Any]:
    if not value:
        return []
    return value[0] if isinstance(value[0], list) else value


def _dot(left: list[float], right: list[float]) -> float:
    return float(sum(a * b for a, b in zip(left, right, strict=False)))


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "").replace("/", "").replace("_", "").replace("-", "")
