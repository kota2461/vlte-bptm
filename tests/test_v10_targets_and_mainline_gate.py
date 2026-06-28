import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
CREATE_SCRIPT_PATH = ROOT / "build" / "create_v10_targets_and_roadmap.py"
GATE_SCRIPT_PATH = ROOT / "build" / "run_v10_mainline_replay_gate.py"
TARGETS_PATH = ROOT / "build" / "v10_targets_and_roadmap_v1.json"
GATE_PATH = ROOT / "build" / "v10_mainline_replay_gate_report_v1.json"
REVIEW_PATH = ROOT / "build" / "v10_sealed_rotation_review_v1.json"
REVIEW_MD_PATH = ROOT / "build" / "v10_sealed_rotation_review_v1.md"
SEALED_V10_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v10.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V10_ROADMAP.md"
V9_ROADMAP_PATH = ROOT / "docs" / "PLM_V9_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v10_targets_record_post_v9_taxonomy_and_bridge_policy() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["schema_version"] == "v10-targets-and-roadmap.v1"
    assert payload["status"] == "step6_sealed_v10_measurement_completed_v11_rotation_required"
    assert payload["policy"] == {
        "sealed_v9_consumed": True,
        "sealed_v9_labels_used_for_tuning": False,
        "sealed_v9_text_used_for_training": False,
        "sealed_v9_measurement_used_as_taxonomy_only": True,
        "v9_nonsealed_replay_gate_passed": True,
        "thought_color_source_scope": "experiment_only",
        "thought_color_source_mainline_training_allowed": False,
        "v10_bridge_mainline_training_allowed": False,
        "v10_bridge_mainline_allowed_use": "router_generalization_and_nonsealed_replay_only",
        "v10_bridge_human_reviewed": True,
        "raw_thought_color_samples_direct_training_allowed": False,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_successor_required_before_measurement": True,
    }
    assert payload["baseline"] == {
        "fixture": "pattern_language_sealed_v9.json",
        "case_count": 28,
        "intent_accuracy": 0.892857,
        "critical_signal_recall": 0.857143,
        "operation_exact_match": 0.821429,
        "constraint_exact_match": 0.642857,
        "risk_exact_match": 0.75,
        "sealed_error_count": 17,
        "critical_signal_miss_count": 2,
        "readiness_decision_after_measurement": "blocked",
        "blocked_reasons": ["sealed_fixture_not_available"],
    }


def test_v10_taxonomy_targets_and_bridge_summary_are_set() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["taxonomy"]["field_error_counts"] == {
        "constraints": 10,
        "information_state": 6,
        "operations": 5,
        "primary_intent": 3,
        "risk": 7,
    }
    assert payload["taxonomy"]["critical_signal_miss_counts"] == {
        "missing_required_information": 0,
        "contains_unverified_claims": 1,
        "requires_current_information": 0,
        "multiple_intents": 1,
    }
    assert payload["taxonomy"]["intent_boundary_transitions"] == {
        "clarify->verify": 1,
        "respond->verify": 1,
        "verify->summarize": 1,
    }
    assert [item["id"] for item in payload["taxonomy"]["focus_areas"]] == [
        "constraint_exactness_recovery",
        "risk_ladder_recovery",
        "missing_multiple_information_state",
        "operation_order_terminality",
        "intent_boundary_tail",
    ]
    assert payload["targets"]["minimum"] == {
        "intent_accuracy": 0.928571,
        "critical_signal_recall": 0.928571,
        "operation_exact_match": 0.892857,
        "constraint_exact_match": 0.857143,
        "risk_exact_match": 0.857143,
        "sealed_error_count_max": 8,
        "critical_signal_miss_count_max": 1,
    }
    bridge = payload["thought_color_bridge_summary"]
    assert bridge["adopted_count"] == 72
    assert bridge["mainline_allowed_use"] == "router_generalization_and_nonsealed_replay_only"
    assert bridge["source_mainline_training_allowed"] is False
    assert bridge["isolated_rewrite_fixture_training_allowed"] is False
    assert bridge["isolated_current_route_measurement_is_gate"] is False
    assert bridge["isolated_measurement"]["error_count"] == 0
    assert bridge["isolated_measurement"]["constraint_exact_match"] == 1.0


