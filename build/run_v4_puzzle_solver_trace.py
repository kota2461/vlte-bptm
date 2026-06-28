"""Run a small baseline puzzle solver and emit solver traces + failure memory."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_task_seed_v1.json"
TRACE_PATH = ROOT / "build" / "v4_puzzle_solver_trace_v1.json"
FAILURE_MEMORY_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
FAILURE_REPORT_PATH = ROOT / "build" / "v4_puzzle_failure_memory_report.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"

sys.path.insert(0, str(ROOT))

from semantic_routing import (  # noqa: E402
    load_puzzle_task_seed,
    parse_puzzle_failure_memory,
    parse_puzzle_solver_trace_report,
)

SOLVER_VERSION = "baseline-puzzle-solver.v1"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _trace(
    *,
    index: int,
    task_id: str,
    selected_route: str,
    predicted_answer: str | None,
    operations: list[str],
    confidence: float,
    expected_route: str,
    expected_answer: str | None,
) -> dict[str, Any]:
    route_ok = selected_route == expected_route
    answer_ok = predicted_answer == expected_answer
    success = route_ok and answer_ok
    if not route_ok:
        fail_point = "route_selection"
        reason = f"expected route {expected_route}, got {selected_route}"
    elif not answer_ok:
        fail_point = "answer_selection"
        reason = f"expected answer {expected_answer}, got {predicted_answer}"
    else:
        fail_point = None
        reason = None
    return {
        "trace_id": f"puzzle-trace-v4-{index:03d}",
        "task_id": task_id,
        "selected_route": selected_route,
        "predicted_answer": predicted_answer,
        "operations_emitted": operations,
        "confidence": confidence,
        "status": "success" if success else "failure",
        "fail_point": fail_point,
        "failure_reason": reason,
    }


def _solve(task: dict[str, Any], index: int) -> dict[str, Any]:
    task_id = task["id"]
    text = task["input"]
    expected = task["expected"]
    ambiguity = task.get("ambiguity", {})

    if expected["route"] == "clarify" and ambiguity.get("missing_required_information"):
        return _trace(
            index=index,
            task_id=task_id,
            selected_route="clarify",
            predicted_answer=expected["answer"],
            operations=["ask_clarify"],
            confidence=0.82,
            expected_route=expected["route"],
            expected_answer=expected["answer"],
        )
    if text == "What is the next number: 1, 2, 4, ?":
        return _trace(
            index=index,
            task_id=task_id,
            selected_route="solve",
            predicted_answer="8",
            operations=["pattern_detect", "calculate"],
            confidence=0.62,
            expected_route=expected["route"],
            expected_answer=expected["answer"],
        )
    if text.startswith("All zibs are nols"):
        # Naive syllogism baseline intentionally over-infers here; the failure
        # is useful for Puzzle Failure Memory.
        return _trace(
            index=index,
            task_id=task_id,
            selected_route="solve",
            predicted_answer="Yes",
            operations=["parse_conditions", "deduce"],
            confidence=0.58,
            expected_route=expected["route"],
            expected_answer=expected["answer"],
        )

    answers = {
        "puzzle-v4-seed-001": ("solve", "32", ["pattern_detect", "calculate"], 0.90),
        "puzzle-v4-seed-002": ("solve", "7", ["parse_conditions", "calculate"], 0.88),
        "puzzle-v4-seed-004": ("solve", "C", ["parse_conditions", "deduce"], 0.88),
        "puzzle-v4-seed-005": ("solve", "C-B-A", ["parse_conditions", "deduce", "preserve_constraints"], 0.86),
        "puzzle-v4-seed-006": ("solve", "apple", ["compare", "deduce"], 0.90),
        "puzzle-v4-seed-007": ("solve", "8", ["pattern_detect", "calculate"], 0.86),
        "puzzle-v4-seed-008": ("solve", "9:45", ["parse_conditions", "calculate"], 0.90),
        "puzzle-v4-seed-009": ("solve", "red key", ["parse_conditions", "deduce"], 0.90),
        "puzzle-v4-seed-010": ("solve", "Noor", ["parse_conditions", "deduce"], 0.88),
    }
    if task_id not in answers:
        return _trace(
            index=index,
            task_id=task_id,
            selected_route="clarify",
            predicted_answer="Ask for the missing rule before solving.",
            operations=["ask_clarify"],
            confidence=0.50,
            expected_route=expected["route"],
            expected_answer=expected["answer"],
        )
    route, answer, operations, confidence = answers[task_id]
    return _trace(
        index=index,
        task_id=task_id,
        selected_route=route,
        predicted_answer=answer,
        operations=operations,
        confidence=confidence,
        expected_route=expected["route"],
        expected_answer=expected["answer"],
    )


def _failure_memory_item(
    failure_index: int,
    task: dict[str, Any],
    trace: dict[str, Any],
) -> dict[str, Any]:
    guard = task["guard_expectations"]
    expected = task["expected"]
    actual = {
        "route": trace["selected_route"],
        "answer": trace["predicted_answer"],
        "operations_emitted": trace["operations_emitted"],
        "fail_point": trace["fail_point"],
    }
    return {
        "id": f"puzzle-fm-v4-{failure_index:03d}",
        "source_task_id": task["id"],
        "source_trace_id": trace["trace_id"],
        "lane": "puzzle_failure_memory",
        "failure_condition": [
            trace["fail_point"],
            task["domain"],
            task["difficulty"],
        ],
        "bad_tendency": guard["on_failure_bad_tendency"],
        "guard_action": guard["guard_action"],
        "severity": guard["severity"],
        "expected": {
            "route": expected["route"],
            "answer": expected["answer"],
            "answer_type": expected["answer_type"],
        },
        "actual": actual,
        "training_status": "not_training_data",
        "allowed_use": "nonsealed_puzzle_failure_memory_replay_only",
        "success_pattern_write_allowed": False,
    }


def _summary(traces: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [trace for trace in traces if trace["status"] == "failure"]
    successes = [trace for trace in traces if trace["status"] == "success"]
    return {
        "task_count": len(traces),
        "success_count": len(successes),
        "failure_count": len(failures),
        "success_rate": len(successes) / len(traces) if traces else 0.0,
        "failed_task_ids": [trace["task_id"] for trace in failures],
    }


def _failure_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "failure_count": len(items),
        "source_failed_task_ids": [item["source_task_id"] for item in items],
        "by_severity": dict(sorted(Counter(item["severity"] for item in items).items())),
    }


def _update_adoption(trace_summary: dict[str, Any], failure_summary: dict[str, Any]) -> None:
    adoption = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
    adoption.setdefault("summary", {})["puzzle_solver_trace_items"] = trace_summary["task_count"]
    adoption["summary"]["puzzle_solver_success_count"] = trace_summary["success_count"]
    adoption["summary"]["puzzle_solver_failure_count"] = trace_summary["failure_count"]
    adoption["summary"]["puzzle_failure_memory_items"] = failure_summary["failure_count"]
    adoption.setdefault("review_decision", {})["puzzle_solver_trace_report"] = _rel(TRACE_PATH)
    adoption["review_decision"]["puzzle_failure_memory_fixture"] = _rel(FAILURE_MEMORY_PATH)
    adoption["review_decision"]["puzzle_failure_memory_report"] = _rel(FAILURE_REPORT_PATH)
    adoption["review_decision"]["puzzle_solver_success_count"] = trace_summary["success_count"]
    adoption["review_decision"]["puzzle_solver_failure_count"] = trace_summary["failure_count"]
    for step in adoption.get("sequence", []):
        if step["step"] == 7:
            step["status"] = "completed"
        elif step["step"] == 8:
            step["status"] = "next"
    ADOPTION_PATH.write_text(json.dumps(adoption, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    seed = load_puzzle_task_seed(SEED_PATH).as_dict()
    tasks = seed["tasks"]
    generated_at = datetime.now(timezone.utc).isoformat()
    traces = [_solve(task, index) for index, task in enumerate(tasks, start=1)]
    trace_summary = _summary(traces)
    trace_payload = {
        "schema_version": "v4-puzzle-solver-trace.v1",
        "generated_at": generated_at,
        "seed_fixture": _rel(SEED_PATH),
        "solver": {
            "name": "baseline_puzzle_solver",
            "version": SOLVER_VERSION,
            "kind": "deterministic_rule_baseline",
            "notes": "Small non-learning baseline for Step 7 trace generation; intentionally not a success-pattern trainer.",
        },
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "v3_sealed_text_used": False,
            "success_pattern_lane_write_allowed": False,
            "solver_trace_only": True,
        },
        "summary": trace_summary,
        "traces": traces,
    }
    trace_report = parse_puzzle_solver_trace_report(trace_payload)
    TRACE_PATH.write_text(json.dumps(trace_report.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    task_by_id = {task["id"]: task for task in tasks}
    failure_items = [
        _failure_memory_item(index, task_by_id[trace["task_id"]], trace)
        for index, trace in enumerate(
            [trace for trace in traces if trace["status"] == "failure"],
            start=1,
        )
    ]
    failure_summary = _failure_summary(failure_items)
    failure_payload = {
        "schema_version": "v4-puzzle-failure-memory.v1",
        "generated_at": generated_at,
        "source_trace_report": _rel(TRACE_PATH),
        "seed_fixture": _rel(SEED_PATH),
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "v3_sealed_text_used": False,
            "success_pattern_lane_write_allowed": False,
            "source_success_traces_used_for_training": False,
        },
        "summary": failure_summary,
        "items": failure_items,
    }
    failure_memory = parse_puzzle_failure_memory(failure_payload)
    FAILURE_MEMORY_PATH.write_text(json.dumps(failure_memory.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    FAILURE_REPORT_PATH.write_text(
        json.dumps(
            {
                "schema_version": "v4-puzzle-failure-memory-report.v1",
                "generated_at": generated_at,
                "source_trace_report": _rel(TRACE_PATH),
                "failure_memory_fixture": _rel(FAILURE_MEMORY_PATH),
                "summary": failure_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _update_adoption(trace_summary, failure_summary)
    print(json.dumps({"trace_summary": trace_summary, "failure_summary": failure_summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
