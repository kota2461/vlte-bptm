import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
TARGETS_PATH = ROOT / "build" / "v5_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V5_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v5_targets_are_defined_from_v4_measurement_taxonomy_only() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["schema_version"] == "v5-targets-and-roadmap.v1"
    assert payload["status"] == "sealed_v5_measured_consumed_rotation_required"
    assert payload["policy"]["sealed_v4_fixture_status"] == "consumed"
    assert payload["policy"]["sealed_v4_text_used_for_training"] is False
    assert payload["policy"]["sealed_v4_labels_used_for_tuning"] is False
    assert payload["policy"]["sealed_v4_measurement_used_as_taxonomy_only"] is True
    assert payload["policy"]["requires_sealed_v5_rotation_before_adjudication"] is True

    metrics = payload["baseline"]["metrics"]
    assert metrics["case_count"] == 28
    assert metrics["intent_accuracy"] == 0.857143
    assert metrics["critical_signal_recall"] == 0.5625
    assert metrics["operation_exact_match"] == 0.75
    assert metrics["constraint_exact_match"] == 0.821429
    assert metrics["risk_exact_match"] == 0.928571
    assert metrics["sealed_error_count"] == 15
    assert metrics["critical_signal_miss_count"] == 7


def test_v5_targets_are_discrete_and_stricter_than_v4_baseline() -> None:
    payload = _load(TARGETS_PATH)
    baseline = payload["baseline"]["metrics"]
    minimum = payload["targets"]["minimum"]
    stretch = payload["targets"]["stretch"]

    assert minimum["intent_accuracy"] == 0.928571
    assert minimum["critical_signal_recall"] == 0.875
    assert minimum["operation_exact_match"] == 0.892857
    assert minimum["constraint_exact_match"] == 0.928571
    assert minimum["risk_exact_match"] == 0.964286
    assert minimum["sealed_error_count_max"] == 6
    assert minimum["critical_signal_miss_count_max"] == 2
    assert stretch["sealed_error_count_max"] == 3
    assert stretch["critical_signal_miss_count_max"] == 0

    assert minimum["intent_accuracy"] > baseline["intent_accuracy"]
    assert minimum["critical_signal_recall"] > baseline["critical_signal_recall"]
    assert minimum["operation_exact_match"] > baseline["operation_exact_match"]
    assert minimum["constraint_exact_match"] > baseline["constraint_exact_match"]
    assert minimum["risk_exact_match"] > baseline["risk_exact_match"]
    assert minimum["sealed_error_count_max"] < baseline["sealed_error_count"]


def test_v5_error_taxonomy_contains_no_sealed_text_payloads() -> None:
    payload = _load(TARGETS_PATH)
    taxonomy = payload["baseline"]["error_taxonomy"]

    assert len(taxonomy) == 15
    for item in taxonomy:
        assert set(item) == {
            "id",
            "kind",
            "fields",
            "expected_intent",
            "predicted_intent",
            "allowed_use",
        }
        assert item["allowed_use"] == "sealed_v4_error_taxonomy_only_no_text_for_training"
        assert "input" not in item
        assert "text" not in item
        assert "expected" not in item

    assert payload["baseline"]["error_field_counts"] == {
        "constraints": 5,
        "information_state": 6,
        "operations": 7,
        "primary_intent": 4,
        "risk": 2,
    }


