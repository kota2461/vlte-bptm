import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SEALED_V10_PATH = FIXTURES / "pattern_language_sealed_v10.json"
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v10_measurement_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
SUMMARY_PATH = ROOT / "build" / "v10_step6_measurement_summary.md"
ROADMAP_PATH = ROOT / "docs" / "PLM_V10_ROADMAP.md"
TARGETS_PATH = ROOT / "build" / "v10_targets_and_roadmap_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v10_sealed_measurement_consumes_fixture_once() -> None:
    measurement = _load(MEASUREMENT_PATH)
    registry = _load(REGISTRY_PATH)
    sealed_hash = hashlib.sha256(SEALED_V10_PATH.read_bytes()).hexdigest()
    entry = registry["fixtures"][SEALED_V10_PATH.name]

    assert measurement["schema_version"] == "plm-sealed-measurement-report.v1"
    assert measurement["sealed_fixture_opened"] is True
    assert measurement["sealed_labels_used_for_tuning"] is False
    assert measurement["fixture"]["registry_name"] == SEALED_V10_PATH.name
    assert measurement["fixture"]["fixture_id"] == "pattern-language-sealed-v10"
    assert measurement["fixture"]["sha256"] == sealed_hash
    assert measurement["fixture"]["status_before_measurement"] == "active"
    assert measurement["registry_update"] == {
        "status_after_measurement": "consumed",
        "measured": True,
        "reviewed": False,
        "rotation_required_before_tuning": True,
    }
    assert entry["status"] == "consumed"
    assert entry["measured"] is True
    assert entry["reviewed"] is False
    assert entry["measurement_report"] == r"build\pattern_language_sealed_v10_measurement_report.json"


def test_v10_sealed_measurement_metrics_are_recorded_and_below_target() -> None:
    measurement = _load(MEASUREMENT_PATH)
    targets = _load(TARGETS_PATH)
    metrics = measurement["measurements"]
    minimum = targets["targets"]["minimum"]

    assert metrics["case_count"] == 28
    assert metrics["valid_packet_rate"] == 1.0
    assert metrics["intent_accuracy"] == 0.785714
    assert metrics["intent_macro_f1"] == 0.759637
    assert metrics["critical_signal_recall"] == 0.4
    assert metrics["operation_exact_match"] == 0.642857
    assert metrics["constraint_exact_match"] == 0.535714
    assert metrics["risk_exact_match"] == 0.678571
    assert metrics["evidence_offset_validity"] == 1.0
    assert len(metrics["errors"]) == 23
    assert metrics["intent_accuracy"] < minimum["intent_accuracy"]
    assert metrics["critical_signal_recall"] < minimum["critical_signal_recall"]
    assert metrics["operation_exact_match"] < minimum["operation_exact_match"]
    assert metrics["constraint_exact_match"] < minimum["constraint_exact_match"]
    assert metrics["risk_exact_match"] < minimum["risk_exact_match"]
    assert len(metrics["errors"]) > minimum["sealed_error_count_max"]


def test_v10_measurement_blocks_readiness_and_advances_to_v11_taxonomy() -> None:
    readiness = _load(READINESS_PATH)
    summary = SUMMARY_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    targets = _load(TARGETS_PATH)

    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
    assert readiness["next_action"] == "continue_accumulation_or_rotate_fixture"
    assert targets["status"] == "step6_sealed_v10_measurement_completed_v11_rotation_required"
    assert targets["next_action"] == "roadmap_v11_step1_post_v10_measurement_taxonomy"
    step6 = targets["step6_sealed_measurement"]
    assert step6["passed_minimum"] is False
    assert step6["minimum_metrics_met"] is False
    assert step6["critical_signal_miss_count"] == 9
    assert step6["critical_signal_miss_gate_met"] is False
    assert step6["rotation_required_before_tuning"] is True
    assert step6["readiness_after_measurement"] == {
        "decision": "blocked",
        "blocked_reasons": ["sealed_fixture_not_available"],
        "sealed_fixture": None,
    }
    assert step6["measurements"]["error_field_counts"] == {
        "constraints": 13,
        "information_state": 10,
        "operations": 10,
        "primary_intent": 6,
        "risk": 9,
    }
    assert "V10 Step 6 Sealed Measurement Summary" in summary
    assert "minimum_passed: `False`" in summary
    assert "| 6 | sealed_v10_one_time_measurement | `build\\pattern_language_sealed_v10_measurement_report.json` | completed |" in roadmap
