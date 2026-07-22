import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

from app.core.constants import MAX_ESTIMATE_PRICE_RANGE_RATIO
from app.core.config import settings
from app.services.estimate_price_range_service import constrain_price_range


ESTIMATE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "expected_price_min": {"type": "integer", "minimum": 0},
        "expected_price_max": {"type": "integer", "minimum": 0},
        "expected_duration_minutes": {"type": "integer", "minimum": 0},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
        "estimate_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price_min": {"type": "integer", "minimum": 0},
                    "price_max": {"type": "integer", "minimum": 0},
                },
                "required": ["name", "price_min", "price_max"],
                "additionalProperties": False,
            },
        },
        "summary": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "expected_price_min",
        "expected_price_max",
        "expected_duration_minutes",
        "confidence_score",
        "estimate_items",
        "summary",
        "warnings",
    ],
    "additionalProperties": False,
}


class OpenAIEstimateService:
    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def can_generate(self, state: dict[str, Any]) -> bool:
        return bool(_api_key() and _first_existing_image_path(state.get("image_paths") or []))

    def generate_estimate(self, state: dict[str, Any]) -> dict[str, Any]:
        image_path = _first_existing_image_path(state.get("image_paths") or [])
        if not image_path:
            raise ValueError("A local image path is required for GPT estimate generation.")

        client = self._client or _build_client()
        prompt_payload = _build_prompt_payload(state)
        response = client.responses.create(
            model=settings.openai_estimate_model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are TukTak AI's repair estimate assistant. "
                                "Return only the requested structured estimate. "
                                "Use the uploaded image, user description, structured labels, "
                                "similar repair cases, and standard price rule. "
                                "Do not invent hidden damage. Keep the estimate inside the given "
                                "standard price and similar-case evidence unless a warning explains why."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": json.dumps(prompt_payload, ensure_ascii=False)},
                        {"type": "input_image", "image_url": _image_to_data_url(image_path)},
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "tuktak_repair_estimate",
                    "strict": True,
                    "schema": ESTIMATE_OUTPUT_SCHEMA,
                }
            },
            timeout=settings.openai_estimate_timeout_seconds,
        )
        estimate = json.loads(_extract_response_text(response))
        return _normalize_estimate(estimate, state)


def _build_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is required for GPT estimate generation.") from exc

    return OpenAI(api_key=_api_key(), timeout=settings.openai_estimate_timeout_seconds)


def _api_key() -> str | None:
    return settings.openai_api_key_ai_estimate or settings.openai_api_key


def _build_prompt_payload(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": "Generate the final customer-facing repair estimate.",
        "constraints": [
            "All prices are KRW.",
            "expected_price_min must be less than or equal to expected_price_max.",
            f"expected_price_max must not exceed {MAX_ESTIMATE_PRICE_RANGE_RATIO} times expected_price_min.",
            "Use standard_price_rule as the primary guardrail.",
            "Use similar_cases as evidence when present.",
            "Return concise Korean summary text.",
        ],
        "original_description": state.get("description"),
        "structured_request": {
            "main_category": state.get("main_category"),
            "object_label": state.get("object_label"),
            "problem_label": state.get("problem_label"),
            "repair_task": state.get("repair_task"),
        },
        "baseline_estimate": {
            "expected_price_min": state.get("min_price"),
            "expected_price_max": state.get("max_price"),
            "expected_duration_minutes": state.get("duration_minutes"),
            "estimate_method": state.get("estimate_method"),
            "estimate_items": state.get("estimate_items") or [],
        },
        "standard_price_rule": _compact_price_rule(state.get("base_price_rule")),
        "similar_cases": _compact_similar_cases(state.get("similar_cases") or []),
    }


def _compact_price_rule(rule: dict[str, Any] | None) -> dict[str, Any] | None:
    if not rule:
        return None
    fields = [
        "price_rule_id",
        "main_category",
        "object_label",
        "problem_label",
        "repair_task",
        "base_price_min",
        "base_price_max",
        "base_duration_minutes",
        "material_cost_min",
        "material_cost_max",
        "labor_cost_min",
        "labor_cost_max",
        "visit_fee_min",
        "visit_fee_max",
        "extra_cost_notes",
        "unit_type",
        "requires_license",
        "is_image_important",
        "memo",
    ]
    return {field: rule.get(field) for field in fields if field in rule}


def _compact_similar_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted = []
    for case in cases[:3]:
        compacted.append(
            {
                "case_id": case.get("case_id"),
                "main_category": case.get("main_category"),
                "object_label": case.get("object_label"),
                "problem_label": case.get("problem_label"),
                "repair_task": case.get("repair_task"),
                "price": case.get("price"),
                "duration_minutes": case.get("duration_minutes"),
                "image_similarity": case.get("image_similarity"),
                "text": case.get("document") or case.get("text"),
            }
        )
    return compacted


def _first_existing_image_path(image_paths: list[str]) -> str | None:
    for image_path in image_paths:
        if image_path and Path(image_path).exists():
            return image_path
    return None


def _image_to_data_url(image_path: str) -> str:
    path = Path(image_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


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


def _normalize_estimate(estimate: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    price_min = int(estimate["expected_price_min"])
    price_max = int(estimate["expected_price_max"])
    duration = int(estimate["expected_duration_minutes"])
    confidence = float(estimate["confidence_score"])
    warnings = [str(item) for item in estimate.get("warnings") or []]

    if price_min > price_max:
        price_min, price_max = price_max, price_min
        warnings.append("LLM returned reversed price range; values were normalized.")

    rule = state.get("base_price_rule") or {}
    if rule:
        guard_min = int(int(rule.get("base_price_min") or 0) * 0.7)
        guard_max = int(int(rule.get("base_price_max") or 0) * 1.5)
        if guard_min and price_min < guard_min:
            price_min = guard_min
            warnings.append("Minimum price was clamped by the standard price guardrail.")
        if guard_max and price_max > guard_max:
            price_max = guard_max
            warnings.append("Maximum price was clamped by the standard price guardrail.")
        if price_min > price_max:
            price_min = int(rule.get("base_price_min") or price_max)
            price_max = int(rule.get("base_price_max") or price_min)
            warnings.append("Price range was reset to the standard price rule.")

    price_min, price_max, range_constrained = constrain_price_range(price_min, price_max)
    if range_constrained:
        warnings.append(f"Price range was narrowed to stay within {MAX_ESTIMATE_PRICE_RANGE_RATIO}x.")

    items = _normalize_items(estimate.get("estimate_items") or [], price_min, price_max)
    return {
        "expected_price_min": price_min,
        "expected_price_max": price_max,
        "expected_duration_minutes": max(0, duration),
        "confidence_score": min(1.0, max(0.0, confidence)),
        "estimate_items": items,
        "summary": str(estimate.get("summary") or ""),
        "warnings": warnings,
    }


def _normalize_items(items: list[dict[str, Any]], price_min: int, price_max: int) -> list[dict[str, Any]]:
    normalized = []
    for item in items:
        name = str(item.get("name") or "estimate_item")
        item_min = max(0, int(item.get("price_min") or 0))
        item_max = max(0, int(item.get("price_max") or 0))
        if item_min > item_max:
            item_min, item_max = item_max, item_min
        normalized.append({"name": name, "price_min": item_min, "price_max": item_max})
    if normalized:
        return normalized
    return [{"name": "llm_estimate", "price_min": price_min, "price_max": price_max}]
