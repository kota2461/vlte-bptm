"""Deterministic v0.1 baseline for Semantic Packet extraction."""

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .semantic_packet import (
    IntentCandidate,
    SemanticPacket,
    parse_semantic_packet,
    request_digest,
)


@dataclass(frozen=True)
class Marker:
    signal: str
    pattern: re.Pattern[str]


def _compile(*phrases: str) -> re.Pattern[str]:
    patterns = []
    for phrase in phrases:
        escaped = re.escape(phrase)
        if re.fullmatch(r"[A-Za-z0-9 _-]+", phrase):
            escaped = rf"(?<![A-Za-z]){escaped}(?![A-Za-z])"
        patterns.append(escaped)
    return re.compile("|".join(patterns), re.I)


INTENT_PRIORITY = {
    "clarify": 7,
    "summarize": 6,
    "verify": 5,
    "build": 4,
    "explore": 3,
    "explain": 2,
    "respond": 1,
}


INTENT_MARKERS: Dict[str, Tuple[Marker, ...]] = {
    "clarify": (
        Marker(
            "missing_information",
            _compile(
                "まだ伝えていません",
                "まだ決めていません",
                "情報がありません",
                "不足しています",
                "先に質問",
                "聞いてください",
                "not provided",
                "not shared",
                "not been shared",
                "not stated",
                "information is missing",
                "ask me",
                "ask first",
                "before answering",
                "before giving",
                "まだ伝わっていません",
                "分かりません",
            ),
        ),
    ),
    "summarize": (
        Marker(
            "summary_request",
            _compile(
                "要約",
                "まとめて",
                "要点",
                "短くまとめ",
                "summarize",
                "summary",
                "recap",
                "condense",
                "boil",
                "key points",
            ),
        ),
    ),
    "verify": (
        Marker(
            "verification_request",
            _compile(
                "確認して",
                "確認してください",
                "確認し",
                "確認する",
                "検証して",
                "検証し",
                "確かめ",
                "検算",
                "正しいか",
                "正しければ",
                "一致するか",
                "合ってい",
                "妥当か",
                "見てもらって",
                "見てほしい",
                "レビュー",
                "チェックして",
                "check",
                "review",
                "verify",
                "validate",
                "confirm",
                "make sure",
                "double-check",
                "matches",
                "accurate",
                "plausible",
            ),
        ),
    ),
    "build": (
        Marker(
            "implementation_request",
            _compile(
                "手順",
                "作業計画",
                "実装計画",
                "順番",
                "タスク",
                "段階",
                "導入計画",
                "step-by-step",
                "implementation plan",
                "work plan",
                "task list",
                "ordered tasks",
                "rollout plan",
                "break down",
                "build plan",
                # deliverable verbs (a build request names something to make)
                "作っ",
                "作成",
                "用意",
                "ドラフト",
                "段取り",
                "組ん",
                "組み立て",
                "チェックリスト",
                "draft",
                "produce",
                "prepare",
                "checklist",
            ),
        ),
    ),
    "explore": (
        Marker(
            "exploration_request",
            _compile(
                "複数の案",
                "選択肢",
                "候補を",
                "いくつかの方法",
                "別の方法",
                "比較して",
                "比べて",
                "挙げて比べ",
                "alternatives",
                "different approaches",
                "several options",
                "brainstorm",
                "other ways",
                "compare options",
                "possible strategies",
            ),
        ),
    ),
    "explain": (
        Marker(
            "explanation_request",
            _compile(
                "説明して",
                "説明してください",
                "なぜ",
                "理由",
                "仕組み",
                "どのように機能",
                "どうして",
                "どういう仕組み",
                "どういう理由",
                "explain",
                "why",
                "how does",
                "how it works",
                "reason",
                "describe how",
                "walk me through",
                "what makes",
                "help me understand",
                # indirect explanation ("I can do it but don't grasp WHY")
                "なんで",
                "ピンとこない",
                "ピンと来ない",
                "腑に落ち",
                "しっくりこない",
                "しっくり来ない",
                "実感がわかない",
                "実感が湧かない",
                "腹落ち",
                "don't get",
                "don't really get",
                "never really got",
                "can't see why",
            ),
        ),
    ),
    "respond": (
        Marker(
            "direct_response_request",
            _compile(
                "とは何",
                "何ですか",
                "教えて",
                "答えて",
                "挙げて",
                "what is",
                "what does",
                "who is",
                "name the",
                "tell me",
                "which",
            ),
        ),
        Marker(
            "conversation_response",
            _compile(
                "こんにちは",
                "こんばんは",
                "おはよう",
                "ありがとう",
                "助かりました",
                "不安",
                "心配",
                "落ち込",
                "困っています",
                "つらい",
                "hello",
                "good morning",
                "good evening",
                "thank you",
                "thanks",
                "appreciate",
                "anxious",
                "worried",
                "feeling stuck",
            ),
        ),
    ),
}

