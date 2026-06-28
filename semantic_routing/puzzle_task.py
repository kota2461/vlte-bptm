"""V4 puzzle task seed contract.

Puzzle seeds are non-sealed review material. They are not success-pattern
training labels; solver failures must flow through Puzzle Failure Memory first.
"""

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from .semantic_packet import LANGUAGES


PUZZLE_TASK_SEED_SCHEMA_VERSION = "v4-puzzle-task-seed.v1"
PUZZLE_STATUSES = ("draft_seed", "reviewed_seed")
PUZZLE_DOMAINS = (
    "arithmetic",
    "sequence",
    "logic",
    "constraint_satisfaction",
    "language",
    "ambiguous",
)
PUZZLE_DIFFICULTIES = ("easy", "medium")
PUZZLE_EXPECTED_ROUTES = ("solve", "clarify")
PUZZLE_ANSWER_TYPES = (
    "number",
    "text",
    "choice",
    "ordering",
    "time",
    "clarification",
)
PUZZLE_OPERATIONS = (
    "parse_conditions",
    "pattern_detect",
    "calculate",
    "deduce",
    "eliminate",
    "compare",
    "preserve_constraints",
    "ask_clarify",
)
REVIEW_STATUSES = ("draft", "approved", "rejected")
TRAINING_STATUSES = ("not_training_data",)
ALLOWED_USES = ("nonsealed_puzzle_seed_replay_only",)
SEVERITIES = ("minor", "medium", "major", "critical")


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


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _non_empty_string(value, field)


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _timestamp(value: Any, field: str) -> str:
    text = _non_empty_string(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return text


def _identifier_list(
    value: Any,
    field: str,
    allowed: Tuple[str, ...] | None = None,
    *,
    require_non_empty: bool = True,
) -> Tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    items = tuple(_non_empty_string(item, field) for item in value)
    if require_non_empty and not items:
        raise ValueError(f"{field} must not be empty")
    if len(items) != len(set(items)):
        raise ValueError(f"{field} must contain unique values")
    if allowed is not None:
        unknown = sorted(set(items) - set(allowed))
        if unknown:
            raise ValueError(f"{field} contains unknown value: {unknown[0]}")
    return items


@dataclass(frozen=True)
class PuzzlePolicy:
    sealed_fixtures_used_as_sources: bool
    v3_sealed_text_used: bool
    success_pattern_lane_write_allowed: bool
    failures_enter_failure_memory_first: bool
    human_review_required_before_training: bool
    same_cycle_promotion_allowed: bool

    def as_dict(self) -> Dict[str, bool]:
        return {
            "sealed_fixtures_used_as_sources": self.sealed_fixtures_used_as_sources,
            "v3_sealed_text_used": self.v3_sealed_text_used,
            "success_pattern_lane_write_allowed": self.success_pattern_lane_write_allowed,
            "failures_enter_failure_memory_first": self.failures_enter_failure_memory_first,
            "human_review_required_before_training": self.human_review_required_before_training,
            "same_cycle_promotion_allowed": self.same_cycle_promotion_allowed,
        }


@dataclass(frozen=True)
class PuzzleExpected:
    route: str
    answer: str | None
    answer_type: str
    rationale_tags: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "answer": self.answer,
            "answer_type": self.answer_type,
            "rationale_tags": list(self.rationale_tags),
        }


@dataclass(frozen=True)
class PuzzleAmbiguity:
    ambiguous: bool
    missing_required_information: bool
    notes: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ambiguous": self.ambiguous,
            "missing_required_information": self.missing_required_information,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PuzzleConstraints:
    response_format: str
    max_steps: int
    allow_multiple_answers: bool

    def as_dict(self) -> Dict[str, Any]:
        return {
            "response_format": self.response_format,
            "max_steps": self.max_steps,
            "allow_multiple_answers": self.allow_multiple_answers,
        }


@dataclass(frozen=True)
class PuzzleGuardExpectations:
    on_failure_bad_tendency: Tuple[str, ...]
    guard_action: Tuple[str, ...]
    severity: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "on_failure_bad_tendency": list(self.on_failure_bad_tendency),
            "guard_action": list(self.guard_action),
            "severity": self.severity,
        }


