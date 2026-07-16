import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Any


REPAIR_OBJECTS = {
    "변기",
    "세면대",
    "싱크대",
    "씽크대",
    "싱크데",
    "수도꼭지",
    "샤워기",
    "배수구",
    "배관",
    "보일러",
    "에어컨",
    "전등",
    "스위치",
    "콘센트",
    "차단기",
    "도어락",
    "현관문",
    "방문",
    "문",
    "문틀",
    "창문",
    "방충망",
    "벽지",
    "장판",
    "타일",
    "몰딩",
    "실리콘",
    "수납장",
    "천장",
    "바닥",
    "벽",
    "욕조",
    "환풍기",
    "수전",
    "하수구",
}

REPAIR_SYMPTOMS = {
    "누수",
    "물샘",
    "물이 새",
    "물이샘",
    "물 새",
    "막힘",
    "막혔",
    "안 내려가",
    "역류",
    "고장",
    "작동하지 않",
    "작동안",
    "먹통",
    "안 켜",
    "전원이 안",
    "전원안",
    "깨졌",
    "깨짐",
    "찢어",
    "찢어졌",
    "찢어짐",
    "파손",
    "금이 갔",
    "금감",
    "갈라짐",
    "갈라졌",
    "떨어졌",
    "들떴",
    "들뜸",
    "변색",
    "곰팡이",
    "냄새",
    "악취",
    "소리가",
    "소음",
    "진동",
    "흔들",
    "안 닫",
    "안닫",
    "고정이 풀",
    "새요",
    "새고",
    "샙니다",
}

REPAIR_REQUEST_WORDS = {
    "수리",
    "고쳐",
    "보수",
    "교체",
    "설치",
    "점검",
    "견적",
    "비용",
    "확인",
    "방문",
    "작업",
    "시공",
}

OUT_OF_SCOPE_OBJECTS = {
    "휴대폰",
    "스마트폰",
    "휴대폰 액정",
    "노트북",
    "컴퓨터",
    "모니터",
    "키보드",
    "자동차",
    "타이어",
    "엔진",
    "오토바이",
    "자전거",
    "시계",
    "구두",
    "신발",
    "가방",
    "카메라",
    "게임기",
    "이어폰",
    "태블릿",
    "프린터",
    "드론",
    "악기",
    "골프채",
}

SPAM_WORDS = {
    "대출",
    "당일 승인",
    "신용 조회",
    "무료 쿠폰",
    "현금 지급",
    "부업",
    "재택 부업",
    "당첨",
    "오픈채팅",
    "카카오톡 id",
    "광고",
    "본인 인증",
    "계좌 정지",
    "배송 보류",
    "미납 요금",
    "무료 체험",
}

PROFANITY_WORDS = {
    "시발",
    "씨발",
    "ㅅㅂ",
    "병신",
    "ㅂㅅ",
    "개새끼",
    "미친놈",
    "미친년",
    "좆",
    "존나",
    "꺼져",
    "닥쳐",
}

SEVERE_PROFANITY_WORDS = {
    "죽여",
    "죽인다",
    "살해",
    "협박",
}

URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|[a-z0-9\-]+\.(com|net|kr|org|io)(/\S*)?)",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"\b(?:01[016789][-\s]?\d{3,4}[-\s]?\d{4}|"
    r"\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})\b"
)


@dataclass(frozen=True)
class RuleConfig:
    min_text_length: int = 2
    max_text_length: int = 1000
    repetition_threshold: float = 0.70
    meaningful_ratio_threshold: float = 0.30
    object_weight: float = 1.0
    symptom_weight: float = 2.5
    request_weight: float = 0.5
    out_of_scope_penalty: float = -5.0
    spam_penalty: float = -5.0
    profanity_penalty: float = -3.0
    valid_threshold: float = 3.5
    invalid_threshold: float = 0.0
    severe_profanity_block: bool = True
    profanity_only_block: bool = True
    out_of_scope_block: bool = True
    spam_block: bool = True


FINAL_RULE_CONFIG = RuleConfig()


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""

    normalized = unicodedata.normalize("NFKC", str(text))
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return re.sub(r"(.)\1{3,}", r"\1\1\1", normalized)


def remove_spaces(text: str) -> str:
    return re.sub(r"\s+", "", text)


def contains_any(text: str, dictionary: set[str]) -> list[str]:
    normalized = normalize_text(text)
    no_space_text = remove_spaces(normalized)
    matched = []

    for word in dictionary:
        word_normalized = normalize_text(word)
        word_no_space = remove_spaces(word_normalized)
        if word_normalized in normalized or word_no_space in no_space_text:
            matched.append(word)

    return sorted(set(matched))


