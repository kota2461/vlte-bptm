"""Strict semantic-packet.v1 contract.

The packet contains only compact routing signals. It deliberately excludes
the raw prompt and any generated answer text.
"""

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple


SEMANTIC_PACKET_SCHEMA_VERSION = "semantic-packet.v1"

INTENTS = (
    "respond",
    "explain",
    "clarify",
    "build",
    "verify",
    "summarize",
    "explore",
)
OPERATIONS = (
    "respond",
    "explain",
    "clarify",
    "build",
    "verify",
    "summarize",
    "explore",
    "search",
    "calculate",
    "compare",
)
LANGUAGES = ("ja", "en", "mixed", "und")
RESPONSE_LENGTHS = ("unspecified", "short", "medium", "long")
RISK_LEVELS = ("low", "medium", "high", "critical")
ADAPTER_KINDS = (
    "pattern_model",
    "llm_semantic_adapter",
    "legacy_pattern_router",
    "deterministic_signal_extractor",
)

_DIGEST_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def request_digest(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("request text must be a string")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strict_object(
    value: Any,
    field: str,
    required_fields: Tuple[str, ...],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    actual = set(value)
    required = set(required_fields)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing:
        raise ValueError(f"{field} is missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"{field} has unknown field: {unknown[0]}")
    return value


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _identifier(value: Any, field: str) -> str:
    text = _non_empty_string(value, field)
    if _IDENTIFIER_PATTERN.fullmatch(text) is None:
        raise ValueError(f"{field} must be a machine identifier")
    return text


def _confidence(value: Any, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not 0.0 <= value <= 1.0
    ):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return float(value)


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _identifier_list(
    value: Any,
    field: str,
    *,
    allowed: Tuple[str, ...] | None = None,
) -> Tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    items = tuple(_identifier(item, field) for item in value)
    if len(set(items)) != len(items):
        raise ValueError(f"{field} must contain unique values")
    if allowed is not None:
        unknown = sorted(set(items) - set(allowed))
        if unknown:
            raise ValueError(f"{field} contains unknown value: {unknown[0]}")
    return items


@dataclass(frozen=True)
class AdapterInfo:
    kind: str
    version: str

    def as_dict(self) -> Dict[str, str]:
        return {"kind": self.kind, "version": self.version}


@dataclass(frozen=True)
class IntentCandidate:
    intent: str
    confidence: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class InformationState:
    missing_required_information: bool
    contains_unverified_claims: bool
    requires_current_information: bool
    multiple_intents: bool

    def as_dict(self) -> Dict[str, bool]:
        return {
            "missing_required_information": (
                self.missing_required_information
            ),
            "contains_unverified_claims": self.contains_unverified_claims,
            "requires_current_information": (
                self.requires_current_information
            ),
            "multiple_intents": self.multiple_intents,
        }


@dataclass(frozen=True)
class SemanticConstraints:
    response_length: str
    formats: Tuple[str, ...]
    must: Tuple[str, ...]
    must_not: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "response_length": self.response_length,
            "formats": list(self.formats),
            "must": list(self.must),
            "must_not": list(self.must_not),
        }


@dataclass(frozen=True)
class RiskSignal:
    level: str
    flags: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "flags": list(self.flags)}


@dataclass(frozen=True)
class EvidenceSpan:
    signal: str
    start: int
    end: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "signal": self.signal,
            "start": self.start,
            "end": self.end,
        }


@dataclass(frozen=True)
class SemanticPacket:
    request_digest: str
    adapter: AdapterInfo
    language: str
    intent_candidates: Tuple[IntentCandidate, ...]
    operations: Tuple[str, ...]
    information_state: InformationState
    constraints: SemanticConstraints
    risk: RiskSignal
    evidence: Tuple[EvidenceSpan, ...]
    unknowns: Tuple[str, ...]
    conflicts: Tuple[str, ...]
    confidence: float

    @property
    def primary_intent(self) -> str:
        return self.intent_candidates[0].intent

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SEMANTIC_PACKET_SCHEMA_VERSION,
            "request_digest": self.request_digest,
            "adapter": self.adapter.as_dict(),
            "language": self.language,
            "intent_candidates": [
                candidate.as_dict()
                for candidate in self.intent_candidates
            ],
            "operations": list(self.operations),
            "information_state": self.information_state.as_dict(),
            "constraints": self.constraints.as_dict(),
            "risk": self.risk.as_dict(),
            "evidence": [span.as_dict() for span in self.evidence],
            "unknowns": list(self.unknowns),
            "conflicts": list(self.conflicts),
            "confidence": self.confidence,
        }


def _parse_adapter(value: Any) -> AdapterInfo:
    payload = _strict_object(value, "adapter", ("kind", "version"))
    kind = payload["kind"]
    if kind not in ADAPTER_KINDS:
        raise ValueError(f"unknown adapter kind: {kind}")
    return AdapterInfo(
        kind=kind,
        version=_non_empty_string(payload["version"], "adapter.version"),
    )


