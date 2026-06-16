from typing import Iterable

from .bits import ThoughtBit
from .state import ThoughtState


IDEA_KEYWORDS = (
    "アイデア",
    "発想",
    "考えました",
    "思いついた",
    "モデル",
    "仕組み",
    "architecture",
    "idea",
    "model",
)

BUILD_KEYWORDS = (
    "実装",
    "コード",
    "作って",
    "作りたい",
    "ファイル",
    "構成",
    "設計",
    "手順",
    "prototype",
    "implement",
    "build",
    "code",
)

VERIFY_KEYWORDS = (
    "検証",
    "正しい",
    "問題",
    "欠点",
    "リスク",
    "レビュー",
    "verify",
    "review",
    "risk",
)

SUMMARY_KEYWORDS = (
    "要約",
    "まとめ",
    "短く",
    "summarize",
    "summary",
)

EMPATHY_KEYWORDS = (
    "つらい",
    "不安",
    "怖い",
    "嬉しい",
    "悲しい",
    "悩んで",
)

UNCERTAINTY_KEYWORDS = (
    "たぶん",
    "かも",
    "不明",
    "わからない",
    "曖昧",
    "maybe",
    "unclear",
    "unknown",
)


def _contains(text: str, keywords: Iterable[str]) -> bool:
    folded = text.casefold()
    return any(keyword.casefold() in folded for keyword in keywords)


def encode_initial_bits(user_input: str) -> ThoughtState:
    state = ThoughtState()
    stripped = user_input.strip()

    if not stripped:
        state.set(ThoughtBit.INSUFFICIENT_INFO, 1.0, "empty_input")
        state.set(ThoughtBit.ASK_QUESTION, 0.9, "empty_input")
        state.set(ThoughtBit.SHORT_REPLY, 0.8, "empty_input")
        return state

    state.set(ThoughtBit.INPUT_DETECTED, 1.0, "base_input")
    state.set(ThoughtBit.USER_INTENT_DETECTED, 0.7, "base_input")
    state.set(ThoughtBit.REPLY_NOW, 0.8, "base_input")
    state.set(ThoughtBit.ANSWER_POSSIBLE, 0.65, "base_input")

    if _contains(stripped, IDEA_KEYWORDS):
        for flag, strength in (
            (ThoughtBit.INTEREST, 0.8),
            (ThoughtBit.CURIOSITY, 0.85),
            (ThoughtBit.NOVELTY_DRIVE, 0.8),
            (ThoughtBit.EXPLORATION_DRIVE, 0.8),
            (ThoughtBit.NOVELTY_DETECTED, 0.8),
            (ThoughtBit.NEED_REASONING, 0.8),
            (ThoughtBit.PROPOSE, 0.75),
            (ThoughtBit.CREATIVE_REPLY, 0.7),
            (ThoughtBit.EXPLAIN, 0.7),
        ):
            state.set(flag, strength, "idea_rule")

    if _contains(stripped, BUILD_KEYWORDS):
        for flag, strength in (
            (ThoughtBit.NEED_DECOMPOSE, 0.8),
            (ThoughtBit.PRECISION_DRIVE, 0.75),
            (ThoughtBit.PLAN, 0.8),
            (ThoughtBit.LONG_REPLY, 0.65),
        ):
            state.set(flag, strength, "build_rule")

    if _contains(stripped, VERIFY_KEYWORDS):
        for flag, strength in (
            (ThoughtBit.CAUTION, 0.7),
            (ThoughtBit.NEED_VERIFY, 0.8),
            (ThoughtBit.NEED_COMPARE, 0.65),
            (ThoughtBit.CRITIQUE, 0.7),
            (ThoughtBit.PRECISION_DRIVE, 0.75),
        ):
            state.set(flag, strength, "verify_rule")

    if _contains(stripped, SUMMARY_KEYWORDS):
        state.set(ThoughtBit.COMPRESSION_DRIVE, 0.8, "summary_rule")
        state.set(ThoughtBit.SUMMARIZE, 0.85, "summary_rule")
        state.set(ThoughtBit.SHORT_REPLY, 0.7, "summary_rule")

    if _contains(stripped, EMPATHY_KEYWORDS):
        state.set(ThoughtBit.USER_EMOTION_DETECTED, 0.8, "empathy_rule")
        state.set(ThoughtBit.EMPATHY, 0.75, "empathy_rule")
        state.set(ThoughtBit.WARMTH, 0.7, "empathy_rule")
        state.set(ThoughtBit.RELATION_DRIVE, 0.7, "empathy_rule")

    if _contains(stripped, UNCERTAINTY_KEYWORDS):
        state.set(ThoughtBit.UNCERTAINTY, 0.7, "uncertainty_rule")
        state.set(ThoughtBit.CAUTION, 0.65, "uncertainty_rule")
        state.set(ThoughtBit.NEED_VERIFY, 0.75, "uncertainty_rule")

    if "?" in stripped or "？" in stripped:
        state.set(ThoughtBit.NEED_REASONING, 0.7, "question_rule")
        state.set(ThoughtBit.EXPLAIN, 0.7, "question_rule")

    return state
