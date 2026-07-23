import json
from typing import Any

from app.core.config import settings


RISK_REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "risk_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "summary": {"type": "string"},
        "risk_items": {"type": "array", "items": {"$ref": "#/$defs/risk_item"}},
        "checklist": {"type": "array", "items": {"$ref": "#/$defs/checklist_item"}},
        "additional_cost_risks": {"type": "array", "items": {"$ref": "#/$defs/risk_detail"}},
        "safety_risks": {"type": "array", "items": {"$ref": "#/$defs/risk_detail"}},
        "contract_risks": {"type": "array", "items": {"$ref": "#/$defs/risk_detail"}},
        "field_variable_risks": {"type": "array", "items": {"$ref": "#/$defs/risk_detail"}},
    },
    "required": [
        "risk_score",
        "risk_level",
        "summary",
        "risk_items",
        "checklist",
        "additional_cost_risks",
        "safety_risks",
        "contract_risks",
        "field_variable_risks",
    ],
    "additionalProperties": False,
    "$defs": {
        "risk_item": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "level": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["category", "level", "title", "description"],
            "additionalProperties": False,
        },
        "checklist_item": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "checked": {"type": "boolean"},
            },
            "required": ["label", "checked"],
            "additionalProperties": False,
        },
        "risk_detail": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "expected_impact": {"type": "string"},
                "evidence_category": {"type": "string"},
            },
            "required": ["title", "expected_impact", "evidence_category"],
            "additionalProperties": False,
        },
    },
}


class OpenAIRiskReportService:
    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def can_generate(self) -> bool:
        return bool(_api_key())

    def generate(self, payload: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        if not self.can_generate():
            raise RuntimeError("OpenAI API key for risk report is not configured.")
        client = self._client or _build_client()
        response = client.responses.create(
            model=settings.openai_risk_report_model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are TukTak AI's repair risk report assistant. "
                                "Prioritize reliable, evidence-backed guidance. Use the provided RAG evidence, "
                                "estimate data, and repair-domain reasoning. "
                                "Return concise Korean customer-facing risk report JSON. "
                                "Write in short, scannable phrases for a mobile UI. "
                                "Even when RAG evidence is missing for some categories, fill every required display field "
                                "with practical risk guidance based on the estimate data, and clearly mention that the "
                                "direct evidence is limited. For legal, contract, safety, consumer dispute, and pricing "
                                "claims, distinguish confirmed evidence from practical caution. Do not invent law names, "
                                "article numbers, legal guarantees, exact regulations, compensation rules, or hidden site "
                                "conditions unless they are explicitly present in the supplied evidence. If evidence is "
                                "weak, phrase it as a checklist item or caution, not as a legal conclusion."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "estimate": payload,
                                    "rag_evidence": evidence,
                                    "risk_categories": ["PRICE", "EXTRA_COST", "SAFETY", "CONTRACT", "FIELD"],
                                    "scoring_rule": "0=low risk, 100=high risk. Use MEDIUM unless evidence strongly supports LOW/HIGH.",
                                    "evidence_policy": (
                                        "Use high-reliability RAG documents first. Prefer source-backed statements. "
                                        "When RAG evidence is absent, provide cautious practical guidance based on the "
                                        "estimate only and explicitly state that direct supporting evidence is limited. "
                                        "Do not fabricate legal citations or official standards."
                                    ),
                                    "output_requirement": (
                                        "Populate summary, risk_items, checklist, additional_cost_risks, safety_risks, "
                                        "contract_risks, and field_variable_risks. Do not return empty arrays unless the "
                                        "category is truly irrelevant to the repair request. Keep each risk item title "
                                        "within 24 Korean characters, each risk item description within 90 Korean "
                                        "characters, summary within 180 Korean characters, and each detail item within "
                                        "110 Korean characters. Avoid paragraph-style long explanations."
                                    ),
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "tuktak_risk_report",
                    "strict": True,
                    "schema": RISK_REPORT_SCHEMA,
                }
            },
            timeout=settings.openai_risk_report_timeout_seconds,
        )
        return json.loads(_extract_response_text(response))


def _api_key() -> str | None:
    return settings.openai_api_key_ai_riskreport or settings.openai_api_key


def _build_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is required for risk report generation.") from exc
    return OpenAI(api_key=_api_key(), timeout=settings.openai_risk_report_timeout_seconds)


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                return text
            if isinstance(content, dict) and content.get("text"):
                return str(content["text"])
    raise ValueError("OpenAI response did not include output text.")
