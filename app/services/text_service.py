class TextAnalysisService:
    def analyze(self, description: str, main_category_hint: str | None = None) -> dict[str, str | None]:
        text = description.lower()
        if "벽지" in description or "wallpaper" in text:
            return {
                "main_category": main_category_hint or "INTERIOR",
                "object_label": "wallpaper",
                "problem_label": "damage",
                "repair_task": "wallpaper_partial_repair",
            }
        if "타일" in description or "tile" in text:
            return {
                "main_category": main_category_hint or "BATHROOM",
                "object_label": "tile",
                "problem_label": "crack",
                "repair_task": "tile_partial_repair",
            }
        if "누수" in description or "배관" in description or "leak" in text:
            return {
                "main_category": main_category_hint or "PLUMBING",
                "object_label": "pipe",
                "problem_label": "leak",
                "repair_task": "pipe_leak_repair",
            }
        return {
            "main_category": main_category_hint or "UNKNOWN",
            "object_label": None,
            "problem_label": None,
            "repair_task": None,
        }

