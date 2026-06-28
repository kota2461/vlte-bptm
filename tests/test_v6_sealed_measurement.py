import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SEALED_V6_PATH = FIXTURES / "pattern_language_sealed_v6.json"
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v6_measurement_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
SUMMARY_PATH = ROOT / "build" / "v6_step6_measurement_summary.md"
ROADMAP_PATH = ROOT / "docs" / "PLM_V6_ROADMAP.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_sealed_measurement_consumes_fixture_once() -> None:
    measurement = _load(MEASUREMENT_PATH)
    registry = _load(REGISTRY_PATH)
    sealed_hash = hashlib.sha256(SEALED_V6_PATH.read_bytes()).hexdigest()
    entry = registry["fixtures"][SEALED_V6_PATH.name]

    assert measurement["schema_version"] == "plm-sealed-measurement-report.v1"
    assert measurement["sealed_fixture_opened"] is True
    assert measurement["sealed_labels_used_for_tuning"] is False
    assert measurement["fixture"]["registry_name"] == SEALED_V6_PATH.name
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
    assert entry["measurement_report"] == r"build\pattern_language_sealed_v6_measurement_report.json"


def test_v6_sealed_measurement_metrics_are_recorded() -> None:
    measurement = _load(MEASUREMENT_PATH)
    metrics = measurement["measurements"]

    assert metrics["case_count"] == 28
    assert metrics["valid_packet_rate"] == 1.0
    assert metrics["intent_accuracy"] == 0.75
    assert metrics["intent_macro_f1"] == 0.740136
    assert metrics["critical_signal_recall"] == 0.357143
    assert metrics["operation_exact_match"] == 0.607143
    assert metrics["constraint_exact_match"] == 0.607143
    assert metrics["risk_exact_match"] == 0.75
    assert metrics["evidence_offset_validity"] == 1.0
    assert len(metrics["errors"]) == 23
    assert metrics["critical_signals"]["contains_unverified_claims"]["recall"] == 0.0
    assert metrics["critical_signals"]["multiple_intents"]["recall"] == 0.25


def test_v6_measurement_blocks_readiness_until_successor_rotation() -> None:
    readiness = _load(READINESS_PATH)
    summary = SUMMARY_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")

    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
    assert "V6 Step 6 Sealed Measurement Summary" in summary
    assert "rotation_required_before_tuning: `True`" in summary
    assert "| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | completed |" in roadmap
    assert "| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | completed |" in roadmap

