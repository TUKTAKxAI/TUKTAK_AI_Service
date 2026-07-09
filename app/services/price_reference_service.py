import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings


class PriceReferenceService:
    def __init__(self, file_path: str | None = None):
        self.file_path = Path(file_path or settings.price_reference_file_path)

    def find_price_rule(
        self,
        main_category: str | None,
        object_label: str | None,
        problem_label: str | None,
        repair_task: str | None,
    ) -> dict[str, Any] | None:
        if not all([main_category, object_label, problem_label, repair_task]):
            return None

        for row in self._load_rows(str(self.file_path)):
            if row.get("is_active", "").lower() != "true":
                continue
            if (
                row.get("main_category") == main_category
                and row.get("object_label") == object_label
                and row.get("problem_label") == problem_label
                and row.get("repair_task") == repair_task
            ):
                return self._coerce_row(row)
        return None

    @staticmethod
    @lru_cache(maxsize=8)
    def _load_rows(file_path: str) -> tuple[dict[str, str], ...]:
        path = Path(file_path)
        if not path.exists():
            return tuple()
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return tuple(csv.DictReader(file))

    @staticmethod
    def _coerce_row(row: dict[str, str]) -> dict[str, Any]:
        int_fields = {
            "base_price_min",
            "base_price_max",
            "base_duration_minutes",
            "material_cost_min",
            "material_cost_max",
            "labor_cost_min",
            "labor_cost_max",
            "visit_fee_min",
            "visit_fee_max",
            "unit_price_min",
            "unit_price_max",
        }
        bool_fields = {"requires_license", "is_image_important", "is_active"}
        coerced: dict[str, Any] = dict(row)
        for field in int_fields:
            coerced[field] = int(row[field]) if row.get(field) else 0
        for field in bool_fields:
            coerced[field] = row.get(field, "").lower() == "true"
        return coerced

