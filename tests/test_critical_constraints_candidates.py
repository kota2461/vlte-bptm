import json
from pathlib import Path

from semantic_routing import route


ROOT = Path(__file__).parents[1]
REPORT_PATH = ROOT / "build" / "critical_constraints_candidates_v1.json"
WORKSHEET_PATH = (
    ROOT / "build" / "critical_constraints_review_worksheet_v1.md"
)


def test_critical_constraints_candidate_report_uses_only_non_sealed_sources() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["schema_version"] == "critical-constraints-candidates.v1"
    assert report["policy"]["sealed_fixtures_used"] is False
    assert report["summary"]["unique_inputs_scanned"] > 0
    assert report["summary"]["candidate_count"] > 0
    assert report["summary"]["review_candidate_count"] > 0
    assert report["summary"]["probe_candidate_count"] > 0
    assert set(report["summary"]["by_priority"]) >= {"A", "B", "C"}

    for source in report["sources"]:
        assert "sealed" not in source["path"].lower()

    for candidate in report["candidates"]:
        assert candidate["review_status"] == "pending"
        assert candidate["priority"] in {"A", "B", "C"}
        assert candidate["draft_expected"]["primary_intent"]
        for origin in candidate["origins"]:
            assert "sealed" not in origin["source_path"].lower()


def test_critical_constraints_worksheet_is_review_focused() -> None:
    worksheet = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "Sealed fixtures are not input sources" in worksheet
    assert "review candidates (A+B)" in worksheet
    assert "probe candidates (C)" in worksheet
    assert "Priority A - Critical Signals" in worksheet
    assert "Priority B - Constraints / Operations" in worksheet
    assert "Showing first 50" in worksheet


def test_critical_constraints_candidates_replay_current_draft_labels() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    for candidate in report["candidates"]:
        packet = route(candidate["input"]).packet
        expected = candidate["draft_expected"]

        assert packet.primary_intent == expected["primary_intent"]
        assert list(packet.operations) == expected["operations"]
        assert packet.information_state.as_dict() == expected[
            "information_state"
        ]
        assert packet.constraints.as_dict() == expected["constraints"]
        assert packet.risk.as_dict() == expected["risk"]
