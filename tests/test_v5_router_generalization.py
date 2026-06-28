import json
from pathlib import Path

from semantic_routing import evaluate_plm_extractor
from semantic_routing.adapter import route
from semantic_routing.benchmark import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v5_router_generalization_report.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v5 step4 generalization",
        "review_status": fixture["review_status"],
        "policy": "non-sealed diagnostic fixture; not a gate",
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


def test_v5_router_generalization_report_records_nonsealed_before_after() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v5-router-generalization-report.v1"
    assert report["status"] == "completed_not_a_gate"
    assert report["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_v4_text_used": False,
        "sealed_v4_labels_used": False,
        "source_fixture": "tests\\fixtures\\v5_critical_operations_fixture_v1.json",
        "source_fixture_review_status": "draft",
        "current_route_measurement_is_gate": False,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
    }
    assert report["before"]["case_count"] == 48
    assert report["before"]["error_count"] == 35
    assert report["before"]["critical_signal_recall"] == 0.452381
    assert report["after"] == {
        "case_count": 48,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 1.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
    assert report["delta"]["error_count"] == -35
    assert report["remaining_errors"] == []
    assert report["meets_presealed_nonsealed_challenge_threshold"] is True
    assert report["next_step"] == {
        "step": 5,
        "name": "nonsealed_replay_gate",
        "output": "build\\v5_nonsealed_replay_gate_report.json",
    }


def test_v5_router_generalization_report_matches_current_route() -> None:
    fixture = _load(FIXTURE_PATH)
    report = _load(REPORT_PATH)
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))
    measurement = evaluate_plm_extractor(
        benchmark.cases,
        lambda text: route(text).packet,
    )

    assert measurement["case_count"] == report["after"]["case_count"]
    assert measurement["intent_accuracy"] == report["after"]["intent_accuracy"]
    assert measurement["critical_signal_recall"] == report["after"]["critical_signal_recall"]
    assert measurement["operation_exact_match"] == report["after"]["operation_exact_match"]
    assert measurement["constraint_exact_match"] == report["after"]["constraint_exact_match"]
    assert measurement["risk_exact_match"] == report["after"]["risk_exact_match"]
    assert len(measurement["errors"]) == report["after"]["error_count"]