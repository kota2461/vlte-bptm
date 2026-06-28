import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "build" / "prioritize_v8_recovery_debate_candidates.py"


def _candidate(topic_id: str, category: str, score: int) -> dict:
    return {
        "id": f"candidate-{topic_id}",
        "status": "usable_review_candidate",
        "selection_score": score,
        "source_topic_id": topic_id,
        "priority": "high",
        "recovery_focus": f"{category} recovery",
        "theme": f"{category} theme {topic_id}",
        "axis_ids": ["v8_recovery", "round4", category],
        "content_chars": 3000,
        "completed_rounds": 4,
        "cautions": [],
        "router_packet_hint": {},
        "desired_discussion": [],
        "training_status": "not_training_data",
    }


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_priority_selection_balances_categories_and_holds_length_finish(tmp_path: Path) -> None:
    selection_path = tmp_path / "selection.json"
    log_path = tmp_path / "run.json"
    output_path = tmp_path / "priority.json"
    worksheet_path = tmp_path / "priority.md"

    selection = {
        "schema_version": "v8-recovery-debate-candidate-selection.v1",
        "policy": {},
        "summary": {},
        "candidates": [
            _candidate("cat-a-01", "cat_a", 100),
            _candidate("cat-a-02", "cat_a", 95),
            _candidate("cat-a-03", "cat_a", 90),
            _candidate("cat-b-01", "cat_b", 100),
            _candidate("cat-b-02", "cat_b", 95),
            _candidate("cat-b-03", "cat_b", 90),
        ],
    }
    run = {
        "schema_version": "router-debate-run.v1",
        "topics": [
            {
                "topic_id": "cat-a-01",
                "turns": [{"role": "gemma_expander", "model": "gemma", "finish_reason": "length"}],
            },
            {"topic_id": "cat-a-02", "turns": [{"finish_reason": "stop"}]},
            {"topic_id": "cat-a-03", "turns": [{"finish_reason": "stop"}]},
            {"topic_id": "cat-b-01", "turns": [{"finish_reason": "stop"}]},
            {"topic_id": "cat-b-02", "turns": [{"finish_reason": "stop"}]},
            {"topic_id": "cat-b-03", "turns": [{"finish_reason": "stop"}]},
        ],
    }
    _write(selection_path, selection)
    _write(log_path, run)

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPT),
            "--selection-source",
            str(selection_path),
            "--source-log",
            str(log_path),
            "--output",
            str(output_path),
            "--worksheet",
            str(worksheet_path),
            "--per-category",
            "2",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "priority_review_queue_prepared" in completed.stdout
    priority = json.loads(output_path.read_text(encoding="utf-8"))
    assert priority["schema_version"] == "v8-recovery-debate-candidate-priority-selection.v1"
    assert priority["summary"]["priority_review_count"] == 4
    assert priority["summary"]["hold_for_rerun_count"] == 1
    assert priority["summary"]["priority_category_counts"] == {"cat_a": 2, "cat_b": 2}
    assert {record["source_topic_id"] for record in priority["priority_review"]} == {
        "cat-a-02",
        "cat-a-03",
        "cat-b-01",
        "cat-b-02",
    }
    assert priority["hold_for_rerun"][0]["source_topic_id"] == "cat-a-01"
    assert worksheet_path.read_text(encoding="utf-8").startswith("# V8 Recovery Debate Candidate Priority Selection v1")