CURRENT_MARKER = Marker(
    "current_information",
    _compile(
        "最新",
        "現在の",
        "現在は",
        "今日の",
        "今日時点",
        "本日時点",
        "今の",
        "現時点",
        "latest",
        "current",
        "today",
        "right now",
        "as of",
    ),
)
UNVERIFIED_MARKER = Marker(
    "unverified_claim",
    _compile(
        "主張",
        "提示された",
        "報告された",
        "合計",
        "料金",
        "claimed",
        "proposed",
        "figures",
        "reported",
        "totals",
        "conclusion",
    ),
)
SHORT_MARKER = Marker(
    "short_response",
    _compile(
        "短く",
        "簡潔",
        "一文",
        "3行",
        "brief",
        "briefly",
        "concise",
        "one sentence",
        "three lines",
    ),
)
LONG_MARKER = Marker(
    "long_response",
    _compile(
        "詳しく",
        "詳細に",
        "網羅的",
        "丁寧に",
        "in detail",
        "detailed",
        "comprehensive",
        "thorough",
    ),
)
FORMAT_MARKERS = {
    "bullets": Marker(
        "format_bullets",
        _compile("箇条書き", "bullet points", "bullets"),
    ),
    "json": Marker(
        "format_json",
        _compile("JSONで", "JSON形式", "as JSON", "json object"),
    ),
    "table": Marker("format_table", _compile("表形式", "table")),
    "code": Marker(
        "format_code",
        _compile("コードで", "code block", "code sample"),
    ),
}
MUST_MARKERS = {
    "cite_sources": Marker(
        "constraint_cite_sources",
        _compile("出典付き", "出典を", "根拠を示", "cite sources", "with sources"),
    ),
    "ask_first": Marker(
        "constraint_ask_first",
        _compile(
            "先に質問",
            "ask first",
            "before answering",
            "before giving",
        ),
    ),
}
MUST_NOT_MARKERS = {
    "no_code": Marker(
        "constraint_no_code",
        _compile("コードは不要", "without code", "no code"),
    ),
    "no_web_search": Marker(
        "constraint_no_web_search",
        _compile("検索せず", "without web search", "do not search"),
    ),
    "no_table": Marker(
        "constraint_no_table",
        _compile("表を使わず", "without using a table", "no table"),
    ),
}
MULTIPLE_INTENT_MARKER = Marker(
    "multiple_intents",
    _compile(
        "その上で",
        "そのうえで",
        "その後で",
        "その後に",
        "挙げてから",
        "続けて",
        "and then",
        "then briefly",
        "then explain",
        "and point out",
        "and also",
    ),
)
RISK_MARKERS = {
    "critical": (
        Marker(
            "emergency_risk",
            _compile(
                "緊急",
                "命に関わる",
                "emergency",
                "life-threatening",
            ),
        ),
    ),
    "high": (
        Marker(
            "medical_risk",
            _compile("医療", "症状", "薬", "medical", "symptom", "medication"),
        ),
        Marker(
            "legal_risk",
            _compile("法律", "法的", "契約違反", "legal", "lawsuit"),
        ),
        Marker(
            "financial_risk",
            _compile("投資", "融資", "税金", "investment", "loan", "tax"),
        ),
        Marker(
            "security_risk",
            _compile(
                "脆弱性",
                "認証情報",
                "security vulnerability",
                "credentials",
            ),
        ),
    ),
}


def _find_markers(
    text: str,
    markers: Iterable[Marker],
) -> List[Tuple[str, int, int]]:
    found = []
    for marker in markers:
        match = marker.pattern.search(text)
        if match:
            found.append((marker.signal, match.start(), match.end()))
    return found


