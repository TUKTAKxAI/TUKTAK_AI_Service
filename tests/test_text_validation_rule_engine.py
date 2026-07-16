from app.core.constants import ValidityLabel
from app.services.text_validation_rule_engine import FINAL_RULE_CONFIG, apply_rule_engine
from app.services.text_validation_service import TextValidationService


def _print_case(name: str, result: dict) -> None:
    rule_engine = result.get("rule_engine", result)
    print(
        f"\n[{name}] "
        f"is_valid={result.get('is_valid', 'n/a')} "
        f"validity_label={result.get('validity_label', 'n/a')} "
        f"missing_info={result.get('missing_info', [])} "
        f"prediction={rule_engine['prediction']} "
        f"score={rule_engine['score']} "
        f"matched_rules={rule_engine['matched_rules']}"
    )


def test_final_rule_config_matches_report_conclusion() -> None:
    print(f"\n[final_config] {FINAL_RULE_CONFIG}")

    assert FINAL_RULE_CONFIG.object_weight == 1.0
    assert FINAL_RULE_CONFIG.symptom_weight == 2.5
    assert FINAL_RULE_CONFIG.request_weight == 0.5
    assert FINAL_RULE_CONFIG.valid_threshold == 3.5
    assert FINAL_RULE_CONFIG.invalid_threshold == 0.0
    assert FINAL_RULE_CONFIG.repetition_threshold == 0.70
    assert FINAL_RULE_CONFIG.min_text_length == 2


def test_rule_engine_accepts_clear_repair_request() -> None:
    result = apply_rule_engine("\ubcc0\uae30 \ub9c9\ud798")
    _print_case("clear_repair_request", result)

    assert result["prediction"] == "VALID"
    assert result["score"] == 3.5
    assert result["matched_rules"] == ["REPAIR_OBJECT", "REPAIR_SYMPTOM"]
    assert result["features"]["repair_objects"] == ["\ubcc0\uae30"]
    assert result["features"]["repair_symptoms"] == ["\ub9c9\ud798"]


def test_rule_engine_accepts_normal_repair_request_with_request_word() -> None:
    result = apply_rule_engine(
        "\ubcbd\uc9c0\uac00 \ucc22\uc5b4\uc838\uc11c "
        "\ubd80\ubd84 \ubcf4\uc218\uac00 \ud544\uc694\ud574\uc694."
    )
    _print_case("normal_repair_request", result)

    assert result["prediction"] == "VALID"
    assert result["score"] >= FINAL_RULE_CONFIG.valid_threshold
    assert result["matched_rules"] == [
        "REPAIR_OBJECT",
        "REPAIR_SYMPTOM",
        "REPAIR_REQUEST_WORD",
    ]


def test_service_maps_review_required_to_needs_more_info_label() -> None:
    result = TextValidationService().validate("\ubcbd\uc9c0")
    _print_case("needs_more_info", result)

    assert result["is_valid"] is False
    assert result["validity_label"] == ValidityLabel.MISSING_SYMPTOM.value
    assert result["missing_info"] == ["repair_symptom"]
    assert result["rule_engine"]["prediction"] == "REVIEW_REQUIRED"


def test_service_rejects_too_short_text() -> None:
    result = TextValidationService().validate("\u314b")
    _print_case("too_short", result)

    assert result["is_valid"] is False
    assert result["validity_label"] == ValidityLabel.TOO_SHORT.value
    assert result["missing_info"] == []
    assert result["rule_engine"]["matched_rules"] == ["TOO_SHORT"]


def test_service_rejects_spam_or_gibberish() -> None:
    spam_result = TextValidationService().validate(
        "\uc800\uae08\ub9ac \ub300\ucd9c \uc0c1\ub2f4 "
        "\uac00\ub2a5\ud569\ub2c8\ub2e4."
    )
    gibberish_result = TextValidationService().validate("\u314b\u314b\u314b\u314b\u314b\u314b")
    _print_case("spam", spam_result)
    _print_case("gibberish", gibberish_result)

    assert spam_result["is_valid"] is False
    assert spam_result["validity_label"] == ValidityLabel.SPAM_OR_GIBBERISH.value
    assert spam_result["rule_engine"]["matched_rules"] == ["SPAM_PATTERN"]

    assert gibberish_result["is_valid"] is False
    assert gibberish_result["validity_label"] == ValidityLabel.SPAM_OR_GIBBERISH.value
    assert gibberish_result["rule_engine"]["matched_rules"] == ["EXCESSIVE_REPETITION"]


def test_service_rejects_out_of_scope_request() -> None:
    result = TextValidationService().validate(
        "\ud734\ub300\ud3f0 \uc561\uc815\uc774 \uae68\uc84c\uc5b4\uc694. "
        "\uc218\ub9ac \uacac\uc801\uc744 \ubc1b\uace0 \uc2f6\uc2b5\ub2c8\ub2e4."
    )
    _print_case("out_of_scope", result)

    assert result["is_valid"] is False
    assert result["validity_label"] == ValidityLabel.NOT_REPAIR_RELATED.value
    assert result["missing_info"] == []
    assert result["rule_engine"]["matched_rules"] == ["OUT_OF_SERVICE_SCOPE"]
