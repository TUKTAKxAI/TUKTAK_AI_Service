from app.core.constants import ValidityLabel


class TextValidationService:
    def validate(self, description: str) -> dict[str, object]:
        text = description.strip()
        if len(text) < 5:
            return {
                "is_valid": False,
                "validity_label": ValidityLabel.TOO_SHORT.value,
                "message": "설명이 너무 짧습니다.",
                "missing_info": ["description"],
            }

        # TODO: 세부 Rule Engine 조건은 팀 기준 확정 후 구현한다.
        return {
            "is_valid": True,
            "validity_label": ValidityLabel.VALID_REPAIR_REQUEST.value,
            "message": "임시 Rule Engine 기준으로 유효한 수리 요청으로 처리했습니다.",
            "missing_info": [],
        }