def calculate_repetition_ratio(text: str) -> float:
    compact = remove_spaces(text)
    if not compact:
        return 1.0

    counts = Counter(compact)
    return max(counts.values()) / len(compact)


def meaningful_character_ratio(text: str) -> float:
    compact = remove_spaces(text)
    if not compact:
        return 0.0

    meaningful = re.findall(r"[가-힣a-zA-Z0-9]", compact)
    return len(meaningful) / len(compact)


def extract_features(text: str | None) -> dict[str, Any]:
    normalized = normalize_text(text)
    return {
        "normalized_text": normalized,
        "char_length": len(normalized),
        "compact_length": len(remove_spaces(normalized)),
        "repetition_ratio": calculate_repetition_ratio(normalized),
        "meaningful_ratio": meaningful_character_ratio(normalized),
        "url_count": len(URL_PATTERN.findall(normalized)),
        "has_phone": bool(PHONE_PATTERN.search(normalized)),
        "repair_objects": contains_any(normalized, REPAIR_OBJECTS),
        "repair_symptoms": contains_any(normalized, REPAIR_SYMPTOMS),
        "repair_requests": contains_any(normalized, REPAIR_REQUEST_WORDS),
        "out_of_scope_objects": contains_any(normalized, OUT_OF_SCOPE_OBJECTS),
        "spam_words": contains_any(normalized, SPAM_WORDS),
        "profanity_words": contains_any(normalized, PROFANITY_WORDS),
        "severe_profanity_words": contains_any(normalized, SEVERE_PROFANITY_WORDS),
    }


def apply_rule_engine(text: str | None, config: RuleConfig = FINAL_RULE_CONFIG) -> dict[str, Any]:
    features = extract_features(text)
    matched_rules = []
    score = 0.0

    if features["compact_length"] == 0:
        return _result("INVALID", -10.0, ["EMPTY_TEXT"], features)

    if features["compact_length"] < config.min_text_length:
        return _result("INVALID", -10.0, ["TOO_SHORT"], features)

    if features["char_length"] > config.max_text_length:
        return _result("INVALID", -10.0, ["TOO_LONG"], features)

    if (
        features["repetition_ratio"] >= config.repetition_threshold
        and not features["repair_objects"]
        and not features["repair_symptoms"]
    ):
        return _result("INVALID", -10.0, ["EXCESSIVE_REPETITION"], features)

    if features["meaningful_ratio"] < config.meaningful_ratio_threshold:
        return _result("INVALID", -10.0, ["LOW_MEANINGFUL_CHARACTER_RATIO"], features)

    if features["severe_profanity_words"]:
        matched_rules.append("SEVERE_PROFANITY")
        if config.severe_profanity_block:
            return _result("INVALID", -10.0, matched_rules, features)

    if features["spam_words"] or features["url_count"] >= 1:
        score += config.spam_penalty
        matched_rules.append("SPAM_PATTERN")
        if config.spam_block:
            return _result("INVALID", score, matched_rules, features)

    if features["out_of_scope_objects"]:
        score += config.out_of_scope_penalty
        matched_rules.append("OUT_OF_SERVICE_SCOPE")
        if config.out_of_scope_block:
            return _result("INVALID", score, matched_rules, features)

    if features["profanity_words"]:
        score += config.profanity_penalty
        matched_rules.append("PROFANITY")
        has_repair_signal = bool(
            features["repair_objects"]
            or features["repair_symptoms"]
            or features["repair_requests"]
        )
        if config.profanity_only_block and not has_repair_signal:
            return _result("INVALID", score, matched_rules + ["PROFANITY_ONLY"], features)

    if features["repair_objects"]:
        score += config.object_weight
        matched_rules.append("REPAIR_OBJECT")

    if features["repair_symptoms"]:
        score += config.symptom_weight
        matched_rules.append("REPAIR_SYMPTOM")

    if features["repair_requests"]:
        score += config.request_weight
        matched_rules.append("REPAIR_REQUEST_WORD")

    if score >= config.valid_threshold:
        prediction = "VALID"
    elif score <= config.invalid_threshold:
        prediction = "INVALID"
    else:
        prediction = "REVIEW_REQUIRED"

    return _result(prediction, score, matched_rules or ["NO_REPAIR_SIGNAL"], features)


def _result(
    prediction: str,
    score: float,
    matched_rules: list[str],
    features: dict[str, Any],
) -> dict[str, Any]:
    return {
        "prediction": prediction,
        "score": score,
        "matched_rules": matched_rules,
        "features": features,
    }
