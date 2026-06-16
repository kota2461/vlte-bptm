import hashlib
import json
import math
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple

from .pipeline import process


EXECUTOR_POLICY_SCHEMA_VERSION = "runtime-executor-policy.v1"
EXECUTOR_REQUEST_SCHEMA_VERSION = "runtime-executor-request.v1"
RUNTIME_CHECKPOINT_SCHEMA_VERSION = "runtime-checkpoint.v1"
RUNTIME_SESSION_SCHEMA_VERSION = "runtime-session.v1"
DEFAULT_EXECUTOR_POLICY_PATH = (
    Path(__file__).resolve().parent / "config" / "runtime_executor.json"
)
_PROCESSING_MODES = {"horizontal", "vertical", "hybrid"}
_ERROR_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_POLICY_FIELDS = {
    "schema_version",
    "timeout_ms",
    "poll_interval_ms",
    "max_attempts",
    "max_dispatches",
    "retry_on",
    "estimated_cost_units_per_attempt",
}


@dataclass(frozen=True)
class RuntimePolicy:
    timeout_ms: int
    poll_interval_ms: int
    max_attempts: int
    max_dispatches: int
    retry_on: Tuple[str, ...]
    estimated_cost_units_per_attempt: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": EXECUTOR_POLICY_SCHEMA_VERSION,
            "timeout_ms": self.timeout_ms,
            "poll_interval_ms": self.poll_interval_ms,
            "max_attempts": self.max_attempts,
            "max_dispatches": self.max_dispatches,
            "retry_on": list(self.retry_on),
            "estimated_cost_units_per_attempt": (
                self.estimated_cost_units_per_attempt
            ),
        }


@dataclass(frozen=True)
class ExecutorRequest:
    execution_id: str
    idempotency_key: str
    run_id: str
    processing_mode: str
    dispatch_index: int
    attempt: int
    stack_id: Optional[str]
    unit_id: str
    timeout_ms: int
    llm_order: Mapping[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": EXECUTOR_REQUEST_SCHEMA_VERSION,
            "execution_id": self.execution_id,
            "idempotency_key": self.idempotency_key,
            "run_id": self.run_id,
            "processing_mode": self.processing_mode,
            "dispatch_index": self.dispatch_index,
            "attempt": self.attempt,
            "stack_id": self.stack_id,
            "unit_id": self.unit_id,
            "timeout_ms": self.timeout_ms,
            "llm_order": dict(self.llm_order),
        }


class ExecutorAdapter(Protocol):
    def execute(self, request: ExecutorRequest) -> Mapping[str, Any]:
        ...

    def cancel(self, execution_id: str) -> None:
        ...


class ExecutorError(RuntimeError):
    def __init__(self, message: str, code: str) -> None:
        if (
            not isinstance(code, str)
            or _ERROR_CODE_PATTERN.fullmatch(code) is None
        ):
            raise ValueError("executor error code must be a machine identifier")
        super().__init__(message)
        self.code = code


class RetryableExecutorError(ExecutorError):
    pass


class PermanentExecutorError(ExecutorError):
    pass


@dataclass
class RuntimeCancellation:
    _event: Event = field(default_factory=Event)

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


