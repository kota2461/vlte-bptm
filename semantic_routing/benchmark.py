"""Strict Pattern Language Model benchmark contract."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from .semantic_packet import (
    INTENTS,
    LANGUAGES,
    OPERATIONS,
    RESPONSE_LENGTHS,
    RISK_LEVELS,
)


PLM_BENCHMARK_SCHEMA_VERSION = "pattern-language-benchmark.v1"
PLM_BENCHMARK_SPLITS = ("train", "validation", "sealed")
PLM_BENCHMARK_REVIEW_STATUSES = ("draft", "human_reviewed")


def _strict_object(
    value: Any,
    field: str,
    required_fields: Sequence[str],
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


def _string_list(
    value: Any,
    field: str,
    *,
    allowed: Sequence[str] | None = None,
) -> Tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    items = tuple(_non_empty_string(item, field) for item in value)
    if len(set(items)) != len(items):
        raise ValueError(f"{field} must contain unique strings")
    if allowed is not None:
        unknown = sorted(set(items) - set(allowed))
        if unknown:
            raise ValueError(f"{field} contains unknown value: {unknown[0]}")
    return items


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


@dataclass(frozen=True)
class BenchmarkEvidence:
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
class ExpectedSemantics:
    primary_intent: str
    operations: Tuple[str, ...]
    missing_required_information: bool
    contains_unverified_claims: bool
    requires_current_information: bool
    multiple_intents: bool
    response_length: str
    formats: Tuple[str, ...]
    must: Tuple[str, ...]
    must_not: Tuple[str, ...]
    risk_level: str
    risk_flags: Tuple[str, ...]
    evidence: Tuple[BenchmarkEvidence, ...]
    unknowns: Tuple[str, ...]
    conflicts: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "primary_intent": self.primary_intent,
            "operations": list(self.operations),
            "information_state": {
                "missing_required_information": (
                    self.missing_required_information
                ),
                "contains_unverified_claims": (
                    self.contains_unverified_claims
                ),
                "requires_current_information": (
                    self.requires_current_information
                ),
                "multiple_intents": self.multiple_intents,
            },
            "constraints": {
                "response_length": self.response_length,
                "formats": list(self.formats),
                "must": list(self.must),
                "must_not": list(self.must_not),
            },
            "risk": {
                "level": self.risk_level,
                "flags": list(self.risk_flags),
            },
            "evidence": [item.as_dict() for item in self.evidence],
            "unknowns": list(self.unknowns),
            "conflicts": list(self.conflicts),
        }


@dataclass(frozen=True)
class PLMBenchmarkCase:
    case_id: str
    split: str
    source_group: str
    contrast_group: str | None
    language: str
    input_text: str
    expected: ExpectedSemantics

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.case_id,
            "split": self.split,
            "source_group": self.source_group,
            "contrast_group": self.contrast_group,
            "language": self.language,
            "input": self.input_text,
            "expected": self.expected.as_dict(),
        }


@dataclass(frozen=True)
class PLMBenchmark:
    frozen_at: str
    authoring_method: str
    review_status: str
    policy: str
    cases: Tuple[PLMBenchmarkCase, ...]

    def cases_for_splits(
        self,
        splits: Sequence[str] = ("train", "validation"),
    ) -> Tuple[PLMBenchmarkCase, ...]:
        unknown = sorted(set(splits) - set(PLM_BENCHMARK_SPLITS))
        if unknown:
            raise ValueError(f"unknown benchmark split: {unknown[0]}")
        return tuple(case for case in self.cases if case.split in splits)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PLM_BENCHMARK_SCHEMA_VERSION,
            "frozen_at": self.frozen_at,
            "authoring_method": self.authoring_method,
            "review_status": self.review_status,
            "policy": self.policy,
            "cases": [case.as_dict() for case in self.cases],
        }


def _parse_evidence(
    value: Any,
    input_text: str,
    field: str,
) -> Tuple[BenchmarkEvidence, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    evidence = []
    for index, raw in enumerate(value):
        payload = _strict_object(
            raw,
            f"{field}[{index}]",
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
            or end > len(input_text)
        ):
            raise ValueError(f"{field}[{index}] has invalid source offsets")
        evidence.append(
            BenchmarkEvidence(
                signal=_non_empty_string(
                    payload["signal"],
                    f"{field}[{index}].signal",
                ),
                start=start,
                end=end,
            )
        )
    ordering = [(item.start, item.end, item.signal) for item in evidence]
    if ordering != sorted(ordering):
        raise ValueError(f"{field} must be ordered by source position")
    if len(set(ordering)) != len(ordering):
        raise ValueError(f"{field} must contain unique spans")
    return tuple(evidence)


def _parse_expected(
    value: Any,
    input_text: str,
    field: str,
) -> ExpectedSemantics:
    payload = _strict_object(
        value,
        field,
        (
            "primary_intent",
            "operations",
            "information_state",
            "constraints",
            "risk",
            "evidence",
            "unknowns",
            "conflicts",
        ),
    )
    primary_intent = payload["primary_intent"]
    if primary_intent not in INTENTS:
        raise ValueError(f"{field} has unknown intent: {primary_intent}")
    operations = _string_list(
        payload["operations"],
        f"{field}.operations",
        allowed=OPERATIONS,
    )
    information = _strict_object(
        payload["information_state"],
        f"{field}.information_state",
        (
            "missing_required_information",
            "contains_unverified_claims",
            "requires_current_information",
            "multiple_intents",
        ),
    )
    constraints = _strict_object(
        payload["constraints"],
        f"{field}.constraints",
        ("response_length", "formats", "must", "must_not"),
    )
    response_length = constraints["response_length"]
    if response_length not in RESPONSE_LENGTHS:
        raise ValueError(f"{field} has unknown response length")
    must = _string_list(constraints["must"], f"{field}.constraints.must")
    must_not = _string_list(
        constraints["must_not"],
        f"{field}.constraints.must_not",
    )
    if set(must) & set(must_not):
        raise ValueError(f"{field} has conflicting constraints")
    risk = _strict_object(
        payload["risk"],
        f"{field}.risk",
        ("level", "flags"),
    )
    risk_level = risk["level"]
    if risk_level not in RISK_LEVELS:
        raise ValueError(f"{field} has unknown risk level")
    return ExpectedSemantics(
        primary_intent=primary_intent,
        operations=operations,
        missing_required_information=_boolean(
            information["missing_required_information"],
            f"{field}.information_state.missing_required_information",
        ),
        contains_unverified_claims=_boolean(
            information["contains_unverified_claims"],
            f"{field}.information_state.contains_unverified_claims",
        ),
        requires_current_information=_boolean(
            information["requires_current_information"],
            f"{field}.information_state.requires_current_information",
        ),
        multiple_intents=_boolean(
            information["multiple_intents"],
            f"{field}.information_state.multiple_intents",
        ),
        response_length=response_length,
        formats=_string_list(
            constraints["formats"],
            f"{field}.constraints.formats",
        ),
        must=must,
        must_not=must_not,
        risk_level=risk_level,
        risk_flags=_string_list(
            risk["flags"],
            f"{field}.risk.flags",
        ),
        evidence=_parse_evidence(
            payload["evidence"],
            input_text,
            f"{field}.evidence",
        ),
        unknowns=_string_list(payload["unknowns"], f"{field}.unknowns"),
        conflicts=_string_list(payload["conflicts"], f"{field}.conflicts"),
    )


def parse_plm_benchmark(value: Any) -> PLMBenchmark:
    payload = _strict_object(
        value,
        "benchmark",
        (
            "schema_version",
            "frozen_at",
            "authoring_method",
            "review_status",
            "policy",
            "cases",
        ),
    )
    if payload["schema_version"] != PLM_BENCHMARK_SCHEMA_VERSION:
        raise ValueError("unsupported Pattern Language benchmark schema")
    review_status = payload["review_status"]
    if review_status not in PLM_BENCHMARK_REVIEW_STATUSES:
        raise ValueError("unsupported benchmark review status")
    raw_cases = payload["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("benchmark cases must be a non-empty array")

    cases = []
    ids = set()
    text_by_split: Dict[str, set[str]] = {
        split: set() for split in PLM_BENCHMARK_SPLITS
    }
    group_splits: Dict[str, str] = {}
    for index, raw in enumerate(raw_cases):
        field = f"cases[{index}]"
        case = _strict_object(
            raw,
            field,
            (
                "id",
                "split",
                "source_group",
                "contrast_group",
                "language",
                "input",
                "expected",
            ),
        )
        case_id = _non_empty_string(case["id"], f"{field}.id")
        if case_id in ids:
            raise ValueError(f"duplicate benchmark case id: {case_id}")
        ids.add(case_id)
        split = case["split"]
        if split not in PLM_BENCHMARK_SPLITS:
            raise ValueError(f"unknown benchmark split: {split}")
        language = case["language"]
        if language not in LANGUAGES:
            raise ValueError(f"unknown benchmark language: {language}")
        input_text = _non_empty_string(case["input"], f"{field}.input")
        if any(input_text in texts for texts in text_by_split.values()):
            raise ValueError("benchmark input texts must be globally unique")
        text_by_split[split].add(input_text)
        contrast_group = case["contrast_group"]
        if contrast_group is not None:
            contrast_group = _non_empty_string(
                contrast_group,
                f"{field}.contrast_group",
            )
            previous = group_splits.setdefault(contrast_group, split)
            if previous != split:
                raise ValueError(
                    "contrast groups must not cross benchmark splits"
                )
        cases.append(
            PLMBenchmarkCase(
                case_id=case_id,
                split=split,
                source_group=_non_empty_string(
                    case["source_group"],
                    f"{field}.source_group",
                ),
                contrast_group=contrast_group,
                language=language,
                input_text=input_text,
                expected=_parse_expected(
                    case["expected"],
                    input_text,
                    f"{field}.expected",
                ),
            )
        )

    return PLMBenchmark(
        frozen_at=_non_empty_string(payload["frozen_at"], "frozen_at"),
        authoring_method=_non_empty_string(
            payload["authoring_method"],
            "authoring_method",
        ),
        review_status=review_status,
        policy=_non_empty_string(payload["policy"], "policy"),
        cases=tuple(cases),
    )


def load_plm_benchmark(path: str | Path) -> PLMBenchmark:
    return parse_plm_benchmark(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )
