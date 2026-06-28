"""V4 puzzle solver trace and Puzzle Failure Memory contracts."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple


PUZZLE_SOLVER_TRACE_SCHEMA_VERSION = "v4-puzzle-solver-trace.v1"
PUZZLE_FAILURE_MEMORY_SCHEMA_VERSION = "v4-puzzle-failure-memory.v1"
SOLVER_TRACE_STATUSES = ("success", "failure")
PUZZLE_FAILURE_LANES = ("puzzle_failure_memory",)
TRAINING_STATUSES = ("not_training_data",)
TRACE_ALLOWED_USES = ("nonsealed_puzzle_trace_observation",)
FAILURE_ALLOWED_USES = ("nonsealed_puzzle_failure_memory_replay_only",)


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


def _ratio(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number in [0, 1]")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{field} must be a number in [0, 1]")
    return result


def _timestamp(value: Any, field: str) -> str:
    text = _non_empty_string(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return text


def _string_list(
    value: Any,
    field: str,
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
    return items


@dataclass(frozen=True)
class PuzzleSolverTrace:
    trace_id: str
    task_id: str
    selected_route: str
    predicted_answer: str | None
    operations_emitted: Tuple[str, ...]
    confidence: float
    status: str
    fail_point: str | None
    failure_reason: str | None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "selected_route": self.selected_route,
            "predicted_answer": self.predicted_answer,
            "operations_emitted": list(self.operations_emitted),
            "confidence": self.confidence,
            "status": self.status,
            "fail_point": self.fail_point,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class PuzzleSolverTraceReport:
    generated_at: str
    seed_fixture: str
    solver: Mapping[str, Any]
    policy: Mapping[str, Any]
    summary: Mapping[str, Any]
    traces: Tuple[PuzzleSolverTrace, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PUZZLE_SOLVER_TRACE_SCHEMA_VERSION,
            "generated_at": self.generated_at,
            "seed_fixture": self.seed_fixture,
            "solver": dict(self.solver),
            "policy": dict(self.policy),
            "summary": dict(self.summary),
            "traces": [trace.as_dict() for trace in self.traces],
        }


@dataclass(frozen=True)
class PuzzleFailureMemoryItem:
    memory_id: str
    source_task_id: str
    source_trace_id: str
    lane: str
    failure_condition: Tuple[str, ...]
    bad_tendency: Tuple[str, ...]
    guard_action: Tuple[str, ...]
    severity: str
    expected: Mapping[str, Any]
    actual: Mapping[str, Any]
    training_status: str
    allowed_use: str
    success_pattern_write_allowed: bool

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.memory_id,
            "source_task_id": self.source_task_id,
            "source_trace_id": self.source_trace_id,
            "lane": self.lane,
            "failure_condition": list(self.failure_condition),
            "bad_tendency": list(self.bad_tendency),
            "guard_action": list(self.guard_action),
            "severity": self.severity,
            "expected": dict(self.expected),
            "actual": dict(self.actual),
            "training_status": self.training_status,
            "allowed_use": self.allowed_use,
            "success_pattern_write_allowed": self.success_pattern_write_allowed,
        }


@dataclass(frozen=True)
class PuzzleFailureMemory:
    generated_at: str
    source_trace_report: str
    seed_fixture: str
    policy: Mapping[str, Any]
    summary: Mapping[str, Any]
    items: Tuple[PuzzleFailureMemoryItem, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PUZZLE_FAILURE_MEMORY_SCHEMA_VERSION,
            "generated_at": self.generated_at,
            "source_trace_report": self.source_trace_report,
            "seed_fixture": self.seed_fixture,
            "policy": dict(self.policy),
            "summary": dict(self.summary),
            "items": [item.as_dict() for item in self.items],
        }


def _parse_trace(value: Any, index: int) -> PuzzleSolverTrace:
    field = f"traces[{index}]"
    payload = _strict_object(
        value,
        field,
        (
            "trace_id",
            "task_id",
            "selected_route",
            "predicted_answer",
            "operations_emitted",
            "confidence",
            "status",
            "fail_point",
            "failure_reason",
        ),
    )
    status = payload["status"]
    if status not in SOLVER_TRACE_STATUSES:
        raise ValueError(f"{field}.status is unknown: {status}")
    if status == "failure" and payload["failure_reason"] is None:
        raise ValueError(f"{field}.failure_reason is required on failure")
    if status == "success" and payload["failure_reason"] is not None:
        raise ValueError(f"{field}.failure_reason must be null on success")
    return PuzzleSolverTrace(
        trace_id=_non_empty_string(payload["trace_id"], f"{field}.trace_id"),
        task_id=_non_empty_string(payload["task_id"], f"{field}.task_id"),
        selected_route=_non_empty_string(
            payload["selected_route"],
            f"{field}.selected_route",
        ),
        predicted_answer=_optional_string(
            payload["predicted_answer"],
            f"{field}.predicted_answer",
        ),
        operations_emitted=_string_list(
            payload["operations_emitted"],
            f"{field}.operations_emitted",
        ),
        confidence=_ratio(payload["confidence"], f"{field}.confidence"),
        status=status,
        fail_point=_optional_string(payload["fail_point"], f"{field}.fail_point"),
        failure_reason=_optional_string(
            payload["failure_reason"],
            f"{field}.failure_reason",
        ),
    )


def _validate_trace_policy(policy: Mapping[str, Any]) -> None:
    required = (
        "sealed_fixtures_used_as_sources",
        "v3_sealed_text_used",
        "success_pattern_lane_write_allowed",
        "solver_trace_only",
    )
    payload = _strict_object(policy, "policy", required)
    if _boolean(payload["sealed_fixtures_used_as_sources"], "policy.sealed_fixtures_used_as_sources"):
        raise ValueError("solver trace must not use sealed fixtures")
    if _boolean(payload["v3_sealed_text_used"], "policy.v3_sealed_text_used"):
        raise ValueError("solver trace must not use V3 sealed text")
    if _boolean(payload["success_pattern_lane_write_allowed"], "policy.success_pattern_lane_write_allowed"):
        raise ValueError("solver trace must not write success patterns")
    if not _boolean(payload["solver_trace_only"], "policy.solver_trace_only"):
        raise ValueError("solver trace must remain trace-only")


def parse_puzzle_solver_trace_report(value: Any) -> PuzzleSolverTraceReport:
    payload = _strict_object(
        value,
        "puzzle solver trace report",
        (
            "schema_version",
            "generated_at",
            "seed_fixture",
            "solver",
            "policy",
            "summary",
            "traces",
        ),
    )
    if payload["schema_version"] != PUZZLE_SOLVER_TRACE_SCHEMA_VERSION:
        raise ValueError("unsupported puzzle solver trace schema")
    _validate_trace_policy(payload["policy"])
    raw_traces = payload["traces"]
    if not isinstance(raw_traces, list):
        raise ValueError("traces must be an array")
    traces = tuple(_parse_trace(item, index) for index, item in enumerate(raw_traces))
    ids = [trace.trace_id for trace in traces]
    task_ids = [trace.task_id for trace in traces]
    if len(ids) != len(set(ids)):
        raise ValueError("trace ids must be unique")
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("task ids must be unique in trace report")
    summary = _strict_object(
        payload["summary"],
        "summary",
        (
            "task_count",
            "success_count",
            "failure_count",
            "success_rate",
            "failed_task_ids",
        ),
    )
    failures = [trace for trace in traces if trace.status == "failure"]
    successes = [trace for trace in traces if trace.status == "success"]
    if summary["task_count"] != len(traces):
        raise ValueError("summary.task_count does not match traces")
    if summary["success_count"] != len(successes):
        raise ValueError("summary.success_count does not match traces")
    if summary["failure_count"] != len(failures):
        raise ValueError("summary.failure_count does not match traces")
    if summary["failed_task_ids"] != [trace.task_id for trace in failures]:
        raise ValueError("summary.failed_task_ids does not match traces")
    expected_rate = len(successes) / len(traces) if traces else 0.0
    if _ratio(summary["success_rate"], "summary.success_rate") != expected_rate:
        raise ValueError("summary.success_rate does not match traces")
    solver = _strict_object(
        payload["solver"],
        "solver",
        ("name", "version", "kind", "notes"),
    )
    return PuzzleSolverTraceReport(
        generated_at=_timestamp(payload["generated_at"], "generated_at"),
        seed_fixture=_non_empty_string(payload["seed_fixture"], "seed_fixture"),
        solver=solver,
        policy=payload["policy"],
        summary=summary,
        traces=traces,
    )


def _parse_failure_item(value: Any, index: int) -> PuzzleFailureMemoryItem:
    field = f"items[{index}]"
    payload = _strict_object(
        value,
        field,
        (
            "id",
            "source_task_id",
            "source_trace_id",
            "lane",
            "failure_condition",
            "bad_tendency",
            "guard_action",
            "severity",
            "expected",
            "actual",
            "training_status",
            "allowed_use",
            "success_pattern_write_allowed",
        ),
    )
    lane = payload["lane"]
    if lane not in PUZZLE_FAILURE_LANES:
        raise ValueError(f"{field}.lane is unknown: {lane}")
    training_status = payload["training_status"]
    if training_status not in TRAINING_STATUSES:
        raise ValueError(f"{field}.training_status is unknown: {training_status}")
    allowed_use = payload["allowed_use"]
    if allowed_use not in FAILURE_ALLOWED_USES:
        raise ValueError(f"{field}.allowed_use is unknown: {allowed_use}")
    if _boolean(payload["success_pattern_write_allowed"], f"{field}.success_pattern_write_allowed"):
        raise ValueError(f"{field} must not write success patterns")
    expected = _strict_object(
        payload["expected"],
        f"{field}.expected",
        ("route", "answer", "answer_type"),
    )
    actual = _strict_object(
        payload["actual"],
        f"{field}.actual",
        ("route", "answer", "operations_emitted", "fail_point"),
    )
    return PuzzleFailureMemoryItem(
        memory_id=_non_empty_string(payload["id"], f"{field}.id"),
        source_task_id=_non_empty_string(payload["source_task_id"], f"{field}.source_task_id"),
        source_trace_id=_non_empty_string(payload["source_trace_id"], f"{field}.source_trace_id"),
        lane=lane,
        failure_condition=_string_list(payload["failure_condition"], f"{field}.failure_condition"),
        bad_tendency=_string_list(payload["bad_tendency"], f"{field}.bad_tendency"),
        guard_action=_string_list(payload["guard_action"], f"{field}.guard_action"),
        severity=_non_empty_string(payload["severity"], f"{field}.severity"),
        expected=expected,
        actual=actual,
        training_status=training_status,
        allowed_use=allowed_use,
        success_pattern_write_allowed=False,
    )


def _validate_failure_policy(policy: Mapping[str, Any]) -> None:
    required = (
        "sealed_fixtures_used_as_sources",
        "v3_sealed_text_used",
        "success_pattern_lane_write_allowed",
        "source_success_traces_used_for_training",
    )
    payload = _strict_object(policy, "policy", required)
    if _boolean(payload["sealed_fixtures_used_as_sources"], "policy.sealed_fixtures_used_as_sources"):
        raise ValueError("puzzle failure memory must not use sealed fixtures")
    if _boolean(payload["v3_sealed_text_used"], "policy.v3_sealed_text_used"):
        raise ValueError("puzzle failure memory must not use V3 sealed text")
    if _boolean(payload["success_pattern_lane_write_allowed"], "policy.success_pattern_lane_write_allowed"):
        raise ValueError("puzzle failure memory must not write success patterns")
    if _boolean(payload["source_success_traces_used_for_training"], "policy.source_success_traces_used_for_training"):
        raise ValueError("success traces must not be used for training here")


def parse_puzzle_failure_memory(value: Any) -> PuzzleFailureMemory:
    payload = _strict_object(
        value,
        "puzzle failure memory",
        (
            "schema_version",
            "generated_at",
            "source_trace_report",
            "seed_fixture",
            "policy",
            "summary",
            "items",
        ),
    )
    if payload["schema_version"] != PUZZLE_FAILURE_MEMORY_SCHEMA_VERSION:
        raise ValueError("unsupported puzzle failure memory schema")
    _validate_failure_policy(payload["policy"])
    raw_items = payload["items"]
    if not isinstance(raw_items, list):
        raise ValueError("items must be an array")
    items = tuple(_parse_failure_item(item, index) for index, item in enumerate(raw_items))
    ids = [item.memory_id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("failure memory ids must be unique")
    summary = _strict_object(
        payload["summary"],
        "summary",
        ("failure_count", "source_failed_task_ids", "by_severity"),
    )
    if summary["failure_count"] != len(items):
        raise ValueError("summary.failure_count does not match items")
    if summary["source_failed_task_ids"] != [item.source_task_id for item in items]:
        raise ValueError("summary.source_failed_task_ids does not match items")
    return PuzzleFailureMemory(
        generated_at=_timestamp(payload["generated_at"], "generated_at"),
        source_trace_report=_non_empty_string(
            payload["source_trace_report"],
            "source_trace_report",
        ),
        seed_fixture=_non_empty_string(payload["seed_fixture"], "seed_fixture"),
        policy=payload["policy"],
        summary=summary,
        items=items,
    )


def load_puzzle_solver_trace_report(path: Path) -> PuzzleSolverTraceReport:
    return parse_puzzle_solver_trace_report(json.loads(path.read_text(encoding="utf-8")))


def load_puzzle_failure_memory(path: Path) -> PuzzleFailureMemory:
    return parse_puzzle_failure_memory(json.loads(path.read_text(encoding="utf-8")))
