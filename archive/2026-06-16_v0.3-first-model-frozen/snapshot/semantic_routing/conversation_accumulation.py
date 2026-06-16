"""Contract for time-boxed open conversation-routing accumulation."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from .processing_plan import CORE_MODES, PROCESSING_CLASSES
from .semantic_packet import INTENTS, LANGUAGES


CONVERSATION_ACCUMULATION_SCHEMA_VERSION = "conversation-accumulation.v1"
CAMPAIGN_STATUSES = ("collecting", "ready_for_review", "closed")
REVIEW_STATUSES = ("draft", "approved", "rejected")


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


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _ratio(value: Any, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0.0 <= float(value) <= 1.0
    ):
        raise ValueError(f"{field} must be a number in [0, 1]")
    return float(value)


def _timestamp(value: Any, field: str) -> str:
    text = _non_empty_string(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return text


@dataclass(frozen=True)
class AccumulationCandidate:
    adapter_kind: str
    adapter_version: str
    frozen_at: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "adapter_kind": self.adapter_kind,
            "adapter_version": self.adapter_version,
            "frozen_at": self.frozen_at,
        }


@dataclass(frozen=True)
class AccumulationPolicy:
    same_batch_tuning_allowed: bool
    active_sealed_v2_must_remain_unread: bool
    min_reviewed_cases: int
    min_end_to_end_accuracy: float
    max_critical_underprocessing: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "same_batch_tuning_allowed": self.same_batch_tuning_allowed,
            "active_sealed_v2_must_remain_unread": (
                self.active_sealed_v2_must_remain_unread
            ),
            "min_reviewed_cases": self.min_reviewed_cases,
            "min_end_to_end_accuracy": self.min_end_to_end_accuracy,
            "max_critical_underprocessing": (
                self.max_critical_underprocessing
            ),
        }


@dataclass(frozen=True)
class AccumulationExpected:
    intent: str
    processing_class: str
    core_mode: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "intent": self.intent,
            "processing_class": self.processing_class,
            "core_mode": self.core_mode,
        }


@dataclass(frozen=True)
class AccumulationCase:
    case_id: str
    batch: str
    collected_at: str
    category: str
    language: str
    input_text: str
    expected: AccumulationExpected
    critical_underprocessing: bool
    review_status: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.case_id,
            "batch": self.batch,
            "collected_at": self.collected_at,
            "category": self.category,
            "language": self.language,
            "input": self.input_text,
            "expected": self.expected.as_dict(),
            "critical_underprocessing": self.critical_underprocessing,
            "review_status": self.review_status,
        }


@dataclass(frozen=True)
class ConversationAccumulation:
    campaign_id: str
    status: str
    started_at: str
    deadline_at: str
    target_case_count: int
    candidate: AccumulationCandidate
    policy: AccumulationPolicy
    required_categories: Mapping[str, int]
    cases: Tuple[AccumulationCase, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": CONVERSATION_ACCUMULATION_SCHEMA_VERSION,
            "campaign_id": self.campaign_id,
            "status": self.status,
            "started_at": self.started_at,
            "deadline_at": self.deadline_at,
            "target_case_count": self.target_case_count,
            "candidate": self.candidate.as_dict(),
            "policy": self.policy.as_dict(),
            "required_categories": dict(self.required_categories),
            "cases": [case.as_dict() for case in self.cases],
        }


def _parse_candidate(value: Any) -> AccumulationCandidate:
    payload = _strict_object(
        value,
        "candidate",
        ("adapter_kind", "adapter_version", "frozen_at"),
    )
    return AccumulationCandidate(
        adapter_kind=_non_empty_string(
            payload["adapter_kind"],
            "candidate.adapter_kind",
        ),
        adapter_version=_non_empty_string(
            payload["adapter_version"],
            "candidate.adapter_version",
        ),
        frozen_at=_timestamp(payload["frozen_at"], "candidate.frozen_at"),
    )


def _parse_policy(value: Any) -> AccumulationPolicy:
    payload = _strict_object(
        value,
        "policy",
        (
            "same_batch_tuning_allowed",
            "active_sealed_v2_must_remain_unread",
            "min_reviewed_cases",
            "min_end_to_end_accuracy",
            "max_critical_underprocessing",
        ),
    )
    if payload["same_batch_tuning_allowed"] is not False:
        raise ValueError("same-batch tuning must remain disabled")
    if payload["active_sealed_v2_must_remain_unread"] is not True:
        raise ValueError("active sealed v2 must remain unread")
    maximum = payload["max_critical_underprocessing"]
    if isinstance(maximum, bool) or not isinstance(maximum, int) or maximum < 0:
        raise ValueError(
            "policy.max_critical_underprocessing must be a non-negative integer"
        )
    return AccumulationPolicy(
        same_batch_tuning_allowed=False,
        active_sealed_v2_must_remain_unread=True,
        min_reviewed_cases=_positive_int(
            payload["min_reviewed_cases"],
            "policy.min_reviewed_cases",
        ),
        min_end_to_end_accuracy=_ratio(
            payload["min_end_to_end_accuracy"],
            "policy.min_end_to_end_accuracy",
        ),
        max_critical_underprocessing=maximum,
    )


def _parse_expected(value: Any, field: str) -> AccumulationExpected:
    payload = _strict_object(
        value,
        field,
        ("intent", "processing_class", "core_mode"),
    )
    intent = payload["intent"]
    processing_class = payload["processing_class"]
    core_mode = payload["core_mode"]
    if intent not in INTENTS:
        raise ValueError(f"{field}.intent is unknown: {intent}")
    if processing_class not in PROCESSING_CLASSES:
        raise ValueError(
            f"{field}.processing_class is unknown: {processing_class}"
        )
    if core_mode not in CORE_MODES:
        raise ValueError(f"{field}.core_mode is unknown: {core_mode}")
    return AccumulationExpected(intent, processing_class, core_mode)


def _parse_case(value: Any, index: int) -> AccumulationCase:
    field = f"cases[{index}]"
    payload = _strict_object(
        value,
        field,
        (
            "id",
            "batch",
            "collected_at",
            "category",
            "language",
            "input",
            "expected",
            "critical_underprocessing",
            "review_status",
        ),
    )
    language = payload["language"]
    if language not in LANGUAGES:
        raise ValueError(f"{field}.language is unknown: {language}")
    critical = payload["critical_underprocessing"]
    if not isinstance(critical, bool):
        raise ValueError(f"{field}.critical_underprocessing must be boolean")
    review_status = payload["review_status"]
    if review_status not in REVIEW_STATUSES:
        raise ValueError(
            f"{field}.review_status is unknown: {review_status}"
        )
    return AccumulationCase(
        case_id=_non_empty_string(payload["id"], f"{field}.id"),
        batch=_non_empty_string(payload["batch"], f"{field}.batch"),
        collected_at=_timestamp(
            payload["collected_at"],
            f"{field}.collected_at",
        ),
        category=_non_empty_string(
            payload["category"],
            f"{field}.category",
        ),
        language=language,
        input_text=_non_empty_string(payload["input"], f"{field}.input"),
        expected=_parse_expected(payload["expected"], f"{field}.expected"),
        critical_underprocessing=critical,
        review_status=review_status,
    )


def parse_conversation_accumulation(value: Any) -> ConversationAccumulation:
    payload = _strict_object(
        value,
        "conversation accumulation",
        (
            "schema_version",
            "campaign_id",
            "status",
            "started_at",
            "deadline_at",
            "target_case_count",
            "candidate",
            "policy",
            "required_categories",
            "cases",
        ),
    )
    if payload["schema_version"] != CONVERSATION_ACCUMULATION_SCHEMA_VERSION:
        raise ValueError("unsupported conversation accumulation schema")
    status = payload["status"]
    if status not in CAMPAIGN_STATUSES:
        raise ValueError(f"unknown campaign status: {status}")
    started_at = _timestamp(payload["started_at"], "started_at")
    deadline_at = _timestamp(payload["deadline_at"], "deadline_at")
    if datetime.fromisoformat(deadline_at) <= datetime.fromisoformat(started_at):
        raise ValueError("deadline_at must be after started_at")

    raw_categories = payload["required_categories"]
    if not isinstance(raw_categories, Mapping) or not raw_categories:
        raise ValueError("required_categories must be a non-empty object")
    required_categories = {
        _non_empty_string(name, "required_categories key"): _positive_int(
            count,
            f"required_categories.{name}",
        )
        for name, count in raw_categories.items()
    }

    raw_cases = payload["cases"]
    if not isinstance(raw_cases, list):
        raise ValueError("cases must be an array")
    cases = tuple(_parse_case(item, index) for index, item in enumerate(raw_cases))
    ids = [case.case_id for case in cases]
    texts = [case.input_text for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("case ids must be unique")
    if len(texts) != len(set(texts)):
        raise ValueError("case inputs must be unique")
    unknown_categories = sorted(
        {case.category for case in cases} - set(required_categories)
    )
    if unknown_categories:
        raise ValueError(
            f"case category is not declared: {unknown_categories[0]}"
        )

    policy = _parse_policy(payload["policy"])
    target_case_count = _positive_int(
        payload["target_case_count"],
        "target_case_count",
    )
    if policy.min_reviewed_cases > target_case_count:
        raise ValueError("min_reviewed_cases cannot exceed target_case_count")

    return ConversationAccumulation(
        campaign_id=_non_empty_string(payload["campaign_id"], "campaign_id"),
        status=status,
        started_at=started_at,
        deadline_at=deadline_at,
        target_case_count=target_case_count,
        candidate=_parse_candidate(payload["candidate"]),
        policy=policy,
        required_categories=required_categories,
        cases=cases,
    )


def load_conversation_accumulation(path: Path) -> ConversationAccumulation:
    return parse_conversation_accumulation(
        json.loads(path.read_text(encoding="utf-8"))
    )
