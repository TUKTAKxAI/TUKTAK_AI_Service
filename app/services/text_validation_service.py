from typing import Any

from app.core.constants import ValidityLabel
from app.services.text_validation_rule_engine import apply_rule_engine


class TextValidationService:
    def validate(self, description: str) -> dict[str, Any]:
        result = apply_rule_engine(description)
        prediction = result["prediction"]

        if prediction == "VALID":
            return {
                "is_valid": True,
                "validity_label": ValidityLabel.VALID_REPAIR_REQUEST.value,
                "message": "Text validation passed.",
                "missing_info": [],
                "rule_engine": result,
            }

        if prediction == "REVIEW_REQUIRED":
            missing_info = self._missing_info(result)
            return {
                "is_valid": False,
                "validity_label": self._review_validity_label(missing_info),
                "message": "Additional repair details are required before creating an estimate.",
                "missing_info": missing_info,
                "rule_engine": result,
            }

        validity_label = self._invalid_validity_label(result)
        return {
            "is_valid": False,
            "validity_label": validity_label,
            "message": self._invalid_message(validity_label),
            "missing_info": self._missing_info(result) if validity_label == ValidityLabel.TOO_VAGUE.value else [],
            "rule_engine": result,
        }

    def _missing_info(self, result: dict[str, Any]) -> list[str]:
        features = result["features"]
        missing_info = []

        if not features["repair_objects"]:
            missing_info.append("repair_object")
        if not features["repair_symptoms"]:
            missing_info.append("repair_symptom")

        return missing_info or ["repair_detail"]

    def _review_validity_label(self, missing_info: list[str]) -> str:
        if "repair_object" in missing_info:
            return ValidityLabel.MISSING_OBJECT.value
        if "repair_symptom" in missing_info:
            return ValidityLabel.MISSING_SYMPTOM.value
        return ValidityLabel.TOO_VAGUE.value

    def _invalid_validity_label(self, result: dict[str, Any]) -> str:
        rules = set(result["matched_rules"])

        if "EMPTY_TEXT" in rules or "TOO_SHORT" in rules:
            return ValidityLabel.TOO_SHORT.value
        if "EXCESSIVE_REPETITION" in rules or "LOW_MEANINGFUL_CHARACTER_RATIO" in rules:
            return ValidityLabel.SPAM_OR_GIBBERISH.value
        if "SPAM_PATTERN" in rules:
            return ValidityLabel.SPAM_OR_GIBBERISH.value
        if "SEVERE_PROFANITY" in rules:
            return ValidityLabel.UNSAFE_INPUT.value
        if "PROFANITY_ONLY" in rules:
            return ValidityLabel.UNSAFE_INPUT.value
        if "OUT_OF_SERVICE_SCOPE" in rules:
            return ValidityLabel.NOT_REPAIR_RELATED.value
        if "NO_REPAIR_SIGNAL" in rules:
            return ValidityLabel.NOT_REPAIR_RELATED.value

        return ValidityLabel.TOO_VAGUE.value

    def _invalid_message(self, validity_label: str) -> str:
        messages = {
            ValidityLabel.TOO_SHORT.value: "The description is too short.",
            ValidityLabel.SPAM_OR_GIBBERISH.value: "The description appears to be spam or gibberish.",
            ValidityLabel.UNSAFE_INPUT.value: "The description contains unsafe or abusive content.",
            ValidityLabel.NOT_REPAIR_RELATED.value: "The description is outside TukTak repair estimate scope.",
            ValidityLabel.TOO_VAGUE.value: "The description does not include enough repair information.",
        }
        return messages.get(validity_label, "Text validation failed.")
