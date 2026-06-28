import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
CANDIDATE_REPORT_PATH = ROOT / "build" / "v4_candidate_eval_report.json"
ROTATION_REPORT_PATH = ROOT / "build" / "v4_sealed_rotation_report.json"
MEASUREMENT_REPORT_PATH = ROOT / "build" / "pattern_language_sealed_v4_measurement_report.json"
REGISTRY_PATH = FIXTURES / "pattern_language_fixture_registry.json"
SEALED_V4_PATH = FIXTURES / "pattern_language_sealed_v4.json"
SEALED_V5_PATH = FIXTURES / "pattern_language_sealed_v5.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v4_candidate_eval_uses_only_nonsealed_material() -> None:
    report = _load(CANDIDATE_REPORT_PATH)

    assert report["schema_version"] == "v4-candidate-eval-report.v1"
    assert report["decision"] == "eligible_for_v4_sealed_measurement"
    assert report["policy"]["sealed_fixtures_opened_for_candidate_eval"] is False
    assert report["policy"]["sealed_labels_used_for_tuning"] is False
    assert report["policy"]["v3_sealed_text_used_for_training"] is False
    assert report["policy"]["v3_measurement_used_as_taxonomy_only"] is True
    assert report["policy"]["success_pattern_lane_write_allowed_from_failures"] is False

    assert report["visible_plm"]["case_count"] == 56
    assert report["visible_plm"]["intent_accuracy"] == 1.0
    assert report["visible_plm"]["critical_signal_recall"] == 1.0
    assert report["visible_plm"]["errors"] == []
    assert report["failure_guard"]["summary"]["item_count"] == 38
    assert report["failure_guard"]["summary"]["guard_exact_match_rate"] == 1.0
    assert report["puzzle_failure_memory"]["summary"]["failure_count"] == 2
    assert report["puzzle_failure_memory"]["policy"]["source_success_traces_used_for_training"] is False
    assert report["nonsealed_gates"]["passed"] is True


def test_v4_sealed_rotation_report_records_pre_measurement_activation() -> None:
    rotation = _load(ROTATION_REPORT_PATH)
    sealed_hash = hashlib.sha256(SEALED_V4_PATH.read_bytes()).hexdigest()

    assert rotation["schema_version"] == "v4-sealed-rotation-report.v1"
    assert rotation["policy"]["sealed_v4_opened_for_measurement"] is False
    assert rotation["policy"]["sealed_v4_labels_used_for_tuning"] is False
    assert rotation["policy"]["v3_sealed_text_used_for_training"] is False
    assert rotation["rotated_from"]["registry_name"] == "pattern_language_sealed_v3.json"
    assert rotation["rotated_from"]["status"] == "consumed"
    assert rotation["rotated_to"]["registry_name"] == SEALED_V4_PATH.name
    assert rotation["rotated_to"]["case_count"] == 28
    assert rotation["rotated_to"]["sha256"] == sealed_hash
    assert rotation["rotated_to"]["status"] == "active"
    assert rotation["rotated_to"]["measured"] is False
    assert rotation["rotated_to"]["reviewed"] is False


