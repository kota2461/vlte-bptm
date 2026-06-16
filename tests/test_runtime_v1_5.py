import json
import subprocess
import sys
import time
from pathlib import Path
from threading import Timer

import pytest

from thought_core.runtime import (
    DEFAULT_EXECUTOR_POLICY_PATH,
    EXECUTOR_POLICY_SCHEMA_VERSION,
    RUNTIME_SESSION_SCHEMA_VERSION,
    RetryableExecutorError,
    RuntimeCancellation,
    RuntimePolicy,
    load_runtime_policy,
    run_with_executor,
)
from thought_core.runtime_evaluation import (
    RUNTIME_EVALUATION_REPORT_SCHEMA_VERSION,
    evaluate_runtime_fixture,
)
from thought_core.vertical_stack import load_vertical_stack_config


ROOT = Path(__file__).parents[1]
EXECUTOR_POLICY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_5_executor_policy.json"
)
RUNTIME_EVALUATION_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_5_runtime_evaluation.json"
)


def _unit_output(unit_id: str, **overrides) -> dict:
    config = load_vertical_stack_config()
    fields = {
        "schema_version": config.output_contracts[unit_id].schema_version,
        "unit_id": unit_id,
        "status": "completed",
        "assumptions": [],
        "evidence": [],
    }
    unit_fields = {
        "verify": {
            "verified": True,
            "verified_assumptions": [],
            "risk_flags": [],
        },
        "build": {"implementation_plan": {"steps": ["edit", "test"]}},
        "summarize": {"summary": "summary-private-marker"},
        "explore": {"hypotheses": ["option-a"]},
        "clarify": {
            "needs_clarification": False,
            "questions": [],
        },
        "respond": {"response": "response-private-marker"},
    }
    fields.update(unit_fields[unit_id])
    fields.update(overrides)
    return fields


class RecordingAdapter:
    def __init__(self, handler=None) -> None:
        self.handler = handler or (
            lambda request: _unit_output(request.unit_id)
        )
        self.requests = []
        self.cancelled = []

    def execute(self, request):
        self.requests.append(request)
        return self.handler(request)

    def cancel(self, execution_id: str) -> None:
        self.cancelled.append(execution_id)


def _policy(**overrides) -> RuntimePolicy:
    values = {
        "timeout_ms": 500,
        "poll_interval_ms": 5,
        "max_attempts": 2,
        "max_dispatches": 4,
        "retry_on": ("retryable_error", "timeout"),
        "estimated_cost_units_per_attempt": 1.0,
    }
    values.update(overrides)
    return RuntimePolicy(**values)