def test_v5_roadmap_documents_handoff_and_presealed_gates() -> None:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    payload = _load(TARGETS_PATH)

    assert "PLM V5 Roadmap" in roadmap
    assert "critical_signal_recall | 0.562500 | 0.875000" in roadmap
    assert "sealed_error_count | 15 | <= 6 | <= 3" in roadmap
    assert "sealed_text_overlap_count: 0" in roadmap
    assert "Step 2 Output" in roadmap
    assert "Step 3 Output" in roadmap
    assert "Step 4 Output" in roadmap
    assert "Step 5 Output" in roadmap
    assert "Step 6 Output" in roadmap
    assert "Step 7 Output" in roadmap
    assert "v5_nonsealed_curriculum_plan_v1.json" in roadmap
    assert "v5_critical_operations_fixture_v1.json" in roadmap
    assert "v5_router_generalization_report.json" in roadmap
    assert "v5_nonsealed_replay_gate_report.json" in roadmap
    assert "v5_sealed_rotation_report.json" in roadmap
    assert "pattern_language_sealed_v5_measurement_report.json" in roadmap
    assert "Router generalization report" in main
    assert "Non-sealed replay gate report" in main
    assert "Sealed v5 rotation report" in main
    assert "Sealed v5 measurement" in main
    assert "PLM V5: Critical Signal Recovery" in main
    assert payload["roadmap"][0]["status"] == "completed"
    assert payload["roadmap"][1]["status"] == "completed"
    assert payload["roadmap"][2]["status"] == "draft_created"
    assert payload["roadmap"][3]["status"] == "completed"
    assert payload["roadmap"][4]["status"] == "completed"
    assert payload["roadmap"][5]["status"] == "completed"
    assert payload["roadmap"][6]["status"] == "completed"
    assert payload["step2_curriculum_plan"]["status"] == "designed"
    assert payload["step2_curriculum_plan"]["case_count_min"] == 48
    assert payload["step3_critical_operations_fixture"]["status"] == "draft_ready_for_human_review"
    assert payload["step3_critical_operations_fixture"]["case_count"] == 48
    assert payload["step3_critical_operations_fixture"]["current_route_measurement_is_gate"] is False
    assert payload["step4_router_generalization"]["status"] == "completed_not_a_gate"
    assert payload["step4_router_generalization"]["current_route_measurement_is_gate"] is False
    assert payload["step4_router_generalization"]["before"]["error_count"] == 35
    assert payload["step4_router_generalization"]["after"]["error_count"] == 0
    assert payload["step4_router_generalization"]["after"]["critical_signal_recall"] == 1.0
    assert payload["step4_router_generalization"]["meets_presealed_nonsealed_challenge_threshold"] is True
    assert payload["step5_nonsealed_replay_gate"]["status"] == "passed"
    assert payload["step5_nonsealed_replay_gate"]["passed"] is True
    assert payload["step5_nonsealed_replay_gate"]["lane_summary"]["passed_lane_count"] == 4
    assert payload["step5_nonsealed_replay_gate"]["lane_summary"]["ready_for_step6_sealed_v5_rotation"] is True
    assert payload["step6_sealed_v5_rotation"]["status"] == "active_unmeasured"
    assert payload["step6_sealed_v5_rotation"]["fixture"]["registry_name"] == "pattern_language_sealed_v5.json"
    assert payload["step6_sealed_v5_rotation"]["fixture"]["measured"] is False
    assert payload["step6_sealed_v5_rotation"]["fixture"]["reviewed"] is False
    assert payload["step6_sealed_v5_rotation"]["sealed_v5_opened_for_measurement"] is False
    assert payload["step7_sealed_v5_measurement"]["status"] == "measured_consumed_minimum_not_met"
    assert payload["step7_sealed_v5_measurement"]["sealed_v5_opened_for_measurement"] is True
    assert payload["step7_sealed_v5_measurement"]["sealed_v5_labels_used_for_tuning"] is False
    assert payload["step7_sealed_v5_measurement"]["rotation_required_before_tuning"] is True
    assert payload["step7_sealed_v5_measurement"]["metrics"]["intent_accuracy"] == 0.75
    assert payload["step7_sealed_v5_measurement"]["metrics"]["critical_signal_recall"] == 0.375
    assert payload["step7_sealed_v5_measurement"]["metrics"]["sealed_error_count"] == 18
    assert payload["step7_sealed_v5_measurement"]["metrics"]["critical_signal_miss_count"] == 10
    assert payload["step7_sealed_v5_measurement"]["target_result"]["meets_minimum"] is False
    assert payload["pre_sealed_v5_gates"]["sealed_text_overlap_count"] == 0