from __future__ import annotations

import re
from typing import Any

from app.schemas.evaluation import AnswerEvidenceItem

MAX_EVIDENCE_ITEMS = 6
MAX_QUOTE_LENGTH = 80
VALID_DIMENSIONS = {"logic", "technical", "expression", "project_depth"}
VALID_POLARITIES = {"strength", "improvement"}
FILLER_WORDS = ("怎么说", "对吧", "那个", "就是", "然后", "其实", "嗯", "啊", "呃")
STRUCTURE_SIGNALS = (
    "首先",
    "其次",
    "最后",
    "第一",
    "第二",
    "第三",
    "因为",
    "所以",
    "例如",
    "总结",
)
PRIVATE_PATTERNS = (
    re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
)


def validate_evidence_items(
    raw_items: Any,
    answer_text: str,
    limit: int = MAX_EVIDENCE_ITEMS,
) -> list[dict[str, str | None]]:
    if not isinstance(raw_items, list):
        return []

    validated: list[dict[str, str | None]] = []
    for raw_item in raw_items:
        if len(validated) >= limit:
            break
        if not isinstance(raw_item, dict):
            continue
        dimension = _clean(raw_item.get("dimension"))
        polarity = _clean(raw_item.get("polarity"))
        quote = _clean(raw_item.get("quote"))
        reason = _clean(raw_item.get("reason"))
        suggestion = _clean(raw_item.get("suggestion")) or None

        if dimension not in VALID_DIMENSIONS or polarity not in VALID_POLARITIES:
            continue
        if not quote or not reason:
            continue
        if quote in {"无", "暂无", "没有", "未提到"}:
            continue
        if len(quote) > MAX_QUOTE_LENGTH:
            continue
        if quote not in answer_text:
            continue
        if _contains_private_text(quote):
            continue
        if polarity == "strength":
            suggestion = None
        validated.append(
            {
                "dimension": dimension,
                "polarity": polarity,
                "quote": quote,
                "reason": reason,
                "suggestion": suggestion,
            }
        )

    return [AnswerEvidenceItem.model_validate(item).model_dump() for item in validated]


def analyze_expression_quality(
    answer_text: str,
    recording_duration_seconds: float | None = None,
) -> dict[str, Any]:
    normalized = answer_text.strip()
    character_count = _effective_character_count(normalized)
    sentence_count = _sentence_count(normalized)
    average_sentence_length = (
        round(character_count / sentence_count, 2) if sentence_count > 0 else None
    )
    filler_word_count = _count_terms(normalized, FILLER_WORDS)
    filler_word_rate = round(filler_word_count / character_count, 4) if character_count else 0
    structure_signal_count = _count_terms(normalized, STRUCTURE_SIGNALS)
    estimated_speech_rate = None
    speech_rate_unit = None
    speech_rate_status = "不可用"
    speech_rate_note = "未提供有效录音时长，无法估算语速。"

    if recording_duration_seconds and recording_duration_seconds > 0 and character_count > 0:
        estimated_speech_rate = round(character_count / (recording_duration_seconds / 60), 2)
        speech_rate_unit = "字词/分钟"
        speech_rate_status = _speech_rate_status(estimated_speech_rate)
        speech_rate_note = "仅基于转写文本与录音时长估算，不代表真实语音质量。"

    return {
        "character_count": character_count,
        "sentence_count": sentence_count,
        "average_sentence_length": average_sentence_length,
        "filler_word_count": filler_word_count,
        "filler_word_rate": filler_word_rate,
        "repetition_hint": _repetition_hint(normalized),
        "structure_signal_count": structure_signal_count,
        "estimated_speech_rate": estimated_speech_rate,
        "speech_rate_unit": speech_rate_unit,
        "speech_rate_status": speech_rate_status,
        "speech_rate_note": speech_rate_note,
    }


def _clean(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _contains_private_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in PRIVATE_PATTERNS)


def _effective_character_count(text: str) -> int:
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = re.findall(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*", text)
    return cjk_count + len(words)


def _sentence_count(text: str) -> int:
    parts = [item.strip() for item in re.split(r"[。！？!?；;\n]+", text) if item.strip()]
    return max(1, len(parts)) if text.strip() else 0


def _count_terms(text: str, terms: tuple[str, ...]) -> int:
    return sum(text.count(term) for term in terms)


def _repetition_hint(text: str) -> str | None:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9]+", text.lower())
    if len(tokens) < 4:
        return None
    repeated = sorted({token for token in tokens if tokens.count(token) >= 3})
    if not repeated:
        return None
    preview = "、".join(repeated[:4])
    return f"存在重复表达：{preview}"


def _speech_rate_status(rate: float) -> str:
    if rate < 120:
        return "偏慢"
    if rate > 260:
        return "偏快"
    return "适中"
