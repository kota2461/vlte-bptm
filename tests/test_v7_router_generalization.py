import json
from pathlib import Path

from semantic_routing import evaluate_plm_extractor
from semantic_routing.adapter import route
from semantic_routing.benchmark import parse_plm_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v7_router_repair_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v7_router_generalization_report_v1.json"
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_payload(fixture):
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "test wrapper for v7 step4 generalization",
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


def test_v7_router_generalization_report_records_nonsealed_before_after() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v7-router-generalization-report.v1"
    assert report["status"] == "completed_not_a_gate"
    assert report["policy"] == {
        "sealed_v6_text_used": False,
        "sealed_v6_labels_used": False,
        "source_fixture": "tests\\fixtures\\v7_router_repair_fixture_v1.json",
        "source_fixture_review_status": "draft",
        "current_route_measurement_is_gate": False,
        "human_review_required_before_gate": True,
        "same_cycle_promotion_allowed": False,
    }
    assert report["before"] == {
        "case_count": 72,
        "intent_accuracy": 0.736111,
        "critical_signal_recall": 0.476923,
        "operation_exact_match": 0.611111,
        "constraint_exact_match": 0.680556,
        "risk_exact_match": 0.763889,
        "valid_packet_rate": 1.0,
        "error_count": 52,
        "error_field_counts": {
            "constraints": 23,
            "information_state": 31,
            "operations": 28,
            "primary_intent": 19,
            "risk": 17,
        },
    }
    assert report["after"] == {
        "case_count": 72,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 1.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }
    assert report["delta"] == {
        "intent_accuracy": 0.263889,
        "critical_signal_recall": 0.523077,
        "operation_exact_match": 0.388889,
        "constraint_exact_match": 0.319444,
        "risk_exact_match": 0.236111,
        "error_count": -52,
    }
    assert report["meets_step5_entry_threshold"] is True
    assert report["next_step"] == {
        "step": 5,
        "name": "v7_nonsealed_replay_gate",
        "output": "build\\v7_nonsealed_replay_gate_report_v1.json",
    }


def test_v7_router_generalization_report_matches_current_route() -> None:
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


def test_v7_router_generalization_remains_recorded_after_step5_gate() -> None:
    targets = _load(TARGETS_PATH)
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert targets["status"] == "step8_sealed_v7_measurement_completed_v8_rotation_required"
    assert [step["status"] for step in targets["roadmap"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert targets["next_action"] == "roadmap_v8_step1_post_v7_measurement_taxonomy"
    assert targets["step4_router_generalization"]["meets_step5_entry_threshold"] is True
    assert "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | completed |" in roadmap
    assert "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | completed |" in roadmap
    assert "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |" in roadmap
    assert "Router generalization report: `build/v7_router_generalization_report_v1.json`" in main
    assert "Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`" in main
    assert "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`" in main
    assert "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`" in main
    assert "Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`" in main