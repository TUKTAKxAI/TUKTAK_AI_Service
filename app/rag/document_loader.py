import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class RiskDocument:
    document_id: str
    text: str
    metadata: dict[str, Any]


def load_risk_documents(path: str | None = None) -> list[RiskDocument]:
    source_path = Path(path or settings.risk_rag_metadata_path or "")
    if not source_path.exists():
        return []

    documents: list[RiskDocument] = []
    for line in source_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        metadata = dict(raw.get("metadata") or {})
        document_id = str(raw.get("id") or metadata.get("document_id") or "")
        text = str(raw.get("text") or metadata.get("summary") or "")
        if not document_id or not text:
            continue
        metadata["document_id"] = document_id
        metadata["risk_category"] = str(metadata.get("risk_category") or "").upper()
        metadata["category"] = str(metadata.get("category") or "공통")
        metadata["document_type"] = str(metadata.get("document_type") or "")
        metadata["source_file"] = str(metadata.get("source_file") or "")
        metadata["source_org"] = str(metadata.get("source_org") or "")
        metadata["service_task"] = str(metadata.get("service_task") or "")
        metadata["reliability_score"] = float(metadata.get("reliability_score") or 0.0)
        documents.append(RiskDocument(document_id=document_id, text=text, metadata=metadata))
    return documents


def split_plain_text(content: str, chunk_size: int = 1000) -> list[str]:
    return [content[index : index + chunk_size] for index in range(0, len(content), chunk_size)]
