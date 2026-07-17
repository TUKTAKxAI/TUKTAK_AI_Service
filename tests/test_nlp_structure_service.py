from app.services.nlp_structure_service import _remove_provided_missing_info


def test_remove_provided_brand_model_missing_info_from_additional_answer() -> None:
    description = "거실 에어컨에서 소음이 납니다.\n\n추가 정보:\n브랜드/모델명: 삼성 에어컨"

    result = _remove_provided_missing_info(description, ["브랜드/모델명"])

    assert result == []


def test_keep_missing_info_when_additional_answer_is_for_other_field() -> None:
    description = "거실 에어컨에서 소음이 납니다.\n\n추가 정보:\n고장 증상: 소음이 심해요"

    result = _remove_provided_missing_info(description, ["브랜드/모델명"])

    assert result == ["브랜드/모델명"]


def test_remove_repair_object_and_symptom_answers() -> None:
    description = "추가 정보:\n수리 대상: 에어컨\n고장 증상: 찬바람이 안 나와요"

    result = _remove_provided_missing_info(description, ["repair_object", "repair_symptom"])

    assert result == []
