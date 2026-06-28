import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "select_v6_boundary_debate_logs.py"
SELECTION_PATH = ROOT / "build" / "v6_boundary_debate_log_selection_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_debate_log_selection_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v6_boundary_debate_log_selection_artifact_is_consistent() -> None:
    payload = _load(SELECTION_PATH)

    assert payload["schema_version"] == "v6-boundary-debate-log-selection.v1"
    assert payload["status"] == "selection_ready_for_human_review"
    assert payload["source_log"] == "build/router_debate_live_31stock_r3.json"
    assert payload["summary"]["source_topic_count"] == 18
    assert payload["summary"]["source_turn_count"] == 144
    assert payload["summary"]["selected_primary_count"] == 15
    assert payload["summary"]["selected_secondary_count"] == 3
    assert payload["summary"]["held_ladder_count"] == 0
    assert payload["summary"]["quality_issue_count"] == 0
    assert payload["summary"]["immediate_focus_match_count"] >= 9
    assert len(payload["items"]) == 18


def test_v6_boundary_debate_log_selection_keeps_raw_logs_review_only() -> None:
    payload = _load(SELECTION_PATH)

    assert payload["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "topic_metadata_selection_allowed": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_gate_use_allowed": False,
    }
    assert all(item["training_allowed"] is False for item in payload["items"])
    assert all(item["gate_use_allowed"] is False for item in payload["items"])
    assert all(item["allowed_use"] == "review_only_log_selection" for item in payload["items"])


def test_v6_boundary_debate_log_selection_prioritizes_requested_focus_topics() -> None:
    payload = _load(SELECTION_PATH)
    by_id = {item["topic_id"]: item for item in payload["items"]}

    requested_focus_ids = {
        "fp-ai-light-chat-healing",
        "paraphrase-ai-light-support",
        "paraphrase-apache-general-question",
        "paraphrase-medical-ui-design",
        "contrast-ai-word-only-low-risk",
        "contrast-medical-word-only-low-risk",
        "mixed-apache-general-ja-en",
        "mixed-medical-ui-ja-en",
    }
    assert requested_focus_ids <= set(by_id)
    for topic_id in requested_focus_ids:
        assert by_id[topic_id]["immediate_focus_match"] is True
        assert by_id[topic_id]["decision"] in {
            "select_primary_review",
            "select_secondary_review",
        }


def test_v6_boundary_debate_log_selection_quality_and_sections_are_complete() -> None:
    payload = _load(SELECTION_PATH)

    for item in payload["items"]:
        assert item["health"]["turn_count"] == 8
        assert item["health"]["closed"] is True
        assert item["health"]["all_turns_content"] is True
        assert item["health"]["reasoning_content_chars"] == 0
        assert item["health"]["min_turn_chars"] > 0
        assert all(item["section_hits"].values())


def test_v6_boundary_debate_log_selection_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Boundary Debate Log Selection v1" in text
    assert "selected_primary_count: 15" in text
    assert "selected_secondary_count: 3" in text
    assert "held_ladder_count: 0" in text
    assert "fp-ai-light-chat-healing" in text
    assert "paraphrase-apache-general-question" in text
    assert "paraphrase-medical-ui-design" in text


def test_v6_boundary_debate_log_selection_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "selection_ready_for_human_review" in completed.stdout
    payload = _load(SELECTION_PATH)
    assert payload["summary"]["selected_primary_count"] == 15
    assert payload["summary"]["held_ladder_count"] == 0