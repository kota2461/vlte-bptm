import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "find_intent_pruning_candidates_post_quarantine.py"
REPORT_PATH = ROOT / "build" / "intent_pruning_candidates_post_quarantine_v1.json"
WORKSHEET_PATH = ROOT / "build" / "intent_pruning_candidates_post_quarantine_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_post_quarantine_pruning_report_records_safe_hold_decision() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "intent-pruning-candidates-post-quarantine.v1"
    assert report["policy"] == {
        "diagnostic_only": True,
        "sealed_fixtures_used": False,
        "writes_training_corpus": False,
        "writes_quarantine_overlay": False,
        "recommended_workflow": "human review -> quarantine/rewrite -> non-sealed replay -> rebuild/gate",
    }
    assert report["active_quarantine"]["entry_count"] == 9
    assert report["active_baseline"]["filtered_examples"] == 730
    assert report["summary"] == {
        "remaining_candidate_count": 38,
        "high_priority_count": 21,
        "rewrite_or_anonymize_count": 13,
        "weak_question_count": 8,
        "manual_review_count": 0,
        "very_short_anchor_count": 17,
    }
    scenarios = {item["name"]: item for item in report["scenario_ablations"]}
    assert scenarios["rewrite_or_anonymize_path"]["candidate_count"] == 13
    assert scenarios["weak_question_holdout"]["candidate_count"] == 8
    assert scenarios["very_short_anchor_control"]["candidate_count"] == 17
    assert scenarios["all_high_priority_remaining"]["candidate_count"] == 21
    assert all(item["evidence_label"] == "keep_until_more_evidence" for item in scenarios.values())
    assert all(row["evidence_label"] == "keep_until_more_evidence" for row in report["high_priority_rows"])


def test_post_quarantine_pruning_worksheet_and_script_regenerate() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")
    assert "Intent Pruning Candidates Post Quarantine v1" in text
    assert "remaining suspect candidates: 38" in text
    assert "rewrite/anonymize path candidates: 13" in text
    assert "keep_until_more_evidence" in text

    compile(SCRIPT_PATH.read_text(encoding="utf-8"), str(SCRIPT_PATH), "exec")
    report = _load(REPORT_PATH)
    assert report["summary"]["high_priority_count"] == 21