def test_v10_plus_learning_lanes_keep_answer_prototypes_separate() -> None:
    payload = _load(TARGETS_PATH)
    lanes = payload["v10_plus_learning_lanes"]

    assert lanes["schema_version"] == "v10-plus-learning-lanes.v1"
    assert lanes["status"] == "planned_after_v10_rotation_review"
    assert lanes["lane_relationship"] == {
        "keep_separate_until_review": True,
        "do_not_mix_answer_only_with_router_judgment": True,
        "answer_only_must_be_converted_to_probes_before_mainline_gate": True,
    }
    assert lanes["recommended_initial_mix"] == {
        "router_judgment_lane": 0.6,
        "boundary_pairs_from_router_judgment": 0.2,
        "answer_prototype_lane": 0.2,
    }

    router = lanes["router_judgment_lane"]
    assert router["priority"] == 1
    assert router["mainline_value"] == "high"
    assert router["training_allowed_after_human_review"] is True
    assert router["direct_mainline_candidate_allowed"] is True
    assert router["data_unit"] == "distilled router trace, not raw router log"
    assert "near_miss" in router["required_fields"]
    assert "nonsealed_replay_gate_candidate" in router["allowed_use"]
    assert "store_raw_log_as_training_data" in router["must_not"]

    answer = lanes["answer_prototype_lane"]
    assert answer["priority"] == 2
    assert answer["separated_from_router_training"] is True
    assert answer["direct_semantic_packet_training_allowed"] is False
    assert answer["training_allowed_after_probe_conversion_and_review"] is True
    assert "generated_question_probes" in answer["required_fields"]
    assert "probe_expected_semantic_packets" in answer["required_fields"]
    assert "question_probe_generation" in answer["allowed_use"]
    assert "infer_final_input_intent_from_answer_only" in answer["must_not"]


def test_v10_mainline_replay_gate_passes_without_training_or_sealed_use() -> None:
    report = _load(GATE_PATH)

    assert report["schema_version"] == "v10-mainline-replay-gate-report.v1"
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["policy"]["sealed_fixture_opened_now"] is False
    assert report["policy"]["sealed_measurement_used_for_tuning"] is False
    assert report["policy"]["sealed_v9_text_used"] is False
    assert report["policy"]["sealed_v9_labels_used"] is False
    assert report["policy"]["thought_color_source_mainline_training_allowed"] is False
    assert report["policy"]["v10_bridge_mainline_training_allowed"] is False
    assert report["policy"]["isolated_rewrite_fixture_training_allowed"] is False
    assert report["policy"]["isolated_replay_was_gate"] is False
    assert report["policy"]["nonsealed_current_route_measurement_is_gate"] is True
    assert report["summary"] == {
        "dependency_v9_gate_passed": True,
        "dependency_v9_required_error_count": 0,
        "required_lane_count": 1,
        "required_passed_lane_count": 1,
        "required_error_count": 0,
        "total_case_count": 72,
        "v10_bridge_case_count": 72,
        "v10_bridge_error_count": 0,
        "ready_for_step4_sealed_v10_rotation_review": True,
    }
    lane = report["required_lanes"][0]
    assert lane["passed_exact"] is True
    assert lane["measurement"]["case_count"] == 72
    assert lane["measurement"]["operation_exact_match"] == 1.0
    assert lane["measurement"]["constraint_exact_match"] == 1.0
    assert lane["errors"] == []
    assert report["roadmap_decision"] == {
        "can_advance": True,
        "advance_to": "sealed_v10_rotation_review",
        "blocked_reasons": [],
    }


