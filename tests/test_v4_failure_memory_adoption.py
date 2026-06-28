import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V4_ROADMAP.md"


def test_v4_failure_memory_adoption_policy_keeps_sealed_text_out() -> None:
    payload = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "v4-failure-memory-adoption.v1"
    assert payload["status"] == "v4_sealed_measured_consumed_rotation_required"
    assert payload["policy"]["sealed_fixtures_used_as_sources"] is False
    assert payload["policy"]["v3_sealed_text_used_for_training"] is False
    assert payload["policy"]["v3_sealed_errors_used_as_taxonomy_only"] is True
    assert payload["policy"]["success_pattern_lane_write_allowed"] is False

    for group_name in ("suspect_review", "ablation_misses", "critical_candidate_refs"):
        for item in payload["items"][group_name]:
            assert "sealed" not in item["source_path"].lower()

    for item in payload["items"]["v3_error_taxonomy"]:
        assert "input" not in item
        assert item["allowed_use"] == "error_taxonomy_only_no_sealed_text_for_training"


def test_v4_failure_memory_adoption_has_reviewable_lanes() -> None:
    payload = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
    lanes = payload["adoption_lanes"]
    summary = payload["summary"]

    assert "negative_calibration" in lanes
    assert "clarify_relabel_guard" in lanes
    assert "critical_constraints_review" in lanes
    assert "puzzle_failure_memory" in lanes
    assert summary["suspect_review_items"] == 12
    assert summary["ablation_miss_items"] == 11
    assert summary["critical_candidate_refs"] == 60
    assert summary["v3_error_taxonomy_items"] == 8
    assert summary["selected_for_failure_memory_fixture"] == 38
    assert summary["context_pair_adoptions"] == 1

    review_decision = payload["review_decision"]
    assert review_decision["guard_relabel_total"] == 38
    assert review_decision["guard_relabel_subset_matches"] == 38
    assert review_decision["guard_relabel_report"] == "build\\v4_guard_relabel_implementation_report.json"
    assert review_decision["v4_sealed_measurement_report"] == "build\\pattern_language_sealed_v4_measurement_report.json"


def test_v4_roadmap_mentions_adoption_and_puzzle_learning() -> None:
    text = ROADMAP_PATH.read_text(encoding="utf-8")

    assert "v4_failure_memory_adoption_v1.json" in text
    assert "Puzzle Learning Integration" in text
    assert "intent_accuracy | 0.857143 | 0.900000" in text
