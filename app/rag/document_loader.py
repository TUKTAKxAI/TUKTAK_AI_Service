import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import ZipFile
import xml.etree.ElementTree as ET

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
    if source_path.suffix.lower() == ".xlsx":
        return _load_risk_documents_from_xlsx(source_path)
    if source_path.suffix.lower() == ".jsonl":
        return _load_risk_documents_from_jsonl(source_path)
    return []


def _load_risk_documents_from_jsonl(source_path: Path) -> list[RiskDocument]:
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


def _load_risk_documents_from_xlsx(source_path: Path) -> list[RiskDocument]:
    rows = _read_first_xlsx_sheet(source_path)
    if not rows:
        return []
    headers = [str(header).strip() for header in rows[0]]
    documents: list[RiskDocument] = []
    for values in rows[1:]:
        row = {headers[index]: values[index] if index < len(values) else "" for index in range(len(headers))}
        if str(row.get("status") or "").strip() not in {"사용", "보조사용"}:
            continue
        document_id = str(row.get("document_id") or "").strip()
        if not document_id:
            continue
        summary = str(row.get("summary") or "").strip()
        key_evidence = str(row.get("key_evidence") or "").strip()
        text = key_evidence if key_evidence else summary
        if summary and key_evidence:
            text = f"{summary} {key_evidence}"
        if not text:
            continue
        metadata = {
            "document_id": document_id,
            "document_type": str(row.get("document_type") or "").strip(),
            "source_file": str(row.get("source_file") or "").strip(),
            "source_org": str(row.get("source_org") or row.get("source_file") or "").strip(),
            "category": str(row.get("category") or "공통").strip(),
            "service_task": str(row.get("service_task") or "").strip(),
            "risk_type": _split_csv_like(row.get("risk_type")),
            "retrieval_tags": _split_csv_like(row.get("keywords")),
            "reliability_score": _to_float(row.get("reliability_score")),
            "priority": str(row.get("use_priority") or row.get("priority") or "").strip(),
            "risk_category": str(row.get("risk_category") or "").strip().upper(),
            "summary": summary,
            "key_evidence": key_evidence,
            "status": str(row.get("status") or "").strip(),
        }
        documents.append(RiskDocument(document_id=document_id, text=text, metadata=metadata))
    return documents


def _read_first_xlsx_sheet(source_path: Path) -> list[list[str]]:
    namespace = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(source_path) as archive:
        names = archive.namelist()
        shared_strings = _read_shared_strings(archive, names, namespace)
        sheet_name = "xl/worksheets/sheet1.xml"
        sheet = ET.fromstring(archive.read(sheet_name))
        rows: list[list[str]] = []
        for row in sheet.findall(".//a:row", namespace):
            values: dict[int, str] = {}
            for cell in row.findall("a:c", namespace):
                cell_ref = str(cell.attrib.get("r") or "")
                column_index = _column_index(cell_ref)
                values[column_index] = _xlsx_cell_value(cell, shared_strings, namespace)
            if values:
                max_index = max(values)
                rows.append([values.get(index, "") for index in range(max_index + 1)])
        return rows


def _read_shared_strings(archive: ZipFile, names: list[str], namespace: dict[str, str]) -> list[str]:
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(text.text or "" for text in item.findall(".//a:t", namespace))
        for item in root.findall("a:si", namespace)
    ]


def _xlsx_cell_value(cell: ET.Element, shared_strings: list[str], namespace: dict[str, str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//a:t", namespace)).strip()
    value_node = cell.find("a:v", namespace)
    value = "" if value_node is None else str(value_node.text or "")
    if cell_type == "s" and value:
        return shared_strings[int(value)].strip()
    return value.strip()


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    index = 0
    for char in match.group(1):
        index = index * 26 + ord(char) - ord("A") + 1
    return index - 1


def _split_csv_like(value: Any) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def split_plain_text(content: str, chunk_size: int = 1000) -> list[str]:
    return [content[index : index + chunk_size] for index in range(0, len(content), chunk_size)]
