import json
from pathlib import Path

from semantic_routing import evaluate_plm_extractor, load_plm_benchmark, parse_plm_benchmark, route


ROOT = Path(__file__).parents[1]
REPORT_PATH = ROOT / "build" / "v5_nonsealed_replay_gate_report.json"
VISIBLE_PLM_PATH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
V5_CHALLENGE_PATH = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _v5_benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v5 nonsealed replay gate",
        "review_status": fixture["review_status"],
        "policy": "non-sealed diagnostic replay; no sealed labels used",
        "cases": [
            {
                "id": case["id"],
                "split": case["split"],
                "source_group": case["source_group"],
                "contrast_group": None,
                "language": case["language"],
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in fixture["cases"]
        ],
    }


def test_v5_nonsealed_replay_gate_passes_all_lanes() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v5-nonsealed-replay-gate-report.v1"
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_v4_text_used": False,
        "sealed_v4_labels_used": False,
        "active_sealed_v5_required_before_adjudication": True,
        "same_cycle_promotion_allowed": False,
        "current_route_measurement_is_gate": True,
    }
    assert report["summary"] == {
        "lane_count": 4,
        "passed_lane_count": 4,
        "failed_lanes": [],
        "ready_for_step6_sealed_v5_rotation": True,
    }

    lanes = report["lanes"]
    assert set(lanes) == {
        "visible_plm",
        "v4_failure_memory_replay",
        "v4_puzzle_failure_memory_preservation",
        "v5_nonsealed_challenge",
    }
    assert all(lane["passed"] is True for lane in lanes.values())
    assert lanes["visible_plm"]["sealed_split_evaluated"] is False
    assert lanes["visible_plm"]["measurement"]["error_count"] == 0
    assert lanes["v4_failure_memory_replay"]["measurement"]["exact_match_rate"] == 1.0
    assert lanes["v4_failure_memory_replay"]["measurement"]["guard_subset_match_rate"] == 1.0
    assert lanes["v4_puzzle_failure_memory_preservation"]["measurement"]["success_traces_promoted"] is False
    assert lanes["v4_puzzle_failure_memory_preservation"]["measurement"]["policy_ok"] is True
    assert lanes["v5_nonsealed_challenge"]["measurement"]["error_count"] == 0
    assert report["next_step"] == {
        "step": 6,
        "name": "sealed_v5_rotation",
        "output": "tests\\fixtures\\pattern_language_sealed_v5.json",
    }


def test_v5_nonsealed_replay_gate_visible_and_challenge_match_current_route() -> None:
    report = _load(REPORT_PATH)
    visible = load_plm_benchmark(VISIBLE_PLM_PATH).cases_for_splits(("train", "validation"))
    visible_measurement = evaluate_plm_extractor(
        visible,
        lambda text: route(text).packet,
    )
    visible_report = report["lanes"]["visible_plm"]["measurement"]

    assert visible_measurement["case_count"] == visible_report["case_count"]
    assert visible_measurement["intent_accuracy"] == visible_report["intent_accuracy"]
    assert visible_measurement["critical_signal_recall"] == visible_report["critical_signal_recall"]
    assert visible_measurement["operation_exact_match"] == visible_report["operation_exact_match"]
    assert visible_measurement["constraint_exact_match"] == visible_report["constraint_exact_match"]
    assert visible_measurement["risk_exact_match"] == visible_report["risk_exact_match"]
    assert len(visible_measurement["errors"]) == visible_report["error_count"]

    fixture = _load(V5_CHALLENGE_PATH)
    challenge = parse_plm_benchmark(_v5_benchmark_payload(fixture))
    challenge_measurement = evaluate_plm_extractor(
        challenge.cases,
        lambda text: route(text).packet,
    )
    challenge_report = report["lanes"]["v5_nonsealed_challenge"]["measurement"]

    assert challenge_measurement["case_count"] == challenge_report["case_count"]
    assert challenge_measurement["intent_accuracy"] == challenge_report["intent_accuracy"]
    assert challenge_measurement["critical_signal_recall"] == challenge_report["critical_signal_recall"]
    assert challenge_measurement["operation_exact_match"] == challenge_report["operation_exact_match"]
    assert challenge_measurement["constraint_exact_match"] == challenge_report["constraint_exact_match"]
    assert challenge_measurement["risk_exact_match"] == challenge_report["risk_exact_match"]
    assert len(challenge_measurement["errors"]) == challenge_report["error_count"]