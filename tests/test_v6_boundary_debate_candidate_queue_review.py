import json
import subprocess
import pytest
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "review_v6_boundary_debate_candidate_queue.py"
REPORT_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_review_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_review_v1.md"


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


def test_v6_boundary_queue_review_summary_and_policy() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v6-boundary-debate-candidate-queue-review.v1"
    assert report["status"] == "review_ready_for_human_decision"
    assert report["source_queue"] == "build/v6_boundary_debate_candidate_queue_v1.json"
    assert report["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "candidate_queue_is_training_data": False,
        "review_measurement_is_gate": False,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_gate_use_allowed": False,
    }
    assert report["summary"] == {
        "queue_candidate_count": 48,
        "review_item_count": 48,
        "ready_item_count": 43,
        "held_item_count": 5,
        "exact_current_route_count": 26,
        "route_gap_count": 22,
        "priority_review_count": 9,
        "suppression_overfire_count": 10,
        "contrast_negative_repair_count": 18,
        "contrast_negative_priority_count": 3,
        "by_action": {
            "coverage_keep": 26,
            "hold_ladder_review": 5,
            "positive_current_counterpart_review": 2,
            "priority_contrast_negative_review": 2,
            "priority_suppression_review": 10,
            "route_gap_review": 3,
        },
        "by_target_set": {
            "contrast_negative_repair": 18,
            "current_search_split": 5,
            "false_positive_set": 5,
            "mixed_ja_en": 5,
            "no_risk_contrast": 5,
            "paraphrase_set": 5,
            "severity_ladder": 5,
        },
        "by_candidate_type": {
            "contrast_negative_repair": 17,
            "contrast_negative_repair_meta": 1,
            "current_search_positive": 2,
            "current_search_split": 3,
            "false_positive_suppression": 2,
            "metalinguistic_suppression": 3,
            "mixed_language_boundary": 5,
            "no_risk_contrast": 5,
            "paraphrase_coverage": 5,
            "severity_ladder_hold": 5,
        },
        "by_expected_risk": {"high": 1, "low": 41, "medium": 6},
        "error_field_counts": {
            "constraints": 10,
            "information_state": 11,
            "operations": 19,
            "primary_intent": 11,
            "risk": 12,
        },
        "top_priority_ids": [
            "v6-boundary-debate-queue-036",
            "v6-boundary-debate-queue-005",
            "v6-boundary-debate-queue-014",
            "v6-boundary-debate-queue-032",
            "v6-boundary-debate-queue-033",
            "v6-boundary-debate-queue-016",
            "v6-boundary-debate-queue-017",
            "v6-boundary-debate-queue-018",
            "v6-boundary-debate-queue-019",
        ],
    }


def test_v6_boundary_queue_review_prioritizes_remaining_overfire() -> None:
    report = _load(REPORT_PATH)
    by_id = {item["id"]: item for item in report["items"]}

    high_priority = [
        item
        for item in report["items"]
        if item["priority_score"] >= 9 and item["action"] != "hold_ladder_review"
    ]
    assert sorted(item["id"] for item in high_priority) == sorted(report["summary"]["top_priority_ids"])
    repair_high = [item for item in high_priority if item["target_set"] == "contrast_negative_repair"]
    assert [item["id"] for item in repair_high] == [
        "v6-boundary-debate-queue-032",
        "v6-boundary-debate-queue-033",
        "v6-boundary-debate-queue-036",
    ]

    medical_data = by_id["v6-boundary-debate-queue-038"]
    assert medical_data["source_topic_id"] == "repair-medical-data-design"
    assert medical_data["action"] == "coverage_keep"
    assert medical_data["fields"] == []

    license_label = by_id["v6-boundary-debate-queue-034"]
    assert license_label["source_topic_id"] == "repair-license-label-use"
    assert license_label["action"] == "coverage_keep"
    assert license_label["fields"] == []

    meta = by_id["v6-boundary-debate-queue-048"]
    assert meta["candidate_type"] == "contrast_negative_repair_meta"
    assert meta["action"] in {"coverage_keep", "route_gap_review", "priority_contrast_negative_review"}
    assert meta["training_allowed"] is False
    assert meta["gate_use_allowed"] is False


def test_v6_boundary_queue_review_keeps_ladders_held() -> None:
    report = _load(REPORT_PATH)
    held = [item for item in report["items"] if item["action"] == "hold_ladder_review"]

    assert len(held) == 5
    assert {item["target_set"] for item in held} == {"severity_ladder"}
    assert all(item["human_review_required"] is True for item in held)


def test_v6_boundary_queue_review_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Boundary Debate Candidate Queue Review v1" in text
    assert "priority_review_count: 9" in text
    assert "suppression_overfire_count: 10" in text
    assert "contrast_negative_priority_count: 3" in text
    assert "## Priority Review Items" in text
    assert "v6-boundary-debate-queue-038" not in text


def test_v6_boundary_queue_review_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "review_ready_for_human_decision" in completed.stdout
    report = _load(REPORT_PATH)
    assert report["summary"]["priority_review_count"] == 9
    assert report["summary"]["contrast_negative_priority_count"] == 3