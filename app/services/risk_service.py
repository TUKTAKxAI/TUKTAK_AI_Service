from typing import Any

from app.core.config import settings
from app.rag.risk_retriever import RISK_CATEGORIES, RiskDocumentRetriever
from app.schemas.risk_report import RiskReportRequest, RiskReportResponse, RiskReportResult
from app.services.openai_risk_report_service import OpenAIRiskReportService


RISK_WEIGHTS = {
    "PRICE": 10,
    "EXTRA_COST": 20,
    "SAFETY": 30,
    "CONTRACT": 25,
    "FIELD": 15,
}
RISK_DETAIL_FIELDS = {
    "EXTRA_COST": "additional_cost_risks",
    "SAFETY": "safety_risks",
    "CONTRACT": "contract_risks",
    "FIELD": "field_variable_risks",
}


class RiskReportService:
    def __init__(
        self,
        retriever: RiskDocumentRetriever | None = None,
        llm_service: OpenAIRiskReportService | None = None,
    ) -> None:
        self._retriever = retriever or RiskDocumentRetriever()
        self._llm_service = llm_service or OpenAIRiskReportService()

    def create_risk_report(self, payload: RiskReportRequest) -> RiskReportResponse:
        payload_dict = payload.model_dump()
        evidence = _collect_evidence(self._retriever, payload_dict)
        sources = _sources_from_evidence(evidence)

        try:
            llm_result = self._llm_service.generate(payload_dict, evidence)
            result = _result_from_llm(llm_result, evidence, sources)
        except Exception as exc:
            result = _fallback_result(payload_dict, evidence, sources)
            result.summary = (
                f"{result.summary} GPT 리스크 분석 호출에 실패해 RAG 근거와 견적 데이터 기반 "
                f"기본 리포트를 사용했습니다. reason={exc}"
            )

        return RiskReportResponse(
            success=True,
            status="completed",
            code="RISK_REPORT_COMPLETED",
            message="Risk report completed successfully.",
            risk_report=result,
        )


