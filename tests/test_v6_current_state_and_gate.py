import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
CURRENT_REPORT_PATH = ROOT / "build" / "v6_current_state_report_v1.json"
CURRENT_MD_PATH = ROOT / "build" / "v6_current_state_report_v1.md"
GATE_REPORT_PATH = ROOT / "build" / "v6_nonsealed_replay_gate_report_v1.json"
GATE_MD_PATH = ROOT / "build" / "v6_nonsealed_replay_gate_report_v1.md"
ARCHIVE_ID = "2026-06-24_v6-nonsealed-exact-pre-roadmap-gate"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_current_state_report_records_backup_and_exact_score() -> None:
    report = _load(CURRENT_REPORT_PATH)

    assert report["schema_version"] == "v6-current-state-report.v1"
    assert report["status"] == "nonsealed_exact_ready_for_gate_packaging"
    assert report["backup"]["archive_id"] == ARCHIVE_ID
    assert (ROOT / report["backup"]["manifest"]).exists()
    assert (ROOT / report["backup"]["restore"]).exists()
    assert report["policy"] == {
        "sealed_fixture_opened_now": False,
        "sealed_measurement_used_for_tuning": False,
        "nonsealed_current_route_measurement_is_gate": False,
        "same_cycle_promotion_allowed": False,
        "draft_or_candidate_lanes_are_gate_evidence": False,
    }
    assert report["summary"]["lane_count"] == 8
    assert report["summary"]["exact_lane_count"] == 8
    assert report["summary"]["gap_lane_count"] == 0
    assert report["summary"]["average_nonsealed_score"] == 1.0
    assert report["required_lane_summary"] == {
        "lane_count": 5,
        "passed_exact_count": 5,
        "error_count": 0,
    }
    assert report["diagnostic_lane_summary"] == {
        "lane_count": 3,
        "passed_exact_count": 3,
        "error_count": 0,
    }


def test_v6_nonsealed_replay_gate_passes_without_sealed_or_candidate_gate_evidence() -> None:
    gate = _load(GATE_REPORT_PATH)

    assert gate["schema_version"] == "v6-nonsealed-replay-gate-report.v1"
    assert gate["status"] == "passed"
    assert gate["passed"] is True
    assert gate["policy"]["sealed_fixture_opened_now"] is False
    assert gate["policy"]["sealed_measurement_used_for_tuning"] is False
    assert gate["policy"]["draft_or_candidate_lanes_are_gate_evidence"] is False
    assert gate["summary"]["required_lane_count"] == 5
    assert gate["summary"]["required_passed_lane_count"] == 5
    assert gate["summary"]["required_error_count"] == 0
    assert gate["summary"]["diagnostic_lane_count"] == 3
    assert gate["summary"]["diagnostic_exact_lane_count"] == 3
    assert gate["summary"]["diagnostic_error_count"] == 0
    assert gate["summary"]["ready_for_step4_sealed_v6_rotation_review"] is True
    assert gate["contract"] == {
        "can_use_for_v6_roadmap_step3": True,
        "can_use_as_sealed_measurement": False,
        "can_use_for_same_cycle_promotion": False,
        "requires_human_review_before_sealed_rotation": True,
    }
    assert gate["next_action"] == "roadmap_step4_sealed_v6_rotation_review"


def test_v6_current_state_and_gate_markdown_exist() -> None:
    current_text = CURRENT_MD_PATH.read_text(encoding="utf-8")
    gate_text = GATE_MD_PATH.read_text(encoding="utf-8")

    assert "V6 Current State Report v1" in current_text
    assert "gap_lane_count: 0" in current_text
    assert "V6 Non-Sealed Replay Gate Report v1" in gate_text
    assert "status: `passed`" in gate_text
    assert "same_cycle_promotion_allowed: false" in gate_text