@dataclass
class RuntimeCheckpoint:
    run_id: str
    input_digest: str
    processing_mode: str
    vertical_outputs: Dict[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    hybrid_outputs: Dict[
        str, Dict[str, Mapping[str, Any]]
    ] = field(default_factory=dict)
    horizontal_output: Optional[Mapping[str, Any]] = None
    attempts_by_key: Dict[str, int] = field(default_factory=dict)
    records: list[Dict[str, Any]] = field(default_factory=list)
    cumulative_elapsed_ms: float = 0.0
    cumulative_estimated_cost_units: float = 0.0

    def as_dict(self, include_outputs: bool = False) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "schema_version": RUNTIME_CHECKPOINT_SCHEMA_VERSION,
            "run_id": self.run_id,
            "input_digest": self.input_digest,
            "processing_mode": self.processing_mode,
            "completed_dispatch_count": self.completed_dispatch_count,
            "attempts_by_key": dict(self.attempts_by_key),
            "records": [dict(record) for record in self.records],
            "elapsed_ms": round(self.cumulative_elapsed_ms, 3),
            "estimated_cost_units": round(
                self.cumulative_estimated_cost_units,
                6,
            ),
            "contains_private_outputs": self.completed_dispatch_count > 0,
        }
        if include_outputs:
            payload["private_outputs"] = {
                "vertical": dict(self.vertical_outputs),
                "hybrid": {
                    stack_id: dict(outputs)
                    for stack_id, outputs in self.hybrid_outputs.items()
                },
                "horizontal": (
                    dict(self.horizontal_output)
                    if self.horizontal_output is not None
                    else None
                ),
            }
        return payload

    @property
    def completed_dispatch_count(self) -> int:
        if self.processing_mode == "horizontal":
            return int(self.horizontal_output is not None)
        if self.processing_mode == "vertical":
            return len(self.vertical_outputs)
        return sum(len(outputs) for outputs in self.hybrid_outputs.values())

    def clone(self) -> "RuntimeCheckpoint":
        return RuntimeCheckpoint(
            run_id=self.run_id,
            input_digest=self.input_digest,
            processing_mode=self.processing_mode,
            vertical_outputs=dict(self.vertical_outputs),
            hybrid_outputs={
                stack_id: dict(outputs)
                for stack_id, outputs in self.hybrid_outputs.items()
            },
            horizontal_output=(
                dict(self.horizontal_output)
                if self.horizontal_output is not None
                else None
            ),
            attempts_by_key=dict(self.attempts_by_key),
            records=[dict(record) for record in self.records],
            cumulative_elapsed_ms=self.cumulative_elapsed_ms,
            cumulative_estimated_cost_units=(
                self.cumulative_estimated_cost_units
            ),
        )


@dataclass(frozen=True)
class RuntimeSession:
    status: str
    run_id: str
    processing_mode: str
    stop_reason: Optional[str]
    elapsed_ms: float
    attempt_count: int
    dispatch_count: int
    estimated_cost_units: float
    pipeline_state: Mapping[str, Any]
    checkpoint: RuntimeCheckpoint
    policy: RuntimePolicy

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": RUNTIME_SESSION_SCHEMA_VERSION,
            "status": self.status,
            "run_id": self.run_id,
            "processing_mode": self.processing_mode,
            "stop_reason": self.stop_reason,
            "metrics": {
                "elapsed_ms": round(self.elapsed_ms, 3),
                "attempt_count": self.attempt_count,
                "dispatch_count": self.dispatch_count,
                "estimated_cost_units": round(
                    self.estimated_cost_units,
                    6,
                ),
            },
            "policy": self.policy.as_dict(),
            "checkpoint": self.checkpoint.as_dict(),
            "pipeline_state": dict(self.pipeline_state),
        }


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def load_runtime_policy(path: Optional[Path] = None) -> RuntimePolicy:
    config_path = path or DEFAULT_EXECUTOR_POLICY_PATH
    payload: Any = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("runtime executor policy must be an object")
    if set(payload) != _POLICY_FIELDS:
        raise ValueError("runtime executor policy fields do not match")
    if payload.get("schema_version") != EXECUTOR_POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported runtime executor policy schema")
    timeout_ms = _positive_int(payload.get("timeout_ms"), "timeout_ms")
    poll_interval_ms = _positive_int(
        payload.get("poll_interval_ms"),
        "poll_interval_ms",
    )
    if poll_interval_ms > timeout_ms:
        raise ValueError("poll_interval_ms cannot exceed timeout_ms")
    max_attempts = _positive_int(
        payload.get("max_attempts"),
        "max_attempts",
    )
    if max_attempts > 5:
        raise ValueError("max_attempts cannot exceed 5")
    max_dispatches = _positive_int(
        payload.get("max_dispatches"),
        "max_dispatches",
    )
    if max_dispatches > 32:
        raise ValueError("max_dispatches cannot exceed 32")
    retry_on = payload.get("retry_on")
    if (
        not isinstance(retry_on, list)
        or any(item not in {"retryable_error", "timeout"} for item in retry_on)
        or len(set(retry_on)) != len(retry_on)
    ):
        raise ValueError("retry_on contains unsupported retry reasons")
    cost = payload.get("estimated_cost_units_per_attempt")
    if (
        isinstance(cost, bool)
        or not isinstance(cost, (int, float))
        or not math.isfinite(cost)
        or cost < 0.0
    ):
        raise ValueError(
            "estimated_cost_units_per_attempt must be non-negative"
        )
    return RuntimePolicy(
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        max_attempts=max_attempts,
        max_dispatches=max_dispatches,
        retry_on=tuple(retry_on),
        estimated_cost_units_per_attempt=float(cost),
    )


