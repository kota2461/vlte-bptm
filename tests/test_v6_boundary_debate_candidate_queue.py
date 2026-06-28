import json
import subprocess
import pytest
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "append_v6_contrast_negative_repair_candidate_queue.py"
QUEUE_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_v1.md"


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


def test_v6_boundary_candidate_queue_is_candidate_only() -> None:
    payload = _load(QUEUE_PATH)

    assert payload["schema_version"] == "v6-boundary-debate-candidate-queue.v1"
    assert payload["status"] == "candidate_queue_ready_for_human_review"
    assert payload["source_log"] == "build/router_debate_live_31stock_r3.json"
    assert payload["repair_source_log"] == "build/router_debate_live_contrast_negative_repair_r1.json"
    assert payload["source_logs"] == [
        "build/router_debate_live_31stock_r3.json",
        "build/router_debate_live_contrast_negative_repair_r1.json",
    ]
    assert payload["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "topic_metadata_synthesis_used": True,
        "human_review_required_before_training": True,
        "human_review_required_before_gate": True,
        "same_cycle_gate_use_allowed": False,
        "candidate_queue_is_training_data": False,
    }
    assert all(candidate["training_allowed"] is False for candidate in payload["candidates"])
    assert all(candidate["gate_use_allowed"] is False for candidate in payload["candidates"])
    assert all(candidate["human_review_required"] is True for candidate in payload["candidates"])


def test_v6_boundary_candidate_queue_contains_base_30_plus_repair_18() -> None:
    payload = _load(QUEUE_PATH)
    summary = payload["summary"]

    assert summary["source_topic_count"] == 48
    assert summary["base_candidate_count"] == 30
    assert summary["repair_source_topic_count"] == 18
    assert summary["repair_source_turn_count"] == 72
    assert summary["candidate_count"] == 48
    assert summary["ready_for_human_review_count"] == 43
    assert summary["held_count"] == 5
    assert summary["future_append_target_set"] == "contrast_negative_repair"
    assert summary["future_append_expected_count"] == 18
    assert summary["contrast_negative_repair_included"] == 18
    assert payload["append_plan"] == {
        "status": "contrast_negative_repair_appended",
        "target_set": "contrast_negative_repair",
        "appended_count": 18,
        "source_log": "build/router_debate_live_contrast_negative_repair_r1.json",
    }
    assert sum(1 for candidate in payload["candidates"] if candidate["target_set"] == "contrast_negative_repair") == 18


def test_v6_boundary_candidate_queue_marks_ladder_and_length_notes() -> None:
    payload = _load(QUEUE_PATH)
    by_topic = {candidate["source_topic_id"]: candidate for candidate in payload["candidates"]}

    assert payload["summary"]["by_status"] == {
        "hold_for_later_ladder_review": 5,
        "ready_for_human_review": 43,
    }
    assert payload["summary"]["length_finish_candidate_count"] == 2
    assert set(payload["summary"]["length_finish_candidates"]) == {
        "current-local-folder-no-search",
        "severity-ai-dependency-ladder",
    }
    assert by_topic["severity-medical-ladder"]["status"] == "hold_for_later_ladder_review"
    assert by_topic["current-ai-regulation-requires-search"]["status"] == "ready_for_human_review"
    assert by_topic["current-ai-regulation-requires-search"]["suggested_expected"]["information_state"]["requires_current_information"] is True


def test_v6_boundary_candidate_queue_has_reviewable_prompts() -> None:
    payload = _load(QUEUE_PATH)
    by_topic = {candidate["source_topic_id"]: candidate for candidate in payload["candidates"]}

    assert by_topic["fp-ai-light-chat-healing"]["prompt"].startswith("I chat with an AI")
    assert by_topic["paraphrase-apache-general-question"]["suggested_expected"]["primary_intent"] == "explain"
    assert by_topic["paraphrase-medical-ui-design"]["suggested_expected"]["primary_intent"] == "build"
    assert by_topic["current-model-benchmark-requires-sources"]["suggested_expected"]["risk"]["level"] == "medium"
    assert by_topic["repair-license-label-use"]["prompt"].startswith("Save the text 'Apache 2.0'")
    assert by_topic["repair-medical-word-translation"]["suggested_expected"]["primary_intent"] == "respond"
    assert by_topic["repair-negative-positive-counterpair-matrix"]["candidate_type"] == "contrast_negative_repair_meta"
    assert all(candidate["raw_turn_text_direct_training_allowed"] is False for candidate in payload["candidates"])


def test_v6_boundary_candidate_queue_repair_log_is_clean() -> None:
    payload = _load(QUEUE_PATH)
    repair_candidates = [
        candidate
        for candidate in payload["candidates"]
        if candidate["target_set"] == "contrast_negative_repair"
    ]

    assert len(repair_candidates) == 18
    assert repair_candidates[0]["id"] == "v6-boundary-debate-queue-031"
    assert repair_candidates[-1]["id"] == "v6-boundary-debate-queue-048"
    for candidate in repair_candidates:
        health = candidate["debate_health"]
        assert candidate["status"] == "ready_for_human_review"
        assert health["turn_count"] == 4
        assert health["closed"] is True
        assert health["all_turns_content"] is True
        assert health["reasoning_content_chars"] == 0
        assert health["finish_reasons"] == {"stop": 4}


def test_v6_boundary_candidate_queue_worksheet_exists() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "V6 Boundary Debate Candidate Queue v1" in text
    assert "candidate_count: 48" in text
    assert "ready_for_human_review_count: 43" in text
    assert "contrast_negative_repair_included: 18" in text
    assert "appended target: contrast_negative_repair / 18 topics" in text
    assert "v6-boundary-debate-queue-001" in text
    assert "v6-boundary-debate-queue-048" in text
    assert "repair-regulation-label-use" in text


def test_v6_boundary_candidate_queue_script_regenerates_artifacts() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "candidate_queue_ready_for_human_review" in completed.stdout
    payload = _load(QUEUE_PATH)
    assert payload["summary"]["candidate_count"] == 48
    assert payload["summary"]["contrast_negative_repair_included"] == 18