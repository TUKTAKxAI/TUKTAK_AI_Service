from app.services.risk_service import RiskReportService
from app.schemas.risk_report import RiskReportRequest


class FakeRetriever:
    def __init__(self, missing=None):
        self.missing = set(missing or [])

    def search(self, payload, risk_category):
        if risk_category in self.missing:
            return []
        return [
            {
                "document_id": f"{risk_category}_001",
                "text": f"{risk_category} evidence",
                "service_task": "도배",
                "source_org": "테스트 문서",
                "source_file": "test.pdf",
                "risk_category": risk_category,
                "relevance_score": 0.9,
                "reliability_score": 0.9,
            }
        ]


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, payload, evidence):
        self.calls += 1
        return {
            "risk_score": 63,
            "risk_level": "MEDIUM",
            "summary": "근거 문서 기반 리스크 리포트입니다.",
            "risk_items": [
                {
                    "category": "CONTRACT",
                    "level": "MEDIUM",
                    "title": "계약 조건 확인",
                    "description": "AS 기간을 확인해야 합니다.",
                }
            ],
            "checklist": [{"label": "AS 기간 확인", "checked": False}],
            "additional_cost_risks": [],
            "safety_risks": [],
            "contract_risks": [
                {
                    "title": "계약 리스크",
                    "expected_impact": "분쟁 가능성",
                    "evidence_category": "CONTRACT",
                }
            ],
            "field_variable_risks": [],
        }


class EmptyArrayLLM:
    def generate(self, payload, evidence):
        return {
            "risk_score": 45,
            "risk_level": "MEDIUM",
            "summary": "",
            "risk_items": [],
            "checklist": [],
            "additional_cost_risks": [],
            "safety_risks": [],
            "contract_risks": [],
            "field_variable_risks": [],
        }


def test_risk_report_uses_llm_even_when_three_categories_are_unknown() -> None:
    llm = FakeLLM()
    service = RiskReportService(retriever=FakeRetriever(missing={"EXTRA_COST", "SAFETY", "FIELD"}), llm_service=llm)

    response = service.create_risk_report(RiskReportRequest(main_category="가전", repair_task="에어컨 수리"))

    assert response.success is True
    assert response.risk_report.report_status == "COMPLETED"
    assert response.risk_report.failure_reason is None
    assert response.risk_report.risk_score == 63
    assert response.risk_report.evidence_status["EXTRA_COST"] == "UNKNOWN"
    assert llm.calls == 1


def test_risk_report_uses_llm_when_evidence_is_sufficient() -> None:
    llm = FakeLLM()
    service = RiskReportService(retriever=FakeRetriever(), llm_service=llm)

    response = service.create_risk_report(RiskReportRequest(main_category="도배/벽면", repair_task="도배"))

    assert response.success is True
    assert response.risk_report.report_status == "COMPLETED"
    assert response.risk_report.risk_score == 63
    assert response.risk_report.risk_level == "MEDIUM"
    assert response.risk_report.sources
    assert llm.calls == 1


def test_risk_report_fills_display_fields_when_llm_returns_empty_arrays() -> None:
    service = RiskReportService(
        retriever=FakeRetriever(missing={"EXTRA_COST", "SAFETY", "FIELD"}),
        llm_service=EmptyArrayLLM(),
    )

    response = service.create_risk_report(RiskReportRequest(main_category="appliance", repair_task="aircon repair"))

    report = response.risk_report
    assert report.report_status == "COMPLETED"
    assert report.summary
    assert report.risk_items
    assert report.checklist
    assert report.additional_cost_risks
    assert report.safety_risks
    assert report.field_variable_risks