def _language(text: str) -> str:
    has_ja = re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text) is not None
    has_en = re.search(r"[A-Za-z]", text) is not None
    if has_ja and has_en:
        return "mixed"
    if has_ja:
        return "ja"
    if has_en:
        return "en"
    return "und"


def _intent_scores(text: str) -> Tuple[List[IntentCandidate], List[Tuple[str, int, int]]]:
    scores: Dict[str, float] = {}
    evidence: List[Tuple[str, int, int]] = []
    for intent, markers in INTENT_MARKERS.items():
        matches = _find_markers(text, markers)
        if matches:
            scores[intent] = min(
                0.98,
                0.78
                + 0.01 * INTENT_PRIORITY[intent]
                + 0.03 * (len(matches) - 1),
            )
            evidence.extend(matches)
    if "build" in scores and "verify" in scores:
        # A request that names a build deliverable AND a verify signal is a
        # verify-then-build sequence: the deliverable (build) is primary and
        # verification is its prerequisite. This holds whether or not an
        # explicit sequencing connective ("その上で"/"and then") is present —
        # relying on a connective dropped the verification gate and produced
        # critical under-processing (build without its verify step).
        scores["build"] = min(0.98, max(scores["build"], scores["verify"] + 0.01))
    if not scores:
        # No marker fired. This is a plain response/explanation, not genuine
        # ambiguity — default to a confident direct response (economy) rather
        # than abstaining to clarify. Real missing-information is detected
        # separately via the clarify markers / information_state, which still
        # routes to clarify. (Pre-fix this was 0.45, which tripped the
        # low-confidence → clarify path and over-abstained on conversational
        # and indirect inputs.)
        scores["respond"] = 0.62
    candidates = [
        IntentCandidate(intent=intent, confidence=score)
        for intent, score in sorted(
            scores.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    return candidates, evidence


# v0.3 hybrid: minimum learned-layer confidence margin (top1-top2) required
# to override the marker no-match fallback. Conservative / precision-first —
# markers always win when they fire; the learned layer only replaces the
# plain `respond` fallback, and only when clearly confident. Chosen a-priori
# (not tuned on the campaign); see docs/SEMANTIC_ADAPTER_v0_3_design.md §11.
# 2026-06-18: raised 0.15 -> 0.20 after margin-gate calibration against
# harvested-drop negatives (build/intent_gate_calibration_v1.json); junk-abstain
# ~doubled with only a small coverage cost. Sealed campaign not used for tuning.
INTENT_GATE_MARGIN = 0.20


def extract_semantic_packet(
    text: str,
    intent_model=None,
    *,
    trace: Optional[Dict] = None,
) -> SemanticPacket:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("semantic extraction requires non-empty text")

    candidates, evidence = _intent_scores(text)
    primary = candidates[0].intent
    # OBSERVABILITY (v0.3.1): `trace` is an optional out-param that records WHY
    # the intent was decided. It NEVER affects the decision — the routing path
    # below is byte-identical whether trace is None or a dict.
    decided_by = "markers" if evidence else "fallback"
    # Hybrid merge: on marker no-match (empty evidence → the respond
    # fallback), defer to the learned intent model only when its margin
    # clears the gate. Safety markers (verify prerequisite, missing-info →
    # clarify) are handled below and stay deterministic regardless.
    if intent_model is not None and not evidence:
        prediction = intent_model.predict(text)
        if trace is not None:
            trace["intent_margin"] = round(prediction.margin, 6)
            trace["intent_top_scores"] = [
                [k, round(v, 4)]
                for k, v in sorted(prediction.scores.items(),
                                   key=lambda kv: -kv[1])[:3]
            ]
        if prediction.margin >= INTENT_GATE_MARGIN:
            primary = prediction.intent
            decided_by = "learned"
            candidates = [
                IntentCandidate(
                    intent=primary,
                    confidence=candidates[0].confidence,
                )
            ]
    if trace is not None:
        trace["decided_by"] = decided_by
        trace["markers_fired"] = bool(evidence)
        trace["gate_margin"] = INTENT_GATE_MARGIN
    missing_matches = _find_markers(text, INTENT_MARKERS["clarify"])
    current_matches = _find_markers(text, (CURRENT_MARKER,))
    unverified_matches = _find_markers(text, (UNVERIFIED_MARKER,))
    multiple_matches = _find_markers(text, (MULTIPLE_INTENT_MARKER,))
    verify_matches = _find_markers(text, INTENT_MARKERS["verify"])
    short_matches = _find_markers(text, (SHORT_MARKER,))
    long_matches = _find_markers(text, (LONG_MARKER,))

    operations = [primary]
    if primary == "build" and verify_matches:
        # Keep verification as a prerequisite operation whenever a build
        # deliverable co-occurs with a verify signal, with or without an
        # explicit connective. This is what makes the plan verified/vertical
        # instead of silently dropping to standard/horizontal.
        operations.append("verify")
    if current_matches:
        operations.append("search")
    if re.search(r"計算して|計算し|を計算|計算結果|合計|calculate|total|add up", text, re.I):
        operations.append("calculate")
    elif re.search(r"\d+\s*[+\-*/×÷]\s*\d+", text):
        # an explicit arithmetic expression is itself a calculate signal,
        # regardless of the verb (e.g. "この計算が合っているか: 12 + 7 = 20").
        # Precise: requires digits AROUND an operator, so prose like
        # 「計算はできる」(no arithmetic) does not trip it.
        operations.append("calculate")
    if re.search(r"比較|compare|trade-?offs?", text, re.I):
        operations.append("compare")

    formats = []
    for format_name, marker in FORMAT_MARKERS.items():
        matches = _find_markers(text, (marker,))
        if matches:
            formats.append(format_name)
            evidence.extend(matches)
    must = []
    for constraint, marker in MUST_MARKERS.items():
        matches = _find_markers(text, (marker,))
        if matches:
            must.append(constraint)
            evidence.extend(matches)
    must_not = []
    for constraint, marker in MUST_NOT_MARKERS.items():
        matches = _find_markers(text, (marker,))
        if matches:
            must_not.append(constraint)
            evidence.extend(matches)

    risk_level = "low"
    risk_flags = []
    for level in ("critical", "high"):
        for marker in RISK_MARKERS[level]:
            matches = _find_markers(text, (marker,))
            if matches:
                risk_level = level
                risk_flags.append(marker.signal.removesuffix("_risk"))
                evidence.extend(matches)
        if risk_flags:
            break
    if risk_level == "low" and current_matches:
        risk_level = "medium"
    if (
        risk_level == "low"
        and unverified_matches
        and "cite_sources" in must
    ):
        risk_level = "medium"
    if current_matches:
        risk_flags.append("current_information")
        evidence.extend(current_matches)
    if unverified_matches:
        evidence.extend(unverified_matches)
        if risk_level != "low":
            risk_flags.append("unverified_claim")

    if short_matches:
        response_length = "short"
        evidence.extend(short_matches)
    elif long_matches:
        response_length = "long"
        evidence.extend(long_matches)
    else:
        response_length = "unspecified"

    evidence = sorted(set(evidence), key=lambda item: (item[1], item[2], item[0]))
    confidence = candidates[0].confidence
    unknowns = [] if confidence >= 0.60 else ["primary_intent"]
    conflicts = []
    if len(candidates) > 1 and candidates[0].confidence == candidates[1].confidence:
        conflicts.append("primary_intent")

    return parse_semantic_packet(
        {
            "schema_version": "semantic-packet.v1",
            "request_digest": request_digest(text),
            "adapter": {
                "kind": "deterministic_signal_extractor",
                "version": "0.2",
            },
            "language": _language(text),
            "intent_candidates": [
                candidate.as_dict() for candidate in candidates
            ],
            "operations": list(dict.fromkeys(operations)),
            "information_state": {
                "missing_required_information": bool(missing_matches),
                "contains_unverified_claims": bool(unverified_matches),
                "requires_current_information": bool(current_matches),
                "multiple_intents": bool(multiple_matches),
            },
            "constraints": {
                "response_length": response_length,
                "formats": formats,
                "must": must,
                "must_not": must_not,
            },
            "risk": {
                "level": risk_level,
                "flags": list(dict.fromkeys(risk_flags)),
            },
            "evidence": [
                {"signal": signal, "start": start, "end": end}
                for signal, start, end in evidence
            ],
            "unknowns": unknowns,
            "conflicts": conflicts,
            "confidence": confidence,
        }
    )
