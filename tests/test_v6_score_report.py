import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "measure_v6_scores.py"
REPORT_PATH = ROOT / "build" / "v6_score_report_v1.json"
SUMMARY_PATH = ROOT / "build" / "v6_score_summary_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_score_report_summary_and_policy() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v6-score-report.v1"
    assert report["status"] == "completed"
    assert report["policy"] == {
        "sealed_fixture_opened_now": False,
        "sealed_measurement_used_for_tuning": False,
        "nonsealed_current_route_measurement_is_gate": False,
        "same_cycle_promotion_allowed": False,
    }
    assert report["summary"]["lane_count"] == 8
    assert report["summary"]["exact_lane_count"] == 8
    assert report["summary"]["gap_lane_count"] == 0
    assert report["summary"]["gap_lanes"] == []
    assert report["summary"]["average_nonsealed_score"] == 1.0
    assert report["summary"]["average_nonsealed_raw_score"] == 0.875


def test_v6_score_report_boundary_false_positive_scores() -> None:
    report = _load(REPORT_PATH)
    lane = report["lanes"]["v6_boundary_false_positive_adopted"]

    assert lane["passed_exact"] is True
    assert lane["score"] == 1.0
    assert lane["raw_score"] == 0.8
    assert lane["score_note"] == "critical_signal_recall excluded from score because this lane has no expected critical signals"
    assert lane["critical_signal_support"] == {
        "missing_required_information": 0,
        "contains_unverified_claims": 0,
        "requires_current_information": 0,
        "multiple_intents": 0,
    }
    assert lane["measurement"] == {
        "case_count": 15,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }


def test_v6_score_report_boundary_priority_review_adopted_scores() -> None:
    report = _load(REPORT_PATH)
    lane = report["lanes"]["v6_boundary_priority_review_adopted"]

    assert lane["passed_exact"] is True
    assert lane["score"] == 1.0
    assert lane["raw_score"] == 0.8
    assert lane["score_note"] == "critical_signal_recall excluded from score because this lane has no expected critical signals"
    assert lane["critical_signal_support"] == {
        "missing_required_information": 0,
        "contains_unverified_claims": 0,
        "requires_current_information": 0,
        "multiple_intents": 0,
    }
    assert lane["measurement"] == {
        "case_count": 26,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }


def test_v6_score_report_structural_build_adopted_scores() -> None:
    report = _load(REPORT_PATH)
    lane = report["lanes"]["v6_structural_build_30_adopted"]

    assert lane["passed_exact"] is True
    assert lane["score"] == 1.0
    assert lane["raw_score"] == 0.8
    assert lane["score_note"] == "critical_signal_recall excluded from score because this lane has no expected critical signals"
    assert lane["critical_signal_support"] == {
        "missing_required_information": 0,
        "contains_unverified_claims": 0,
        "requires_current_information": 0,
        "multiple_intents": 0,
    }
    assert lane["measurement"] == {
        "case_count": 30,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }


def test_v6_score_report_contrast_negative_remains_next_gap() -> None:
    report = _load(REPORT_PATH)
    lane = report["lanes"]["v6_contrast_negative"]

    assert lane["passed_exact"] is True
    assert lane["score"] == 1.0
    assert lane["raw_score"] == 0.8
    assert lane["measurement"] == {
        "case_count": 30,
        "intent_accuracy": 1.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": 1.0,
        "constraint_exact_match": 1.0,
        "risk_exact_match": 1.0,
        "valid_packet_rate": 1.0,
        "error_count": 0,
        "error_field_counts": {},
    }


def test_v6_score_report_reads_existing_sealed_v5_without_opening() -> None:
    report = _load(REPORT_PATH)
    sealed = report["sealed_v5_existing_report"]

    assert sealed["available"] is True
    assert sealed["read_only_existing_report"] is True
    assert sealed["sealed_fixture_opened_now"] is False
    assert sealed["score"] == 0.705357
    assert sealed["raw_score"] == 0.705357
    assert sealed["measurement"]["case_count"] == 28
    assert sealed["measurement"]["error_count"] == 18


def test_v6_score_summary_exists() -> None:
    text = SUMMARY_PATH.read_text(encoding="utf-8")

    assert "V6 Score Summary v1" in text
    assert "boundary_false_positive_adopted_score: 1.000" in text
    assert "boundary_priority_review_adopted_score: 1.000" in text
    assert "structural_build_30_adopted_score: 1.000" in text
    assert "v6_boundary_priority_review_adopted | 26 | 1.000 | 0.800 | 0" in text
    assert "v6_structural_build_30_adopted | 30 | 1.000 | 0.800 | 0" in text
    assert "v6_contrast_negative | 30 | 1.000 | 0.800 | 0" in text
    assert "score 0.705357" in text


def test_v6_score_script_regenerates_report() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "v6_score_report_v1.json" in completed.stdout
    report = _load(REPORT_PATH)
    assert report["summary"]["boundary_false_positive_adopted_score"] == 1.0
    assert report["summary"]["boundary_priority_review_adopted_score"] == 1.0
    assert report["summary"]["structural_build_30_adopted_score"] == 1.0
    assert report["summary"]["gap_lanes"] == []