def _parse_intents(value: Any) -> Tuple[IntentCandidate, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("intent_candidates must be a non-empty array")
    candidates = []
    for index, item in enumerate(value):
        payload = _strict_object(
            item,
            f"intent_candidates[{index}]",
            ("intent", "confidence"),
        )
        intent = payload["intent"]
        if intent not in INTENTS:
            raise ValueError(f"unknown intent: {intent}")
        candidates.append(
            IntentCandidate(
                intent=intent,
                confidence=_confidence(
                    payload["confidence"],
                    f"intent_candidates[{index}].confidence",
                ),
            )
        )
    if len({candidate.intent for candidate in candidates}) != len(candidates):
        raise ValueError("intent_candidates must contain unique intents")
    confidences = [candidate.confidence for candidate in candidates]
    if confidences != sorted(confidences, reverse=True):
        raise ValueError(
            "intent_candidates must be ordered by descending confidence"
        )
    return tuple(candidates)


def _parse_information_state(value: Any) -> InformationState:
    fields = (
        "missing_required_information",
        "contains_unverified_claims",
        "requires_current_information",
        "multiple_intents",
    )
    payload = _strict_object(value, "information_state", fields)
    return InformationState(
        missing_required_information=_boolean(
            payload["missing_required_information"],
            "information_state.missing_required_information",
        ),
        contains_unverified_claims=_boolean(
            payload["contains_unverified_claims"],
            "information_state.contains_unverified_claims",
        ),
        requires_current_information=_boolean(
            payload["requires_current_information"],
            "information_state.requires_current_information",
        ),
        multiple_intents=_boolean(
            payload["multiple_intents"],
            "information_state.multiple_intents",
        ),
    )


def _parse_constraints(value: Any) -> SemanticConstraints:
    payload = _strict_object(
        value,
        "constraints",
        ("response_length", "formats", "must", "must_not"),
    )
    response_length = payload["response_length"]
    if response_length not in RESPONSE_LENGTHS:
        raise ValueError(f"unknown response length: {response_length}")
    formats = _identifier_list(payload["formats"], "constraints.formats")
    must = _identifier_list(payload["must"], "constraints.must")
    must_not = _identifier_list(
        payload["must_not"],
        "constraints.must_not",
    )
    overlap = sorted(set(must) & set(must_not))
    if overlap:
        raise ValueError(
            f"constraint cannot be both must and must_not: {overlap[0]}"
        )
    return SemanticConstraints(
        response_length=response_length,
        formats=formats,
        must=must,
        must_not=must_not,
    )


def _parse_risk(value: Any) -> RiskSignal:
    payload = _strict_object(value, "risk", ("level", "flags"))
    level = payload["level"]
    if level not in RISK_LEVELS:
        raise ValueError(f"unknown risk level: {level}")
    return RiskSignal(
        level=level,
        flags=_identifier_list(payload["flags"], "risk.flags"),
    )


def _parse_evidence(value: Any) -> Tuple[EvidenceSpan, ...]:
    if not isinstance(value, list):
        raise ValueError("evidence must be an array")
    spans = []
    for index, item in enumerate(value):
        payload = _strict_object(
            item,
            f"evidence[{index}]",
            ("signal", "start", "end"),
        )
        start = payload["start"]
        end = payload["end"]
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
        ):
            raise ValueError(
                f"evidence[{index}] must have integer 0 <= start < end"
            )
        spans.append(
            EvidenceSpan(
                signal=_identifier(
                    payload["signal"],
                    f"evidence[{index}].signal",
                ),
                start=start,
                end=end,
            )
        )
    ordering = [(span.start, span.end, span.signal) for span in spans]
    if ordering != sorted(ordering):
        raise ValueError("evidence must be ordered by source position")
    if len(set(ordering)) != len(ordering):
        raise ValueError("evidence spans must be unique")
    return tuple(spans)


def parse_semantic_packet(value: Any) -> SemanticPacket:
    fields = (
        "schema_version",
        "request_digest",
        "adapter",
        "language",
        "intent_candidates",
        "operations",
        "information_state",
        "constraints",
        "risk",
        "evidence",
        "unknowns",
        "conflicts",
        "confidence",
    )
    payload = _strict_object(value, "semantic packet", fields)
    if payload["schema_version"] != SEMANTIC_PACKET_SCHEMA_VERSION:
        raise ValueError("unsupported semantic packet schema")

    digest = payload["request_digest"]
    if not isinstance(digest, str) or _DIGEST_PATTERN.fullmatch(digest) is None:
        raise ValueError("request_digest must be a SHA-256 hex digest")
    language = payload["language"]
    if language not in LANGUAGES:
        raise ValueError(f"unknown language: {language}")

    return SemanticPacket(
        request_digest=digest.lower(),
        adapter=_parse_adapter(payload["adapter"]),
        language=language,
        intent_candidates=_parse_intents(payload["intent_candidates"]),
        operations=_identifier_list(
            payload["operations"],
            "operations",
            allowed=OPERATIONS,
        ),
        information_state=_parse_information_state(
            payload["information_state"]
        ),
        constraints=_parse_constraints(payload["constraints"]),
        risk=_parse_risk(payload["risk"]),
        evidence=_parse_evidence(payload["evidence"]),
        unknowns=_identifier_list(payload["unknowns"], "unknowns"),
        conflicts=_identifier_list(payload["conflicts"], "conflicts"),
        confidence=_confidence(payload["confidence"], "confidence"),
    )
