import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SEALED_V8_PATH = FIXTURES / "pattern_language_sealed_v8.json"
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v8_measurement_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
SUMMARY_PATH = ROOT / "build" / "v8_step8_measurement_summary.md"
ROADMAP_PATH = ROOT / "docs" / "PLM_V8_ROADMAP.md"
TARGETS_PATH = ROOT / "build" / "v8_targets_and_roadmap_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v8_sealed_measurement_consumes_fixture_once() -> None:
    measurement = _load(MEASUREMENT_PATH)
    registry = _load(REGISTRY_PATH)
    sealed_hash = hashlib.sha256(SEALED_V8_PATH.read_bytes()).hexdigest()
    entry = registry["fixtures"][SEALED_V8_PATH.name]

    assert measurement["schema_version"] == "plm-sealed-measurement-report.v1"
    assert measurement["sealed_fixture_opened"] is True
    assert measurement["sealed_labels_used_for_tuning"] is False
    assert measurement["fixture"]["registry_name"] == SEALED_V8_PATH.name
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
    assert entry["measurement_report"] == r"build\pattern_language_sealed_v8_measurement_report.json"


def test_v8_sealed_measurement_metrics_are_recorded_and_below_target() -> None:
    measurement = _load(MEASUREMENT_PATH)
    targets = _load(TARGETS_PATH)
    metrics = measurement["measurements"]
    minimum = targets["targets"]["minimum"]

    assert metrics["case_count"] == 28
    assert metrics["valid_packet_rate"] == 1.0
    assert metrics["intent_accuracy"] == 0.928571
    assert metrics["intent_macro_f1"] == 0.927438
    assert metrics["critical_signal_recall"] == 0.833333
    assert metrics["operation_exact_match"] == 0.785714
    assert metrics["constraint_exact_match"] == 0.785714
    assert metrics["risk_exact_match"] == 0.785714
    assert metrics["evidence_offset_validity"] == 1.0
    assert len(metrics["errors"]) == 14
    assert metrics["intent_accuracy"] >= minimum["intent_accuracy"]
    assert metrics["critical_signal_recall"] < minimum["critical_signal_recall"]
    assert metrics["operation_exact_match"] < minimum["operation_exact_match"]
    assert metrics["constraint_exact_match"] < minimum["constraint_exact_match"]
    assert metrics["risk_exact_match"] < minimum["risk_exact_match"]
    assert len(metrics["errors"]) > minimum["sealed_error_count_max"]


def test_v8_measurement_blocks_readiness_until_successor_rotation() -> None:
    readiness = _load(READINESS_PATH)
    summary = SUMMARY_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    targets = _load(TARGETS_PATH)

    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
    assert targets["status"] == "step8_sealed_v8_measurement_completed_v9_rotation_required"
    assert targets["next_action"] == "roadmap_v9_step1_post_v8_measurement_taxonomy"
    assert targets["step8_sealed_measurement"]["passed_minimum"] is False
    assert targets["step8_sealed_measurement"]["minimum_metrics_met"] is False
    assert targets["step8_sealed_measurement"]["critical_signal_miss_count"] == 2
    assert targets["step8_sealed_measurement"]["critical_signal_miss_gate_met"] is True
    assert targets["step8_sealed_measurement"]["measurements"]["error_field_counts"] == {
        "constraints": 6,
        "information_state": 6,
        "operations": 6,
        "primary_intent": 2,
        "risk": 6,
    }
    assert "V8 Step 8 Sealed Measurement Summary" in summary
    assert "minimum_passed: `False`" in summary
    assert "| 8 | sealed_v8_one_time_measurement | `build\\pattern_language_sealed_v8_measurement_report.json` | completed |" in roadmap