def test_executor_policy_matches_v1_5_fixture() -> None:
    fixture = json.loads(
        EXECUTOR_POLICY_FIXTURE.read_text(encoding="utf-8")
    )
    policy = load_runtime_policy()

    assert DEFAULT_EXECUTOR_POLICY_PATH.is_file()
    assert fixture["schema_version"] == EXECUTOR_POLICY_SCHEMA_VERSION
    assert policy.as_dict() == fixture


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update(schema_version="unknown"),
            "unsupported",
        ),
        (
            lambda payload: payload.update(poll_interval_ms=6000),
            "cannot exceed",
        ),
        (
            lambda payload: payload.update(retry_on=["permanent_error"]),
            "unsupported retry",
        ),
        (
            lambda payload: payload.update(
                estimated_cost_units_per_attempt=-1
            ),
            "non-negative",
        ),
        (
            lambda payload: payload.update(max_attempts=6),
            "cannot exceed",
        ),
        (
            lambda payload: payload.update(private_output="forbidden"),
            "fields do not match",
        ),
    ],
)
def test_executor_policy_rejects_unsafe_config(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(
        DEFAULT_EXECUTOR_POLICY_PATH.read_text(encoding="utf-8")
    )
    mutate(payload)
    path = tmp_path / "bad-runtime-policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_runtime_policy(path)


def test_runtime_completes_vertical_stack_without_echoing_outputs() -> None:
    marker = "implementation-private-marker-551"

    def handler(request):
        if request.unit_id == "build":
            return _unit_output(
                "build",
                implementation_plan={"private": marker},
            )
        return _unit_output(request.unit_id)

    adapter = RecordingAdapter(handler)
    session = run_with_executor(
        "Please implement and build this feature",
        "vertical",
        adapter,
        policy=_policy(),
        run_id="vertical-run",
    )
    payload = session.as_dict()

    assert payload["schema_version"] == RUNTIME_SESSION_SCHEMA_VERSION
    assert session.status == "completed"
    assert session.dispatch_count == 2
    assert session.attempt_count == 2
    assert [request.unit_id for request in adapter.requests] == [
        "verify",
        "build",
    ]
    assert "summary-private-marker" not in json.dumps(payload)
    assert marker not in json.dumps(payload)
    assert session.checkpoint.as_dict()["contains_private_outputs"] is True
    assert "private_outputs" not in session.checkpoint.as_dict()


def test_runtime_retries_with_same_idempotency_key() -> None:
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RetryableExecutorError("temporary", "temporary_failure")
        return _unit_output(request.unit_id)

    adapter = RecordingAdapter(handler)
    session = run_with_executor(
        "Hello",
        "horizontal",
        adapter,
        policy=_policy(),
        run_id="retry-run",
    )

    assert session.status == "completed"
    assert session.attempt_count == 2
    assert adapter.requests[0].idempotency_key == (
        adapter.requests[1].idempotency_key
    )
    assert adapter.requests[0].execution_id != (
        adapter.requests[1].execution_id
    )


def test_runtime_timeout_calls_cancel_and_stops_after_budget() -> None:
    def handler(_request):
        time.sleep(0.05)
        return {"late": True}

    adapter = RecordingAdapter(handler)
    session = run_with_executor(
        "Hello",
        "horizontal",
        adapter,
        policy=_policy(
            timeout_ms=10,
            poll_interval_ms=2,
            max_attempts=1,
        ),
        run_id="timeout-run",
    )

    assert session.status == "failed"
    assert session.stop_reason == "timeout"
    assert session.attempt_count == 1
    assert adapter.cancelled == [adapter.requests[0].execution_id]


def test_runtime_observes_cancellation_during_dispatch() -> None:
    def handler(_request):
        time.sleep(0.05)
        return {"late": True}

    adapter = RecordingAdapter(handler)
    cancellation = RuntimeCancellation()
    timer = Timer(0.01, cancellation.cancel)
    timer.start()
    try:
        session = run_with_executor(
            "Hello",
            "horizontal",
            adapter,
            policy=_policy(timeout_ms=200),
            cancellation=cancellation,
            run_id="cancel-run",
        )
    finally:
        timer.cancel()

    assert session.status == "cancelled"
    assert session.stop_reason == "cancelled"
    assert adapter.cancelled == [adapter.requests[0].execution_id]


def test_runtime_resumes_without_redispatching_completed_unit() -> None:
    first_adapter = RecordingAdapter()
    interrupted = run_with_executor(
        "Please implement and build this feature",
        "vertical",
        first_adapter,
        policy=_policy(max_dispatches=1),
        run_id="resume-run",
    )

    assert interrupted.status == "failed"
    assert interrupted.stop_reason == "dispatch_budget_exhausted"
    assert [request.unit_id for request in first_adapter.requests] == [
        "verify"
    ]

    resumed_adapter = RecordingAdapter()
    resumed = run_with_executor(
        "Please implement and build this feature",
        "vertical",
        resumed_adapter,
        policy=_policy(
            max_dispatches=4,
            estimated_cost_units_per_attempt=3.0,
        ),
        checkpoint=interrupted.checkpoint,
    )

    assert resumed.status == "completed"
    assert [request.unit_id for request in resumed_adapter.requests] == [
        "build"
    ]
    assert resumed.dispatch_count == 2
    assert resumed.attempt_count == 2
    assert resumed.estimated_cost_units == pytest.approx(4.0)


def test_runtime_rejects_checkpoint_for_different_input_or_mode() -> None:
    session = run_with_executor(
        "Hello",
        "horizontal",
        RecordingAdapter(),
        policy=_policy(),
        run_id="checkpoint-run",
    )

    with pytest.raises(ValueError, match="input digest"):
        run_with_executor(
            "Different",
            "horizontal",
            RecordingAdapter(),
            checkpoint=session.checkpoint,
        )
    with pytest.raises(ValueError, match="processing mode"):
        run_with_executor(
            "Hello",
            "vertical",
            RecordingAdapter(),
            checkpoint=session.checkpoint,
        )


def test_runtime_hybrid_continues_with_alternative_after_failed_verify() -> None:
    def handler(request):
        if request.unit_id == "verify":
            return _unit_output(
                "verify",
                verified=False,
                risk_flags=["missing evidence"],
            )
        return _unit_output(request.unit_id)

    adapter = RecordingAdapter(handler)
    session = run_with_executor(
        "Please implement and build this feature, then summarize it",
        "hybrid",
        adapter,
        policy=_policy(),
        run_id="hybrid-alternative-run",
    )

    assert session.status == "completed"
    assert [request.unit_id for request in adapter.requests] == [
        "verify",
        "summarize",
    ]
    decision = session.pipeline_state["hybrid_stack_mesh"]
    assert decision["winning_stack_id"] == "summarize"


def test_runtime_invalid_output_falls_back_without_echoing_body() -> None:
    marker = "executor-private-marker-991"
    adapter = RecordingAdapter(lambda _request: {"body": marker})
    session = run_with_executor(
        "Please implement and build this feature",
        "vertical",
        adapter,
        policy=_policy(),
        run_id="invalid-output-run",
    )
    payload = json.dumps(session.as_dict())

    assert session.status == "fallback"
    assert session.stop_reason == "invalid_output_contract"
    assert marker not in payload


def test_runtime_evaluation_fixture_reports_blind_tradeoffs() -> None:
    fixture = json.loads(
        RUNTIME_EVALUATION_FIXTURE.read_text(encoding="utf-8")
    )
    report = evaluate_runtime_fixture(fixture)

    assert report["schema_version"] == (
        RUNTIME_EVALUATION_REPORT_SCHEMA_VERSION
    )
    assert report["case_count"] == 4
    assert report["privacy"] == {
        "raw_output_stored": False,
        "automatic_learning": False,
        "candidate_mode_hidden_during_scoring": True,
    }
    assert report["mode_metrics"]["horizontal"][
        "quality_score_mean"
    ] == pytest.approx(3.75)
    assert report["mode_metrics"]["vertical"][
        "quality_score_mean"
    ] == pytest.approx(4.35)
    assert report["mode_metrics"]["hybrid"][
        "quality_score_mean"
    ] == pytest.approx(4.7)
    assert report["comparisons"][
        "hybrid_quality_gain_over_horizontal"
    ] == pytest.approx(0.95)
    assert report["comparisons"][
        "runtime_selection_human_agreement"
    ] == pytest.approx(0.75)
    assert report["comparisons"][
        "hybrid_stack_winner_human_agreement"
    ] == pytest.approx(0.75)


def test_runtime_evaluation_rejects_unblinded_candidate() -> None:
    fixture = json.loads(
        RUNTIME_EVALUATION_FIXTURE.read_text(encoding="utf-8")
    )
    fixture["cases"][0]["candidates"][0]["mode"] = "horizontal"

    with pytest.raises(ValueError, match="candidate fields"):
        evaluate_runtime_fixture(fixture)


def test_runtime_evaluation_rejects_unknown_fixture_field() -> None:
    fixture = json.loads(
        RUNTIME_EVALUATION_FIXTURE.read_text(encoding="utf-8")
    )
    fixture["raw_output"] = "forbidden"

    with pytest.raises(ValueError, match="fixture fields"):
        evaluate_runtime_fixture(fixture)


def test_runtime_evaluation_cli() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core.runtime_evaluation",
            "--input-file",
            str(RUNTIME_EVALUATION_FIXTURE),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    report = json.loads(completed.stdout)

    assert report["case_count"] == 4
    assert report["privacy"]["automatic_learning"] is False
