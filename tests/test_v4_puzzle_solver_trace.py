import copy
import json
from pathlib import Path

import pytest

from semantic_routing import (
    load_puzzle_failure_memory,
    load_puzzle_solver_trace_report,
    parse_puzzle_failure_memory,
    parse_puzzle_solver_trace_report,
)


ROOT = Path(__file__).parents[1]
TRACE_PATH = ROOT / "build" / "v4_puzzle_solver_trace_v1.json"
FAILURE_MEMORY_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
FAILURE_REPORT_PATH = ROOT / "build" / "v4_puzzle_failure_memory_report.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"
FAILED_TASK_IDS = ["puzzle-v4-seed-003", "puzzle-v4-seed-011"]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v4_puzzle_solver_trace_contract_is_observation_only() -> None:
    report = load_puzzle_solver_trace_report(TRACE_PATH)
    payload = report.as_dict()

    assert payload["schema_version"] == "v4-puzzle-solver-trace.v1"
    assert payload["policy"]["sealed_fixtures_used_as_sources"] is False
    assert payload["policy"]["v3_sealed_text_used"] is False
    assert payload["policy"]["success_pattern_lane_write_allowed"] is False
    assert payload["policy"]["solver_trace_only"] is True
    assert payload["summary"]["task_count"] == 12
    assert payload["summary"]["success_count"] == 10
    assert payload["summary"]["failure_count"] == 2
    assert payload["summary"]["success_rate"] == pytest.approx(10 / 12)
    assert payload["summary"]["failed_task_ids"] == FAILED_TASK_IDS

    failures = [trace for trace in payload["traces"] if trace["status"] == "failure"]
    assert [trace["task_id"] for trace in failures] == FAILED_TASK_IDS
    assert all(trace["failure_reason"] for trace in failures)
    assert all(trace["operations_emitted"] for trace in payload["traces"])


def test_v4_puzzle_failure_memory_contract_keeps_only_failures() -> None:
    memory = load_puzzle_failure_memory(FAILURE_MEMORY_PATH)
    payload = memory.as_dict()

    assert payload["schema_version"] == "v4-puzzle-failure-memory.v1"
    assert payload["source_trace_report"] == r"build\v4_puzzle_solver_trace_v1.json"
    assert payload["policy"]["sealed_fixtures_used_as_sources"] is False
    assert payload["policy"]["v3_sealed_text_used"] is False
    assert payload["policy"]["success_pattern_lane_write_allowed"] is False
    assert payload["policy"]["source_success_traces_used_for_training"] is False
    assert payload["summary"]["failure_count"] == 2
    assert payload["summary"]["source_failed_task_ids"] == FAILED_TASK_IDS

    assert [item["source_task_id"] for item in payload["items"]] == FAILED_TASK_IDS
    for item in payload["items"]:
        assert item["lane"] == "puzzle_failure_memory"
        assert item["training_status"] == "not_training_data"
        assert item["allowed_use"] == "nonsealed_puzzle_failure_memory_replay_only"
        assert item["success_pattern_write_allowed"] is False
        assert item["bad_tendency"]
        assert item["guard_action"]
        assert item["actual"]["fail_point"]


def test_v4_puzzle_solver_and_failure_memory_parsers_reject_contract_drift() -> None:
    trace_payload = _load(TRACE_PATH)
    mutated_trace = copy.deepcopy(trace_payload)
    mutated_trace["traces"][0]["raw_prompt"] = "not allowed"
    with pytest.raises(ValueError, match="unknown field"):
        parse_puzzle_solver_trace_report(mutated_trace)

    mutated_trace = copy.deepcopy(trace_payload)
    mutated_trace["policy"]["success_pattern_lane_write_allowed"] = True
    with pytest.raises(ValueError, match="success patterns"):
        parse_puzzle_solver_trace_report(mutated_trace)

    memory_payload = _load(FAILURE_MEMORY_PATH)
    mutated_memory = copy.deepcopy(memory_payload)
    mutated_memory["policy"]["source_success_traces_used_for_training"] = True
    with pytest.raises(ValueError, match="success traces"):
        parse_puzzle_failure_memory(mutated_memory)

    mutated_memory = copy.deepcopy(memory_payload)
    mutated_memory["items"][0]["success_pattern_write_allowed"] = True
    with pytest.raises(ValueError, match="success patterns"):
        parse_puzzle_failure_memory(mutated_memory)


def test_v4_puzzle_failure_report_and_adoption_registry_mark_step7_complete() -> None:
    report = _load(FAILURE_REPORT_PATH)
    adoption = _load(ADOPTION_PATH)

    assert report["schema_version"] == "v4-puzzle-failure-memory-report.v1"
    assert report["source_trace_report"] == r"build\v4_puzzle_solver_trace_v1.json"
    assert report["failure_memory_fixture"] == r"tests\fixtures\v4_puzzle_failure_memory_v1.json"
    assert report["summary"]["failure_count"] == 2
    assert report["summary"]["source_failed_task_ids"] == FAILED_TASK_IDS

    steps = {step["step"]: step["status"] for step in adoption["sequence"]}
    assert steps[7] == "completed"
    assert steps[8] == "completed"
    assert adoption["summary"]["puzzle_solver_trace_items"] == 12
    assert adoption["summary"]["puzzle_solver_success_count"] == 10
    assert adoption["summary"]["puzzle_solver_failure_count"] == 2
    assert adoption["summary"]["puzzle_failure_memory_items"] == 2
    assert adoption["review_decision"]["puzzle_solver_trace_report"] == r"build\v4_puzzle_solver_trace_v1.json"
    assert adoption["review_decision"]["puzzle_failure_memory_fixture"] == r"tests\fixtures\v4_puzzle_failure_memory_v1.json"
    assert adoption["review_decision"]["puzzle_failure_memory_report"] == r"build\v4_puzzle_failure_memory_report.json"