@dataclass(frozen=True)
class PuzzleTask:
    task_id: str
    language: str
    domain: str
    difficulty: str
    input_text: str
    expected: PuzzleExpected
    allowed_reasoning_operations: Tuple[str, ...]
    ambiguity: PuzzleAmbiguity
    constraints: PuzzleConstraints
    guard_expectations: PuzzleGuardExpectations
    review_status: str
    training_status: str
    allowed_use: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.task_id,
            "language": self.language,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "input": self.input_text,
            "expected": self.expected.as_dict(),
            "allowed_reasoning_operations": list(self.allowed_reasoning_operations),
            "ambiguity": self.ambiguity.as_dict(),
            "constraints": self.constraints.as_dict(),
            "guard_expectations": self.guard_expectations.as_dict(),
            "review_status": self.review_status,
            "training_status": self.training_status,
            "allowed_use": self.allowed_use,
        }


@dataclass(frozen=True)
class PuzzleTaskSeed:
    generated_at: str
    status: str
    policy: PuzzlePolicy
    schema: Mapping[str, Any]
    summary: Mapping[str, Any]
    tasks: Tuple[PuzzleTask, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PUZZLE_TASK_SEED_SCHEMA_VERSION,
            "generated_at": self.generated_at,
            "status": self.status,
            "policy": self.policy.as_dict(),
            "schema": dict(self.schema),
            "summary": dict(self.summary),
            "tasks": [task.as_dict() for task in self.tasks],
        }


def _parse_policy(value: Any) -> PuzzlePolicy:
    payload = _strict_object(
        value,
        "policy",
        (
            "sealed_fixtures_used_as_sources",
            "v3_sealed_text_used",
            "success_pattern_lane_write_allowed",
            "failures_enter_failure_memory_first",
            "human_review_required_before_training",
            "same_cycle_promotion_allowed",
        ),
    )
    policy = PuzzlePolicy(
        sealed_fixtures_used_as_sources=_boolean(
            payload["sealed_fixtures_used_as_sources"],
            "policy.sealed_fixtures_used_as_sources",
        ),
        v3_sealed_text_used=_boolean(
            payload["v3_sealed_text_used"],
            "policy.v3_sealed_text_used",
        ),
        success_pattern_lane_write_allowed=_boolean(
            payload["success_pattern_lane_write_allowed"],
            "policy.success_pattern_lane_write_allowed",
        ),
        failures_enter_failure_memory_first=_boolean(
            payload["failures_enter_failure_memory_first"],
            "policy.failures_enter_failure_memory_first",
        ),
        human_review_required_before_training=_boolean(
            payload["human_review_required_before_training"],
            "policy.human_review_required_before_training",
        ),
        same_cycle_promotion_allowed=_boolean(
            payload["same_cycle_promotion_allowed"],
            "policy.same_cycle_promotion_allowed",
        ),
    )
    if policy.sealed_fixtures_used_as_sources:
        raise ValueError("puzzle seeds must not use sealed fixtures")
    if policy.v3_sealed_text_used:
        raise ValueError("puzzle seeds must not use V3 sealed text")
    if policy.success_pattern_lane_write_allowed:
        raise ValueError("puzzle seeds must not write success patterns")
    if not policy.failures_enter_failure_memory_first:
        raise ValueError("puzzle failures must enter failure memory first")
    if policy.same_cycle_promotion_allowed:
        raise ValueError("same-cycle promotion must remain disabled")
    return policy


def _parse_expected(value: Any, field: str) -> PuzzleExpected:
    payload = _strict_object(
        value,
        field,
        ("route", "answer", "answer_type", "rationale_tags"),
    )
    route = payload["route"]
    answer_type = payload["answer_type"]
    if route not in PUZZLE_EXPECTED_ROUTES:
        raise ValueError(f"{field}.route is unknown: {route}")
    if answer_type not in PUZZLE_ANSWER_TYPES:
        raise ValueError(f"{field}.answer_type is unknown: {answer_type}")
    if route == "solve" and payload["answer"] is None:
        raise ValueError(f"{field}.answer must be present for solve tasks")
    if route == "clarify" and answer_type != "clarification":
        raise ValueError(f"{field}.answer_type must be clarification")
    return PuzzleExpected(
        route=route,
        answer=_optional_string(payload["answer"], f"{field}.answer"),
        answer_type=answer_type,
        rationale_tags=_identifier_list(
            payload["rationale_tags"],
            f"{field}.rationale_tags",
        ),
    )