def test_v10_roadmap_can_advance_to_sealed_rotation_after_review() -> None:
    payload = _load(TARGETS_PATH)

    assert [step["status"] for step in payload["roadmap"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["roadmap"][3]["name"] == "sealed_v10_rotation_review"
    assert payload["roadmap"][4]["name"] == "sealed_v10_rotation"
    assert payload["roadmap"][5]["name"] == "sealed_v10_one_time_measurement"
    assert payload["next_action"] == "roadmap_v11_step1_post_v10_measurement_taxonomy"
    assert payload["roadmap_decision"] == {
        "can_advance": True,
        "advance_to": "v11_post_v10_measurement_taxonomy",
        "blocked_reasons": [],
    }
    assert payload["step3_mainline_replay_gate"]["passed"] is True
    assert payload["step3_mainline_replay_gate"]["summary"]["required_error_count"] == 0
    assert payload["step5_sealed_rotation"]["passed"] is True
    assert payload["step5_sealed_rotation"]["summary"] == {
        "case_count": 28,
        "status": "active",
        "measured": False,
        "reviewed": False,
        "readiness_decision": "eligible",
        "blocked_reasons": [],
    }
    assert payload["step6_sealed_measurement"]["passed_minimum"] is False
    assert payload["step6_sealed_measurement"]["minimum_metrics_met"] is False
    assert payload["step6_sealed_measurement"]["critical_signal_miss_count"] == 9
    assert payload["step6_sealed_measurement"]["critical_signal_miss_gate_met"] is False
    assert payload["step6_sealed_measurement"]["readiness_after_measurement"] == {
        "decision": "blocked",
        "blocked_reasons": ["sealed_fixture_not_available"],
        "sealed_fixture": None,
    }
    assert payload["step6_sealed_measurement"]["measurements"] == {
        "case_count": 28,
        "intent_accuracy": 0.785714,
        "intent_macro_f1": 0.759637,
        "critical_signal_recall": 0.4,
        "operation_exact_match": 0.642857,
        "constraint_exact_match": 0.535714,
        "risk_exact_match": 0.678571,
        "valid_packet_rate": 1.0,
        "evidence_offset_validity": 1.0,
        "error_count": 23,
        "error_field_counts": {
            "constraints": 13,
            "information_state": 10,
            "operations": 10,
            "primary_intent": 6,
            "risk": 9,
        },
    }


def test_v10_sealed_rotation_review_is_pre_rotation_eligible() -> None:
    report = _load(REVIEW_PATH)

    assert report["schema_version"] == "v10-sealed-rotation-review.v1"
    assert report["decision"] == "eligible_for_fresh_sealed_v10_rotation"
    assert report["passed"] is True
    assert report["policy"] == {
        "sealed_v10_fixture_created_now": False,
        "sealed_v10_opened_for_measurement": False,
        "sealed_v10_labels_used_for_tuning": False,
        "sealed_v9_text_used_for_training": False,
        "sealed_v9_labels_used_for_tuning": False,
        "sealed_v9_measurement_used_as_taxonomy_only": True,
        "nonsealed_replay_gate_required": True,
        "nonsealed_replay_gate_passed": True,
        "same_cycle_promotion_allowed": False,
    }
    assert report["gate_summary"]["required_error_count"] == 0
    assert report["gate_summary"]["total_case_count"] == 72
    assert report["registry_state"]["active_sealed_fixtures"] == []
    assert report["registry_state"]["previous_sealed"] == {
        "registry_name": "pattern_language_sealed_v9.json",
        "status": "consumed",
        "measured": True,
        "reviewed": False,
        "measurement_report": "build\\pattern_language_sealed_v9_measurement_report.json",
    }
    assert report["registry_state"]["planned_successor"] == {
        "registry_name": "pattern_language_sealed_v10.json",
        "predecessor": "pattern_language_sealed_v9.json",
        "status": "not_created",
        "measured": False,
        "reviewed": False,
    }
    assert SEALED_V10_PATH.exists() is True
    assert report["blockers"] == []
    assert report["next_action"] == "roadmap_v10_step5_generate_and_rotate_sealed_v10_fixture"


def test_v10_sealed_rotation_review_records_fixture_constraints() -> None:
    report = _load(REVIEW_PATH)
    constraints = report["planned_v10_fixture_constraints"]

    assert constraints["case_count"] == 28
    assert constraints["cases_per_intent"] == 4
    assert constraints["split"] == "sealed"
    assert constraints["must_be_unopened_until_measurement"] is True
    assert "pattern_language_sealed_v9.json" in constraints["must_exclude_exact_text_from"]["prior_sealed_and_benchmark"]
    assert "tests\\fixtures\\v10_thought_color_bridge_isolated_benchmark_v1.json" in constraints[
        "must_exclude_exact_text_from"
    ]["v10_required_nonsealed_gate_lanes"]
    assert constraints["measurement_rule"] == "measure_once_then_mark_consumed"
    assert "measurement-only" in constraints["labels_rule"]


def test_v10_rotation_review_docs_and_targets_are_step5_ready() -> None:
    review_md = REVIEW_MD_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    targets = _load(TARGETS_PATH)

    assert "V10 Sealed Rotation Review v1" in review_md
    assert "eligible_for_fresh_sealed_v10_rotation" in review_md
    assert targets["step4_sealed_rotation_review"]["passed"] is True
    assert targets["step4_sealed_rotation_review"]["summary"]["blocker_count"] == 0
    assert r"| 4 | sealed_v10_rotation_review | `build\v10_sealed_rotation_review_v1.json` | completed |" in roadmap
    assert r"| 5 | sealed_v10_rotation | `tests\fixtures\pattern_language_sealed_v10.json` | completed |" in roadmap
    assert r"| 6 | sealed_v10_one_time_measurement | `build\pattern_language_sealed_v10_measurement_report.json` | completed |" in roadmap
    assert "Sealed v10 rotation review: `build/v10_sealed_rotation_review_v1.json`" in main
    assert "Sealed v10 rotation report: `build/v10_sealed_rotation_report_v1.json`" in main
    assert "Sealed v10 fixture: `tests/fixtures/pattern_language_sealed_v10.json`" in main
    assert "Sealed v10 measurement: `build/pattern_language_sealed_v10_measurement_report.json`" in main
    assert "Sealed v10 summary: `build/v10_step6_measurement_summary.md`" in main
    assert "advance_to=v11_post_v10_measurement_taxonomy" in main


def test_v10_scripts_and_docs_regenerate() -> None:
    gate = subprocess.run(
        [sys.executable, "-B", str(GATE_SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert '"status": "passed"' in gate.stdout

    created = subprocess.run(
        [sys.executable, "-B", str(CREATE_SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "step6_sealed_v10_measurement_completed" in created.stdout

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    v9 = V9_ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")

    assert "PLM V10 Roadmap" in roadmap
    assert "can_advance: true" in roadmap
    assert "advance_to: v11_post_v10_measurement_taxonomy" in roadmap
    assert "V10+ Learning Lanes" in roadmap
    assert "answer_prototype_lane" in roadmap
    assert "router_judgment_lane" in roadmap
    assert "Step 9 Output" in v9
    assert "PLM V10: Bridge Generalization And Exactness Recovery" in main
    assert "Targets and taxonomy: `build/v10_targets_and_roadmap_v1.json`" in main
    assert "V10+ learning lanes: router_judgment_lane and separated answer_prototype_lane" in main
    assert "Mainline replay gate: `build/v10_mainline_replay_gate_report_v1.json`" in main
    assert "Sealed v10 rotation review: `build/v10_sealed_rotation_review_v1.json`" in main
    assert "Roadmap decision: can_advance=true" in main
