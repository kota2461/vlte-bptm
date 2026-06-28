import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "create_v8_targets_and_roadmap.py"
TARGETS_PATH = ROOT / "build" / "v8_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V8_ROADMAP.md"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v8_targets_record_post_v7_taxonomy_and_gate_without_sealed_training() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["schema_version"] == "v8-targets-and-roadmap.v1"
    assert payload["status"] == "step8_sealed_v8_measurement_completed_v9_rotation_required"
    assert payload["policy"] == {
        "sealed_v7_consumed": True,
        "sealed_v7_labels_used_for_tuning": False,
        "sealed_v7_text_used_for_training": False,
        "sealed_v7_measurement_used_as_taxonomy_only": True,
        "v8_priority_review_human_approved": True,
        "v8_nonsealed_replay_gate_passed": True,
        "prior_v8_provisional_replay_was_gate": False,
        "raw_debate_logs_direct_training_allowed": False,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_successor_required_before_measurement": True,
    }
    assert payload["baseline"] == {
        "fixture": "pattern_language_sealed_v7.json",
        "case_count": 28,
        "intent_accuracy": 0.785714,
        "critical_signal_recall": 0.642857,
        "operation_exact_match": 0.714286,
        "constraint_exact_match": 0.75,
        "risk_exact_match": 0.785714,
        "sealed_error_count": 16,
        "readiness_decision_after_measurement": "blocked",
        "blocked_reasons": ["sealed_fixture_not_available"],
    }


def test_v8_taxonomy_and_targets_are_set() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["taxonomy"]["field_error_counts"] == {
        "constraints": 7,
        "information_state": 6,
        "operations": 8,
        "primary_intent": 6,
        "risk": 6,
    }
    assert payload["taxonomy"]["critical_signal_miss_counts"] == {
        "missing_required_information": 2,
        "contains_unverified_claims": 0,
        "requires_current_information": 1,
        "multiple_intents": 2,
    }
    assert payload["taxonomy"]["intent_boundary_transitions"] == {
        "build->summarize": 1,
        "build->verify": 1,
        "clarify->build": 1,
        "clarify->verify": 2,
        "respond->explain": 1,
    }
    assert [item["id"] for item in payload["taxonomy"]["focus_areas"]] == [
        "clarify_missing_info_recovery",
        "operation_terminal_sequence",
        "constraint_false_positive_balance",
        "risk_ladder_boundary",
        "current_search_split",
        "paraphrase_and_mixed_language_robustness",
        "unverified_claim_guard",
    ]
    assert payload["targets"]["minimum"] == {
        "intent_accuracy": 0.892857,
        "critical_signal_recall": 0.857143,
        "operation_exact_match": 0.857143,
        "constraint_exact_match": 0.857143,
        "risk_exact_match": 0.892857,
        "sealed_error_count_max": 8,
        "critical_signal_miss_count_max": 2,
    }
    assert payload["targets"]["stretch"]["sealed_error_count_max"] == 5


def test_v8_nonsealed_recovery_and_roadmap_status() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["nonsealed_recovery_summary"]["source_topic_count"] == 100
    assert payload["nonsealed_recovery_summary"]["priority_review_count"] == 30
    assert payload["nonsealed_recovery_summary"]["v8_gate_required_error_count"] == 0
    assert payload["nonsealed_recovery_summary"]["v8_gate_case_count"] == 30
    assert payload["nonsealed_recovery_summary"]["v8_gate_exact"] is True
    assert payload["pre_rotation_gates"] == {
        "prior_v7_nonsealed_gate_required": True,
        "v8_priority_review_exact_required": True,
        "v8_nonsealed_gate_error_count_max": 0,
        "sealed_overlap_count_required": 0,
    }
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
    assert payload["roadmap"][5]["name"] == "sealed_v8_rotation_review"
    assert payload["step6_sealed_rotation_review"]["passed"] is True
    assert payload["step6_sealed_rotation_review"]["summary"]["blocker_count"] == 0
    assert payload["step7_sealed_rotation"]["passed"] is True
    assert payload["step7_sealed_rotation"]["summary"]["readiness_decision"] == "eligible"
    assert payload["step8_sealed_measurement"]["passed_minimum"] is False
    assert payload["step8_sealed_measurement"]["critical_signal_miss_gate_met"] is True
    assert payload["step8_sealed_measurement"]["measurements"]["error_count"] == 14
    assert payload["next_action"] == "roadmap_v9_step1_post_v8_measurement_taxonomy"


def test_v8_roadmap_docs_are_linked_and_script_regenerates() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "step8_sealed_v8_measurement_completed" in completed.stdout
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    v7 = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert "PLM V8 Roadmap" in roadmap
    assert "| 5 | v8_nonsealed_replay_gate | `build\\v8_nonsealed_replay_gate_report_v1.json` | completed |" in roadmap
    assert "| 6 | sealed_v8_rotation_review | `build\\v8_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert "| 7 | sealed_v8_rotation | `tests\\fixtures\\pattern_language_sealed_v8.json` | completed |" in roadmap
    assert "| 8 | sealed_v8_one_time_measurement | `build\\pattern_language_sealed_v8_measurement_report.json` | completed |" in roadmap
    assert "Step 9 Output" in v7
    assert "PLM V8: Recovery Gate And Fresh Rotation" in main
    assert "Targets and taxonomy: `build/v8_targets_and_roadmap_v1.json`" in main
    assert "Non-sealed replay gate report: `build/v8_nonsealed_replay_gate_report_v1.json`" in main
    payload = _load(TARGETS_PATH)
    assert payload["nonsealed_recovery_summary"]["v8_gate_required_error_count"] == 0
