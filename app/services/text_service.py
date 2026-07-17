from typing import Any

from app.services.nlp_structure_service import NLPStructureService


class TextAnalysisService:
    def analyze(self, description: str, main_category_hint: str | None = None) -> dict[str, Any]:
        result = NLPStructureService().analyze(description)
        if main_category_hint:
            result["main_category"] = main_category_hint
        return result