def _parse_ambiguity(value: Any, field: str) -> PuzzleAmbiguity:
    payload = _strict_object(
        value,
        field,
        ("ambiguous", "missing_required_information", "notes"),
    )
    return PuzzleAmbiguity(
        ambiguous=_boolean(payload["ambiguous"], f"{field}.ambiguous"),
        missing_required_information=_boolean(
            payload["missing_required_information"],
            f"{field}.missing_required_information",
        ),
        notes=_identifier_list(payload["notes"], f"{field}.notes", None, require_non_empty=False),
    )


def _parse_constraints(value: Any, field: str) -> PuzzleConstraints:
    payload = _strict_object(
        value,
        field,
        ("response_format", "max_steps", "allow_multiple_answers"),
    )
    return PuzzleConstraints(
        response_format=_non_empty_string(
            payload["response_format"],
            f"{field}.response_format",
        ),
        max_steps=_positive_int(payload["max_steps"], f"{field}.max_steps"),
        allow_multiple_answers=_boolean(
            payload["allow_multiple_answers"],
            f"{field}.allow_multiple_answers",
        ),
    )


def _parse_guard(value: Any, field: str) -> PuzzleGuardExpectations:
    payload = _strict_object(
        value,
        field,
        ("on_failure_bad_tendency", "guard_action", "severity"),
    )
    severity = payload["severity"]
    if severity not in SEVERITIES:
        raise ValueError(f"{field}.severity is unknown: {severity}")
    return PuzzleGuardExpectations(
        on_failure_bad_tendency=_identifier_list(
            payload["on_failure_bad_tendency"],
            f"{field}.on_failure_bad_tendency",
        ),
        guard_action=_identifier_list(
            payload["guard_action"],
            f"{field}.guard_action",
        ),
        severity=severity,
    )


def _parse_task(value: Any, index: int) -> PuzzleTask:
    field = f"tasks[{index}]"
    payload = _strict_object(
        value,
        field,
        (
            "id",
            "language",
            "domain",
            "difficulty",
            "input",
            "expected",
            "allowed_reasoning_operations",
            "ambiguity",
            "constraints",
            "guard_expectations",
            "review_status",
            "training_status",
            "allowed_use",
        ),
    )
    language = payload["language"]
    domain = payload["domain"]
    difficulty = payload["difficulty"]
    if language not in LANGUAGES:
        raise ValueError(f"{field}.language is unknown: {language}")
    if domain not in PUZZLE_DOMAINS:
        raise ValueError(f"{field}.domain is unknown: {domain}")
    if difficulty not in PUZZLE_DIFFICULTIES:
        raise ValueError(f"{field}.difficulty is unknown: {difficulty}")
    expected = _parse_expected(payload["expected"], f"{field}.expected")
    ambiguity = _parse_ambiguity(payload["ambiguity"], f"{field}.ambiguity")
    if (ambiguity.ambiguous or ambiguity.missing_required_information) and expected.route != "clarify":
        raise ValueError(f"{field} ambiguous/missing tasks must route to clarify")
    if expected.route == "clarify" and "ask_clarify" not in payload["allowed_reasoning_operations"]:
        raise ValueError(f"{field} clarify tasks must allow ask_clarify")
    review_status = payload["review_status"]
    training_status = payload["training_status"]
    allowed_use = payload["allowed_use"]
    if review_status not in REVIEW_STATUSES:
        raise ValueError(f"{field}.review_status is unknown: {review_status}")
    if training_status not in TRAINING_STATUSES:
        raise ValueError(f"{field}.training_status is unknown: {training_status}")
    if allowed_use not in ALLOWED_USES:
        raise ValueError(f"{field}.allowed_use is unknown: {allowed_use}")
    return PuzzleTask(
        task_id=_non_empty_string(payload["id"], f"{field}.id"),
        language=language,
        domain=domain,
        difficulty=difficulty,
        input_text=_non_empty_string(payload["input"], f"{field}.input"),
        expected=expected,
        allowed_reasoning_operations=_identifier_list(
            payload["allowed_reasoning_operations"],
            f"{field}.allowed_reasoning_operations",
            PUZZLE_OPERATIONS,
        ),
        ambiguity=ambiguity,
        constraints=_parse_constraints(payload["constraints"], f"{field}.constraints"),
        guard_expectations=_parse_guard(payload["guard_expectations"], f"{field}.guard_expectations"),
        review_status=review_status,
        training_status=training_status,
        allowed_use=allowed_use,
    )