def _collect_evidence(retriever: RiskDocumentRetriever, payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {category: retriever.search(payload, category) for category in RISK_CATEGORIES}


def _result_from_llm(
    llm_result: dict[str, Any],
    evidence: dict[str, list[dict[str, Any]]],
    sources: list[dict[str, Any]],
) -> RiskReportResult:
    score = _clamp_score(llm_result.get("risk_score"))
    fallback = _fallback_result({}, evidence, sources)
    return RiskReportResult(
        report_status="COMPLETED",
        failure_reason=None,
        risk_score=score,
        risk_level=_risk_level(llm_result.get("risk_level"), score),
        summary=str(llm_result.get("summary") or fallback.summary),
        risk_items=_ensure_list(llm_result.get("risk_items"), fallback.risk_items),
        checklist=_ensure_list(llm_result.get("checklist"), fallback.checklist),
        additional_cost_risks=_ensure_list(
            llm_result.get("additional_cost_risks"),
            fallback.additional_cost_risks,
        ),
        safety_risks=_ensure_list(llm_result.get("safety_risks"), fallback.safety_risks),
        contract_risks=_ensure_list(llm_result.get("contract_risks"), fallback.contract_risks),
        field_variable_risks=_ensure_list(
            llm_result.get("field_variable_risks"),
            fallback.field_variable_risks,
        ),
        sources=sources,
        model_name=settings.openai_risk_report_model,
        model_version="risk-rag-v1",
        evidence_status=_evidence_status(evidence),
    )


def _fallback_result(
    payload: dict[str, Any],
    evidence: dict[str, list[dict[str, Any]]],
    sources: list[dict[str, Any]],
) -> RiskReportResult:
    score = _score_from_evidence(evidence)
    risk_items: list[dict[str, Any]] = []
    details: dict[str, list[dict[str, Any]]] = {field: [] for field in RISK_DETAIL_FIELDS.values()}

    for category, docs in evidence.items():
        if not docs:
            risk_items.append(
                {
                    "category": category,
                    "level": "MEDIUM",
                    "title": f"{category} 리스크 확인 필요",
                    "description": "직접 근거 문서가 부족하므로 견적 내용과 일반 시공 리스크 기준으로 확인이 필요합니다.",
                }
            )
            _append_missing_detail(details, category)
            continue

        top_doc = docs[0]
        risk_items.append(
            {
                "category": category,
                "level": _risk_level(None, score),
                "title": f"{category} 리스크 확인",
                "description": str(top_doc.get("text") or "")[:180],
            }
        )
        _append_evidence_detail(details, category, top_doc)

    repair_task = payload.get("repair_task") or payload.get("main_category") or "시공"
    evidence_count = sum(1 for docs in evidence.values() if docs)
    return RiskReportResult(
        report_status="COMPLETED",
        failure_reason=None,
        risk_score=score,
        risk_level=_risk_level(None, score),
        summary=f"{repair_task} 요청에 대해 {evidence_count}/5개 리스크 항목의 근거 문서를 확보했습니다.",
        risk_items=risk_items,
        checklist=[
            {"label": "작업 범위와 제외 항목이 견적서에 명시되어 있는지 확인", "checked": False},
            {"label": "출장비, 자재비, 폐기물 처리비 포함 여부 확인", "checked": False},
            {"label": "AS 기간과 하자보수 조건 확인", "checked": False},
            {"label": "현장 확인 후 추가 비용 발생 조건 확인", "checked": False},
        ],
        additional_cost_risks=details["additional_cost_risks"],
        safety_risks=details["safety_risks"],
        contract_risks=details["contract_risks"],
        field_variable_risks=details["field_variable_risks"],
        sources=sources,
        model_name="rag-fallback",
        model_version="risk-rag-v1",
        evidence_status=_evidence_status(evidence),
    )


def _append_missing_detail(details: dict[str, list[dict[str, Any]]], category: str) -> None:
    field = RISK_DETAIL_FIELDS.get(category)
    if not field:
        return
    details[field].append(
        {
            "title": f"{category} 직접 근거 부족",
            "expected_impact": "현장 조건과 계약 조건에 따라 비용, 일정, 책임 범위가 달라질 수 있습니다.",
            "evidence_category": category,
        }
    )


def _append_evidence_detail(
    details: dict[str, list[dict[str, Any]]],
    category: str,
    top_doc: dict[str, Any],
) -> None:
    field = RISK_DETAIL_FIELDS.get(category)
    if not field:
        return
    details[field].append(
        {
            "title": f"{category} 확인 필요",
            "expected_impact": str(top_doc.get("text") or "")[:160],
            "evidence_category": category,
        }
    )


def _ensure_list(value: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(value, list) and value:
        return value
    return fallback


def _score_from_evidence(evidence: dict[str, list[dict[str, Any]]]) -> int:
    score = 30
    for category, docs in evidence.items():
        if not docs:
            score += RISK_WEIGHTS[category]
        else:
            reliability = float(docs[0].get("reliability_score") or 0.0)
            score += int(RISK_WEIGHTS[category] * max(0.0, 1.0 - reliability))
    return _clamp_score(score)


def _sources_from_evidence(evidence: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    sources = []
    for category, docs in evidence.items():
        for order, doc in enumerate(docs, 1):
            sources.append(
                {
                    "document_id": doc.get("document_id"),
                    "title": doc.get("service_task") or doc.get("document_id"),
                    "source_name": doc.get("source_org") or doc.get("source_file"),
                    "source_file": doc.get("source_file"),
                    "risk_category": category,
                    "relevance_score": doc.get("relevance_score"),
                    "quoted_summary": str(doc.get("text") or "")[:240],
                    "citation_order": order,
                }
            )
    return sources


def _evidence_status(evidence: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    return {category: "OK" if docs else "UNKNOWN" for category, docs in evidence.items()}


def _clamp_score(score: Any) -> int:
    try:
        value = int(score)
    except (TypeError, ValueError):
        value = 50
    return min(100, max(0, value))


def _risk_level(level: Any, score: int) -> str:
    normalized = str(level or "").upper()
    if normalized in {"LOW", "MEDIUM", "HIGH"}:
        return normalized
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"