def test_v4_sealed_measurement_consumes_fixture_and_v5_is_later_consumed() -> None:
    registry = _load(REGISTRY_PATH)
    measurement = _load(MEASUREMENT_REPORT_PATH)
    readiness = _load(READINESS_PATH)
    sealed_hash = hashlib.sha256(SEALED_V4_PATH.read_bytes()).hexdigest()

    fixtures = registry["fixtures"]
    active = [
        name for name, entry in fixtures.items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    assert active == []
    assert fixtures[SEALED_V4_PATH.name]["sha256"] == sealed_hash
    assert fixtures[SEALED_V4_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V4_PATH.name]["measured"] is True
    assert fixtures[SEALED_V4_PATH.name]["reviewed"] is False
    assert fixtures[SEALED_V4_PATH.name]["measurement_report"] == r"build\pattern_language_sealed_v4_measurement_report.json"
    assert fixtures[SEALED_V4_PATH.name]["successor"] == SEALED_V5_PATH.name
    assert fixtures[SEALED_V5_PATH.name]["status"] == "consumed"
    assert fixtures[SEALED_V5_PATH.name]["measured"] is True
    assert fixtures[SEALED_V5_PATH.name]["reviewed"] is False
    assert fixtures[SEALED_V5_PATH.name]["measurement_report"] == r"build\pattern_language_sealed_v5_measurement_report.json"
    assert fixtures[SEALED_V5_PATH.name]["successor"] == "pattern_language_sealed_v6.json"
    assert fixtures["pattern_language_sealed_v6.json"]["status"] == "consumed"
    assert fixtures["pattern_language_sealed_v6.json"]["measured"] is True
    assert fixtures["pattern_language_sealed_v6.json"]["reviewed"] is False
    assert fixtures["pattern_language_sealed_v6.json"]["measurement_report"] == r"build\pattern_language_sealed_v6_measurement_report.json"

    assert measurement["schema_version"] == "plm-sealed-measurement-report.v1"
    assert measurement["sealed_fixture_opened"] is True
    assert measurement["sealed_labels_used_for_tuning"] is False
    assert measurement["fixture"]["registry_name"] == SEALED_V4_PATH.name
    assert measurement["fixture"]["sha256"] == sealed_hash
    assert measurement["fixture"]["status_before_measurement"] == "active"
    assert measurement["measurements"]["case_count"] == 28
    assert measurement["measurements"]["intent_accuracy"] == 0.857143
    assert measurement["measurements"]["critical_signal_recall"] == 0.5625
    assert measurement["measurements"]["operation_exact_match"] == 0.75
    assert measurement["measurements"]["constraint_exact_match"] == 0.821429
    assert measurement["measurements"]["risk_exact_match"] == 0.928571
    assert len(measurement["measurements"]["errors"]) == 15
    assert measurement["registry_update"]["status_after_measurement"] == "consumed"
    assert measurement["registry_update"]["rotation_required_before_tuning"] is True

    assert readiness["decision"] == "blocked"
    assert readiness["sealed_fixture_opened"] is False
    assert readiness["sealed_fixture"] is None
    assert readiness["blocked_reasons"] == ["sealed_fixture_not_available"]
    assert readiness["next_action"] == "continue_accumulation_or_rotate_fixture"


def test_v4_adoption_registry_records_measurement_completion() -> None:
    adoption = _load(ADOPTION_PATH)

    assert adoption["status"] == "v4_sealed_measured_consumed_rotation_required"
    steps = {step["step"]: step["status"] for step in adoption["sequence"]}
    assert steps[8] == "completed"
    assert adoption["summary"]["v4_candidate_visible_case_count"] == 56
    assert adoption["summary"]["v4_candidate_visible_intent_accuracy"] == 1.0
    assert adoption["summary"]["v4_candidate_failure_guard_exact_match_rate"] == 1.0
    assert adoption["summary"]["v4_candidate_puzzle_failure_memory_items"] == 2
    assert adoption["summary"]["active_plm_sealed_fixture"] == SEALED_V4_PATH.name
    assert adoption["summary"]["v4_sealed_measured"] is True
    assert adoption["summary"]["v4_sealed_fixture_status"] == "consumed"
    assert adoption["summary"]["v4_sealed_intent_accuracy"] == 0.857143
    assert adoption["summary"]["v4_sealed_critical_signal_recall"] == 0.5625
    assert adoption["summary"]["v4_sealed_error_count"] == 15
    assert adoption["summary"]["plm_measurement_readiness_decision"] == "blocked"
    assert adoption["review_decision"]["v4_candidate_eval_report"] == r"build\v4_candidate_eval_report.json"
    assert adoption["review_decision"]["v4_sealed_rotation_report"] == r"build\v4_sealed_rotation_report.json"
    assert adoption["review_decision"]["v4_active_sealed_fixture"] == r"tests\fixtures\pattern_language_sealed_v4.json"
    assert adoption["review_decision"]["v4_sealed_measurement_report"] == r"build\pattern_language_sealed_v4_measurement_report.json"
    assert adoption["review_decision"]["v4_sealed_rotation_required_before_tuning"] is True

