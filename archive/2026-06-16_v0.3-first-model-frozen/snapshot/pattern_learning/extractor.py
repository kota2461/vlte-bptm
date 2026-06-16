import re
from typing import Iterable, List

from thought_core import process

from .models import OPERATORS, PatternDraft, SourceDocument


SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？!?])|[\r\n]+")

OPERATOR_MARKERS = {
    "definition": ("とは", "である", "をいう", "means", "defined as"),
    "equivalence": ("同じ", "等しい", "同値", "equivalent", "equals"),
    "comparison": ("一方", "より", "対して", "比較", "whereas", "than"),
    "condition": ("場合", "なら", "とき", "条件", "if ", "when "),
    "causal_relation": ("ため", "ので", "結果", "原因", "because", "therefore"),
    "sequence": ("まず", "次に", "その後", "手順", "first", "then"),
    "decomposition": ("分け", "分類", "構成", "要素", "consists", "divided"),
    "uncertainty": ("可能性", "推定", "おそらく", "不明", "may ", "likely"),
    "calculation": ("計算", "方程式", "加算", "確率", "equation", "calculate"),
    "verification": ("検証", "証明", "確認", "根拠", "verify", "proof"),
}


def _sentences(text: str) -> Iterable[str]:
    for raw in SENTENCE_BOUNDARY.split(text):
        sentence = re.sub(r"\s+", " ", raw).strip()
        if 12 <= len(sentence) <= 600:
            yield sentence


def _operators(sentence: str) -> List[str]:
    folded = sentence.casefold()
    matches = [
        name
        for name, markers in OPERATOR_MARKERS.items()
        if any(marker in folded for marker in markers)
    ]
    return [name for name in OPERATORS if name in matches] or ["definition"]


def _route(sentence: str) -> str:
    mode = process(sentence).llm_order["mode"]
    return mode if mode in {
        "respond",
        "clarify",
        "build",
        "verify",
        "summarize",
        "explore",
    } else "respond"


def extract_patterns(
    document: SourceDocument,
    limit: int = 20,
) -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    seen = set()
    for sentence in _sentences(document.text):
        normalized = sentence.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)

        operators = _operators(sentence)
        route = _route(sentence)
        confidence = min(
            0.92,
            0.42 + 0.07 * len(operators) + (0.08 if route != "respond" else 0),
        )
        drafts.append(
            PatternDraft(
                input_text=sentence,
                suggested_route=route,
                suggested_operators=operators,
                thought_form={
                    "facts": [sentence],
                    "goals": [],
                    "constraints": [],
                    "uncertainty": (
                        ["source statement requires human verification"]
                        if "uncertainty" in operators
                        else []
                    ),
                    "operation": operators[0],
                    "candidates": [],
                },
                confidence=confidence,
            )
        )
        if len(drafts) >= limit:
            break
    return drafts
