import copy
import json
from pathlib import Path

import pytest

from semantic_routing import load_puzzle_task_seed, parse_puzzle_task_seed


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_task_seed_v1.json"
REPORT_PATH = ROOT / "build" / "v4_puzzle_task_seed_report.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v4_puzzle_task_seed_contract_is_nonsealed() -> None:
    seed = load_puzzle_task_seed(FIXTURE_PATH)
    payload = seed.as_dict()

    assert payload["schema_version"] == "v4-puzzle-task-seed.v1"
    assert payload["status"] == "draft_seed"
    assert payload["policy"]["sealed_fixtures_used_as_sources"] is False
    assert payload["policy"]["v3_sealed_text_used"] is False
    assert payload["policy"]["success_pattern_lane_write_allowed"] is False
    assert payload["policy"]["failures_enter_failure_memory_first"] is True
    assert payload["policy"]["same_cycle_promotion_allowed"] is False
    assert payload["summary"]["task_count"] == 12
    assert payload["summary"]["by_expected_route"] == {"clarify": 2, "solve": 10}

    for task in payload["tasks"]:
        assert task["training_status"] == "not_training_data"
        assert task["allowed_use"] == "nonsealed_puzzle_seed_replay_only"
        assert task["review_status"] == "draft"
        assert task["guard_expectations"]["guard_action"]
        assert task["allowed_reasoning_operations"]


def test_v4_puzzle_task_seed_has_clarify_cases_for_ambiguous_or_missing_puzzles() -> None:
    payload = _load(FIXTURE_PATH)
    clarify_tasks = [
        task for task in payload["tasks"]
        if task["expected"]["route"] == "clarify"
    ]

    assert len(clarify_tasks) == 2
    assert any(task["ambiguity"]["ambiguous"] for task in clarify_tasks)
    assert any(
        task["ambiguity"]["missing_required_information"]
        for task in clarify_tasks
    )
    for task in clarify_tasks:
        assert task["expected"]["answer_type"] == "clarification"
        assert "ask_clarify" in task["allowed_reasoning_operations"]
        assert "ask_clarify" in task["guard_expectations"]["guard_action"]


def test_v4_puzzle_task_seed_parser_rejects_success_lane_or_unknown_fields() -> None:
    payload = _load(FIXTURE_PATH)
    mutated = copy.deepcopy(payload)
    mutated["tasks"][0]["raw_prompt"] = mutated["tasks"][0]["input"]
    with pytest.raises(ValueError, match="unknown field"):
        parse_puzzle_task_seed(mutated)

    mutated = copy.deepcopy(payload)
    mutated["policy"]["success_pattern_lane_write_allowed"] = True
    with pytest.raises(ValueError, match="success patterns"):
        parse_puzzle_task_seed(mutated)

    mutated = copy.deepcopy(payload)
    mutated["tasks"][10]["expected"]["route"] = "solve"
    with pytest.raises(ValueError, match="ambiguous/missing"):
        parse_puzzle_task_seed(mutated)


def test_v4_puzzle_seed_report_and_adoption_registry_record_step6_seed() -> None:
    fixture = _load(FIXTURE_PATH)
    report = _load(REPORT_PATH)
    adoption = _load(ADOPTION_PATH)

    assert report["schema_version"] == "v4-puzzle-task-seed-report.v1"
    assert report["policy"]["sealed_fixtures_used_as_sources"] is False
    assert report["policy"]["success_pattern_lane_write_allowed"] is False
    assert report["policy"]["solver_trace_generated"] is False
    assert report["summary"] == fixture["summary"]

    steps = {step["step"]: step["status"] for step in adoption["sequence"]}
    assert steps[6] == "completed"
    assert steps[7] == "completed"
    assert steps[8] == "completed"
    assert adoption["summary"]["puzzle_task_seed_items"] == 12
    assert adoption["summary"]["puzzle_task_seed_clarify_items"] == 2
    assert adoption["review_decision"]["puzzle_task_seed_fixture"] == (
        "tests\\fixtures\\v4_puzzle_task_seed_v1.json"
    )
    assert adoption["review_decision"]["puzzle_task_seed_report"] == (
        "build\\v4_puzzle_task_seed_report.json"
    )
