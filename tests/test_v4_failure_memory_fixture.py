import json
from pathlib import Path

from semantic_routing import route


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
SELECTION_PATH = ROOT / "build" / "v4_failure_memory_selection_recommendation_v1.json"
REPLAY_PATH = ROOT / "build" / "v4_failure_memory_replay_v1.json"
GUARD_REPORT_PATH = ROOT / "build" / "v4_guard_relabel_implementation_report.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v4_failure_memory_fixture_is_nonsealed_guard_lane() -> None:
    fixture = _load(FIXTURE_PATH)
    selection = _load(SELECTION_PATH)

    assert fixture["schema_version"] == "v4-failure-memory-fixture.v1"
    assert fixture["status"] == "adopted_for_nonsealed_replay"
    assert fixture["policy"]["sealed_fixtures_used_as_sources"] is False
    assert fixture["policy"]["sealed_text_used"] is False
    assert fixture["policy"]["success_pattern_lane_write_allowed"] is False
    assert fixture["summary"]["item_count"] == selection["summary"]["selected_count"]
    assert fixture["summary"]["item_count"] == 38

    for source in fixture["sources"]:
        assert source["sealed"] is False
        assert "sealed" not in source["path"].lower()

    source_ids = {item["source_candidate_id"] for item in fixture["items"]}
    assert "cc-open-v1-057" not in source_ids

    for item in fixture["items"]:
        assert item["human_review_status"] == "approved_for_failure_memory_fixture"
        assert item["training_status"] == "not_training_data"
        assert item["allowed_use"] == "nonsealed_failure_memory_replay_only"
        assert item["success_pattern_write_allowed"] is False
        assert item["guard_action"]
        assert item["bad_tendency"]
        assert "sealed" not in item["source_path"].lower()


def test_v4_failure_memory_context_pair_keeps_previous_log_as_memo() -> None:
    fixture = _load(FIXTURE_PATH)
    item = next(
        row for row in fixture["items"]
        if row["source_candidate_id"] == "cc-open-v1-038"
    )

    assert item["mode"] == "context_pair"
    assert item["context_pair_pattern"] == "previous_error_report_then_verify_check_request"
    assert len(item["context"]) == 1
    assert item["context"][0]["role"] == "previous_log_memo"
    assert item["context"][0]["intent"] == "respond"
    assert "inspect_error_context" in item["guard_action"]
    assert "avoid_status_only_response" in item["guard_action"]
    assert item["trigger_packet"]["primary_intent"] == "verify"


def test_v4_failure_memory_replay_matches_current_route() -> None:
    fixture = _load(FIXTURE_PATH)
    replay = _load(REPLAY_PATH)

    assert replay["schema_version"] == "v4-failure-memory-replay.v1"
    assert replay["summary"]["item_count"] == fixture["summary"]["item_count"]
    assert replay["summary"]["exact_match_count"] == fixture["summary"]["item_count"]
    assert replay["summary"]["miss_count"] == 0
    assert replay["summary"]["exact_match_rate"] == 1.0



def test_v4_failure_memory_guard_actions_are_exposed_by_route_trace() -> None:
    fixture = _load(FIXTURE_PATH)

    for item in fixture["items"]:
        result = route(item["input"])
        guard = result.trace["failure_guard"]

        assert set(item["guard_action"]) <= set(guard["guard_actions"])
        assert guard["severity"] in {"minor", "medium", "major"}
        assert guard["relabel_hints"]
        assert "success" not in json.dumps(guard)


def test_v4_guard_relabel_report_covers_failure_memory_fixture() -> None:
    fixture = _load(FIXTURE_PATH)
    report = _load(GUARD_REPORT_PATH)

    assert report["schema_version"] == "v4-guard-relabel-implementation-report.v1"
    assert report["policy"]["sealed_fixtures_used_as_sources"] is False
    assert report["policy"]["success_pattern_lane_write_allowed"] is False
    assert report["policy"]["packet_rewrite_allowed"] is False
    assert report["summary"]["item_count"] == fixture["summary"]["item_count"]
    assert report["summary"]["guard_subset_match_count"] == fixture["summary"]["item_count"]
    assert report["summary"]["guard_subset_match_rate"] == 1.0