def _validate_summary(summary: Mapping[str, Any], tasks: Tuple[PuzzleTask, ...]) -> None:
    required = (
        "task_count",
        "ambiguous_count",
        "missing_info_count",
        "by_domain",
        "by_expected_route",
        "by_difficulty",
    )
    _strict_object(summary, "summary", required)
    by_domain = dict(Counter(task.domain for task in tasks))
    by_route = dict(Counter(task.expected.route for task in tasks))
    by_difficulty = dict(Counter(task.difficulty for task in tasks))
    ambiguous_count = sum(task.ambiguity.ambiguous for task in tasks)
    missing_count = sum(task.ambiguity.missing_required_information for task in tasks)
    if summary["task_count"] != len(tasks):
        raise ValueError("summary.task_count does not match tasks")
    if summary["ambiguous_count"] != ambiguous_count:
        raise ValueError("summary.ambiguous_count does not match tasks")
    if summary["missing_info_count"] != missing_count:
        raise ValueError("summary.missing_info_count does not match tasks")
    if summary["by_domain"] != dict(sorted(by_domain.items())):
        raise ValueError("summary.by_domain does not match tasks")
    if summary["by_expected_route"] != dict(sorted(by_route.items())):
        raise ValueError("summary.by_expected_route does not match tasks")
    if summary["by_difficulty"] != dict(sorted(by_difficulty.items())):
        raise ValueError("summary.by_difficulty does not match tasks")


def parse_puzzle_task_seed(value: Any) -> PuzzleTaskSeed:
    payload = _strict_object(
        value,
        "puzzle task seed",
        (
            "schema_version",
            "generated_at",
            "status",
            "policy",
            "schema",
            "summary",
            "tasks",
        ),
    )
    if payload["schema_version"] != PUZZLE_TASK_SEED_SCHEMA_VERSION:
        raise ValueError("unsupported puzzle task seed schema")
    status = payload["status"]
    if status not in PUZZLE_STATUSES:
        raise ValueError(f"unknown puzzle seed status: {status}")
    raw_tasks = payload["tasks"]
    if not isinstance(raw_tasks, list):
        raise ValueError("tasks must be an array")
    tasks = tuple(_parse_task(item, index) for index, item in enumerate(raw_tasks))
    ids = [task.task_id for task in tasks]
    inputs = [task.input_text for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("task ids must be unique")
    if len(inputs) != len(set(inputs)):
        raise ValueError("task inputs must be unique")
    summary = _strict_object(
        payload["summary"],
        "summary",
        (
            "task_count",
            "ambiguous_count",
            "missing_info_count",
            "by_domain",
            "by_expected_route",
            "by_difficulty",
        ),
    )
    _validate_summary(summary, tasks)
    schema = _strict_object(
        payload["schema"],
        "schema",
        (
            "task_required_fields",
            "allowed_domains",
            "allowed_operations",
            "expected_routes",
        ),
    )
    if tuple(schema["allowed_domains"]) != PUZZLE_DOMAINS:
        raise ValueError("schema.allowed_domains does not match parser")
    if tuple(schema["allowed_operations"]) != PUZZLE_OPERATIONS:
        raise ValueError("schema.allowed_operations does not match parser")
    if tuple(schema["expected_routes"]) != PUZZLE_EXPECTED_ROUTES:
        raise ValueError("schema.expected_routes does not match parser")
    return PuzzleTaskSeed(
        generated_at=_timestamp(payload["generated_at"], "generated_at"),
        status=status,
        policy=_parse_policy(payload["policy"]),
        schema=schema,
        summary=summary,
        tasks=tasks,
    )


def load_puzzle_task_seed(path: Path) -> PuzzleTaskSeed:
    return parse_puzzle_task_seed(json.loads(path.read_text(encoding="utf-8")))
