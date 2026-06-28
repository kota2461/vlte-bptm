import json
import subprocess
import pytest
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "create_v9_targets_and_roadmap.py"
TARGETS_PATH = ROOT / "build" / "v9_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V9_ROADMAP.md"
V8_ROADMAP_PATH = ROOT / "docs" / "PLM_V8_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", autouse=True)
def _regenerate_artifact():
    """Regenerate the build/ artifact before the read-asserts so these tests do
    not depend on stale on-disk state left by a prior test or manual run (S4)."""
    subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def test_v9_targets_record_post_v8_taxonomy_without_sealed_training() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["schema_version"] == "v9-targets-and-roadmap.v1"
    assert payload["status"] == "step8_sealed_v9_measurement_completed_v10_rotation_required"
    assert payload["policy"] == {
        "sealed_v8_consumed": True,
        "sealed_v8_labels_used_for_tuning": False,
        "sealed_v8_text_used_for_training": False,
        "sealed_v8_measurement_used_as_taxonomy_only": True,
        "v9_primary_review_human_approved": True,
        "v9_constraint_operation_extension_human_approved": True,
        "v9_nonsealed_replay_gate_passed": True,
        "raw_debate_logs_direct_training_allowed": False,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_successor_required_before_measurement": True,
    }
    assert payload["baseline"] == {
        "fixture": "pattern_language_sealed_v8.json",
        "case_count": 28,
        "intent_accuracy": 0.928571,
        "critical_signal_recall": 0.833333,
        "operation_exact_match": 0.785714,
        "constraint_exact_match": 0.785714,
        "risk_exact_match": 0.785714,
        "sealed_error_count": 14,
        "readiness_decision_after_measurement": "blocked",
        "blocked_reasons": ["sealed_fixture_not_available"],
    }


def test_v9_taxonomy_targets_and_recovery_summary_are_set() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["taxonomy"]["field_error_counts"] == {
        "constraints": 6,
        "information_state": 6,
        "operations": 6,
        "primary_intent": 2,
        "risk": 6,
    }
    assert payload["taxonomy"]["critical_signal_miss_counts"] == {
        "missing_required_information": 0,
        "contains_unverified_claims": 0,
        "requires_current_information": 1,
        "multiple_intents": 1,
    }
    assert payload["taxonomy"]["intent_boundary_transitions"] == {
        "clarify->verify": 1,
        "respond->build": 1,
    }
    assert [item["id"] for item in payload["taxonomy"]["focus_areas"]] == [
        "operation_constraint_exactness",
        "risk_current_information_balance",
        "respond_vs_build_boundary",
        "clarify_vs_verify_boundary",
        "paraphrase_mixed_language_tail",
    ]
    assert payload["targets"]["minimum"] == {
        "intent_accuracy": 0.928571,
        "critical_signal_recall": 0.916667,
        "operation_exact_match": 0.892857,
        "constraint_exact_match": 0.892857,
        "risk_exact_match": 0.892857,
        "sealed_error_count_max": 7,
        "critical_signal_miss_count_max": 1,
    }
    assert payload["targets"]["stretch"]["critical_signal_recall"] == 1.0
    assert payload["nonsealed_recovery_summary"]["primary_review_count"] == 34
    assert payload["nonsealed_recovery_summary"]["constraint_operation_extension_count"] == 24
    assert payload["nonsealed_recovery_summary"]["v9_focused_case_count"] == 58
    assert payload["nonsealed_recovery_summary"]["v9_primary_review_exact"] is True
    assert payload["nonsealed_recovery_summary"]["v9_constraint_operation_extension_exact"] is True


def test_v9_roadmap_status_after_step8_measurement() -> None:
    payload = _load(TARGETS_PATH)

    assert [step["status"] for step in payload["roadmap"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["roadmap"][4]["name"] == "v9_nonsealed_replay_gate"
    assert payload["roadmap"][5]["name"] == "sealed_v9_rotation_review"
    assert payload["roadmap"][6]["name"] == "sealed_v9_rotation"
    assert payload["roadmap"][7]["name"] == "sealed_v9_one_time_measurement"
    assert payload["step5_nonsealed_replay_gate"]["passed"] is True
    assert payload["step5_nonsealed_replay_gate"]["summary"]["total_case_count"] == 88
    assert payload["step5_nonsealed_replay_gate"]["summary"]["required_error_count"] == 0
    assert payload["step6_sealed_rotation_review"]["passed"] is True
    assert payload["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0
    assert payload["step7_sealed_rotation"]["passed"] is True
    assert payload["step7_sealed_rotation"]["summary"]["case_count"] == 28
    assert payload["step7_sealed_rotation"]["summary"]["status"] == "active"
    assert payload["step7_sealed_rotation"]["summary"]["measured"] is False
    assert payload["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"
    assert payload["step7_sealed_rotation"]["summary"]["blocked_reasons"] == []
    assert payload["step8_sealed_measurement"]["passed_minimum"] is False
    assert payload["step8_sealed_measurement"]["minimum_metrics_met"] is False
    assert payload["step8_sealed_measurement"]["critical_signal_miss_count"] == 2
    assert payload["step8_sealed_measurement"]["critical_signal_miss_gate_met"] is False
    assert payload["step8_sealed_measurement"]["measurements"]["error_count"] == 17
    assert payload["next_action"] == "roadmap_v10_step1_post_v9_measurement_taxonomy"


def test_v9_roadmap_docs_are_linked_and_script_regenerates() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "step8_sealed_v9_measurement_completed" in completed.stdout
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    v8 = V8_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert "PLM V9 Roadmap" in roadmap
    assert "| 5 | v9_nonsealed_replay_gate | `build\\v9_nonsealed_replay_gate_report_v1.json` | completed |" in roadmap
    assert "| 6 | sealed_v9_rotation_review | `build\\v9_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v9_rotation | `tests\\fixtures\\pattern_language_sealed_v9.json` | completed |" in roadmap
    assert "| 8 | sealed_v9_one_time_measurement | `build\\pattern_language_sealed_v9_measurement_report.json` | completed |" in roadmap
    assert "Step 9 Output" in v8
    assert "PLM V9: Exactness Recovery And Fresh Rotation" in main
    assert "Targets and taxonomy: `build/v9_targets_and_roadmap_v1.json`" in main
    assert "Non-sealed replay gate report: `build/v9_nonsealed_replay_gate_report_v1.json`" in main
    assert "Sealed v9 rotation review: `build/v9_sealed_rotation_review_v1.json`" in main
    assert "Sealed v9 rotation report: `build/v9_sealed_rotation_report_v1.json`" in main
    assert "V10 taxonomy and fresh rotation required" in main