DEFAULT_RUNTIME_POLICY = load_runtime_policy()


def _input_digest(user_input: str) -> str:
    return hashlib.sha256(user_input.encode("utf-8")).hexdigest()


def _idempotency_key(
    run_id: str,
    processing_mode: str,
    dispatch_index: int,
    stack_id: Optional[str],
    unit_id: str,
) -> str:
    payload = "|".join(
        (
            run_id,
            processing_mode,
            str(dispatch_index),
            stack_id or "",
            unit_id,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cancel_adapter(adapter: ExecutorAdapter, execution_id: str) -> None:
    cancel = getattr(adapter, "cancel", None)
    if callable(cancel):
        cancel(execution_id)


def _execute_once(
    adapter: ExecutorAdapter,
    request: ExecutorRequest,
    policy: RuntimePolicy,
    cancellation: RuntimeCancellation,
) -> Tuple[str, Optional[Mapping[str, Any]], Optional[str], float]:
    started = time.perf_counter()
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(adapter.execute, request)
    deadline = started + policy.timeout_ms / 1000.0
    try:
        while True:
            if cancellation.cancelled:
                _cancel_adapter(adapter, request.execution_id)
                future.cancel()
                return (
                    "cancelled",
                    None,
                    "cancelled",
                    (time.perf_counter() - started) * 1000.0,
                )
            remaining = deadline - time.perf_counter()
            if remaining <= 0.0:
                _cancel_adapter(adapter, request.execution_id)
                future.cancel()
                return (
                    "timeout",
                    None,
                    "timeout",
                    (time.perf_counter() - started) * 1000.0,
                )
            try:
                output = future.result(
                    timeout=min(
                        remaining,
                        policy.poll_interval_ms / 1000.0,
                    )
                )
            except TimeoutError:
                continue
            except RetryableExecutorError as error:
                return (
                    "retryable_error",
                    None,
                    error.code,
                    (time.perf_counter() - started) * 1000.0,
                )
            except PermanentExecutorError as error:
                return (
                    "permanent_error",
                    None,
                    error.code,
                    (time.perf_counter() - started) * 1000.0,
                )
            except Exception:
                return (
                    "permanent_error",
                    None,
                    "executor_error",
                    (time.perf_counter() - started) * 1000.0,
                )
            if not isinstance(output, Mapping):
                return (
                    "permanent_error",
                    None,
                    "invalid_executor_output",
                    (time.perf_counter() - started) * 1000.0,
                )
            return (
                "completed",
                dict(output),
                None,
                (time.perf_counter() - started) * 1000.0,
            )
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _pipeline(
    user_input: str,
    processing_mode: str,
    checkpoint: RuntimeCheckpoint,
) -> Mapping[str, Any]:
    if processing_mode == "vertical":
        state = process(
            user_input,
            processing_mode=processing_mode,
            vertical_outputs=checkpoint.vertical_outputs,
        )
    elif processing_mode == "hybrid":
        state = process(
            user_input,
            processing_mode=processing_mode,
            hybrid_outputs=checkpoint.hybrid_outputs,
        )
    else:
        state = process(user_input, processing_mode=processing_mode)
    return state.as_dict()


def _next_dispatch(
    pipeline_state: Mapping[str, Any],
    processing_mode: str,
    checkpoint: RuntimeCheckpoint,
) -> Tuple[
    Optional[Mapping[str, Optional[str]]],
    Optional[str],
    Optional[str],
]:
    if processing_mode == "horizontal":
        if checkpoint.horizontal_output is not None:
            return None, "completed", None
        return (
            {
                "stack_id": None,
                "unit_id": pipeline_state["llm_order"]["mode"],
            },
            None,
            None,
        )
    if processing_mode == "vertical":
        progress = pipeline_state["vertical_stack"]["progress"]
        if progress["status"] == "waiting":
            return (
                {
                    "stack_id": None,
                    "unit_id": progress["next_unit_id"],
                },
                None,
                None,
            )
        if progress["status"] == "completed":
            return None, "completed", None
        return None, "fallback", progress["stop_reason"]
    decision = pipeline_state["hybrid_stack_mesh"]
    if decision["status"] == "waiting":
        return decision["next_dispatch"], None, None
    if decision["status"] == "completed":
        return None, "completed", None
    return None, "fallback", decision["stop_reason"]


def _store_output(
    checkpoint: RuntimeCheckpoint,
    processing_mode: str,
    stack_id: Optional[str],
    unit_id: str,
    output: Mapping[str, Any],
) -> None:
    if processing_mode == "horizontal":
        checkpoint.horizontal_output = dict(output)
    elif processing_mode == "vertical":
        checkpoint.vertical_outputs[unit_id] = dict(output)
    else:
        if stack_id is None:
            raise ValueError("hybrid dispatch requires a stack id")
        checkpoint.hybrid_outputs.setdefault(stack_id, {})[unit_id] = dict(
            output
        )


def _last_failure_reason(checkpoint: RuntimeCheckpoint) -> str:
    if not checkpoint.records:
        return "retry_budget_exhausted"
    record = checkpoint.records[-1]
    return record.get("error_code") or record.get("status") or (
        "retry_budget_exhausted"
    )


def _session(
    status: str,
    stop_reason: Optional[str],
    started: float,
    pipeline_state: Mapping[str, Any],
    checkpoint: RuntimeCheckpoint,
    policy: RuntimePolicy,
) -> RuntimeSession:
    attempt_count = len(checkpoint.records)
    checkpoint.cumulative_elapsed_ms += (
        time.perf_counter() - started
    ) * 1000.0
    return RuntimeSession(
        status=status,
        run_id=checkpoint.run_id,
        processing_mode=checkpoint.processing_mode,
        stop_reason=stop_reason,
        elapsed_ms=checkpoint.cumulative_elapsed_ms,
        attempt_count=attempt_count,
        dispatch_count=checkpoint.completed_dispatch_count,
        estimated_cost_units=checkpoint.cumulative_estimated_cost_units,
        pipeline_state=pipeline_state,
        checkpoint=checkpoint,
        policy=policy,
    )


def run_with_executor(
    user_input: str,
    processing_mode: str,
    adapter: ExecutorAdapter,
    *,
    policy: RuntimePolicy = DEFAULT_RUNTIME_POLICY,
    checkpoint: Optional[RuntimeCheckpoint] = None,
    cancellation: Optional[RuntimeCancellation] = None,
    run_id: Optional[str] = None,
) -> RuntimeSession:
    if processing_mode not in _PROCESSING_MODES:
        raise ValueError(
            "processing_mode must be horizontal, vertical, or hybrid"
        )
    if not isinstance(user_input, str):
        raise ValueError("user_input must be a string")
    digest = _input_digest(user_input)
    if checkpoint is None:
        active_checkpoint = RuntimeCheckpoint(
            run_id=run_id or uuid.uuid4().hex,
            input_digest=digest,
            processing_mode=processing_mode,
        )
    else:
        if run_id is not None and run_id != checkpoint.run_id:
            raise ValueError("run_id does not match checkpoint")
        if checkpoint.input_digest != digest:
            raise ValueError("checkpoint input digest does not match")
        if checkpoint.processing_mode != processing_mode:
            raise ValueError("checkpoint processing mode does not match")
        active_checkpoint = checkpoint.clone()
    cancellation = cancellation or RuntimeCancellation()
    started = time.perf_counter()
    pipeline_state: Mapping[str, Any] = {}

    while True:
        pipeline_state = _pipeline(
            user_input,
            processing_mode,
            active_checkpoint,
        )
        dispatch, terminal_status, terminal_reason = _next_dispatch(
            pipeline_state,
            processing_mode,
            active_checkpoint,
        )
        if terminal_status is not None:
            return _session(
                terminal_status,
                terminal_reason,
                started,
                pipeline_state,
                active_checkpoint,
                policy,
            )
        if cancellation.cancelled:
            return _session(
                "cancelled",
                "cancelled",
                started,
                pipeline_state,
                active_checkpoint,
                policy,
            )
        if active_checkpoint.completed_dispatch_count >= (
            policy.max_dispatches
        ):
            return _session(
                "failed",
                "dispatch_budget_exhausted",
                started,
                pipeline_state,
                active_checkpoint,
                policy,
            )

        dispatch_index = active_checkpoint.completed_dispatch_count
        stack_id = dispatch["stack_id"]
        unit_id = dispatch["unit_id"]
        key = _idempotency_key(
            active_checkpoint.run_id,
            processing_mode,
            dispatch_index,
            stack_id,
            unit_id,
        )
        previous_attempts = active_checkpoint.attempts_by_key.get(key, 0)
        if previous_attempts >= policy.max_attempts:
            return _session(
                "failed",
                _last_failure_reason(active_checkpoint),
                started,
                pipeline_state,
                active_checkpoint,
                policy,
            )

        output = None
        for attempt in range(previous_attempts + 1, policy.max_attempts + 1):
            active_checkpoint.attempts_by_key[key] = attempt
            execution_id = f"{key}:{attempt}"
            request = ExecutorRequest(
                execution_id=execution_id,
                idempotency_key=key,
                run_id=active_checkpoint.run_id,
                processing_mode=processing_mode,
                dispatch_index=dispatch_index,
                attempt=attempt,
                stack_id=stack_id,
                unit_id=unit_id,
                timeout_ms=policy.timeout_ms,
                llm_order=pipeline_state["llm_order"],
            )
            result_status, candidate_output, error_code, elapsed_ms = (
                _execute_once(adapter, request, policy, cancellation)
            )
            active_checkpoint.records.append(
                {
                    "dispatch_index": dispatch_index,
                    "attempt": attempt,
                    "idempotency_key": key,
                    "execution_id": execution_id,
                    "stack_id": stack_id,
                    "unit_id": unit_id,
                    "status": result_status,
                    "error_code": error_code,
                    "elapsed_ms": round(elapsed_ms, 3),
                }
            )
            active_checkpoint.cumulative_estimated_cost_units += (
                policy.estimated_cost_units_per_attempt
            )
            if result_status == "completed":
                output = candidate_output
                break
            if result_status == "cancelled":
                return _session(
                    "cancelled",
                    "cancelled",
                    started,
                    pipeline_state,
                    active_checkpoint,
                    policy,
                )
            if result_status not in policy.retry_on:
                return _session(
                    "failed",
                    error_code or result_status,
                    started,
                    pipeline_state,
                    active_checkpoint,
                    policy,
                )
        if output is None:
            return _session(
                "failed",
                _last_failure_reason(active_checkpoint),
                started,
                pipeline_state,
                active_checkpoint,
                policy,
            )
        _store_output(
            active_checkpoint,
            processing_mode,
            stack_id,
            unit_id,
            output,
        )
