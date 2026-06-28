import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[1]
TOPICS_PATH = ROOT / "debate_lab" / "topics_v8_recovery_100.json"
CONFIG_PATH = ROOT / "debate_lab" / "debate_config.json"
GENERATOR_PATH = ROOT / "build" / "create_v8_recovery_debate_stock.py"
EXTRACTOR_PATH = ROOT / "build" / "extract_v8_recovery_debate_candidates.py"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v8_recovery_topic_stock_has_100_round4_themes() -> None:
    payload = _load(TOPICS_PATH)
    topics = payload["topics"]
    counts = Counter(topic["axis_ids"][2] for topic in topics)

    assert payload["schema_version"] == "router-debate-topics.v1"
    assert payload["recommended_run"] == {
        "target_set": "v8_recovery_round4",
        "rounds": 4,
        "expected_topics": 100,
        "expected_turns": 800,
        "output": "build/v8_recovery_debate_r4_100.json",
    }
    assert len(topics) == 100
    assert len({topic["id"] for topic in topics}) == 100
    assert {topic["target_set"] for topic in topics} == {"v8_recovery_round4"}
    assert all(topic["training_status"] == "not_training_data" for topic in topics)
    assert all(topic["human_review_required"] is True for topic in topics)
    assert counts == {
        "constraints": 10,
        "current_search_split": 10,
        "false_positive": 10,
        "missing_info": 10,
        "mixed_language": 10,
        "multiple_intents": 10,
        "operation_terminal": 10,
        "paraphrase": 10,
        "risk_ladder": 10,
        "unverified_claim": 10,
    }


def test_v8_debate_config_defaults_to_round4_and_v7_weaknesses() -> None:
    config = _load(CONFIG_PATH)

    assert config["rounds"] == 4
    assert config["moderator"]["min_rounds"] == 4
    assert config["moderator"]["max_rounds"] == 4
    assert config["moderator_support"]["weak_metric_threshold"] == 0.8
    assert config["moderator_support"]["weak_metric_names"] == [
        "intent_accuracy",
        "critical_signal_recall",
        "operation_exact_match",
        "constraint_exact_match",
        "risk_exact_match",
    ]
    assert config["moderator_support"]["measured_weaknesses"]["source"] == "build/pattern_language_sealed_v7_measurement_report.json#sealed_v7"
    assert config["debate_goal"]["name"] == "v8_recovery_round4_boundary_calibration"


def test_v8_generator_regenerates_topic_stock() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(GENERATOR_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "wrote_v8_recovery_topics" in completed.stdout
    assert len(_load(TOPICS_PATH)["topics"]) == 100


def test_v8_dry_run_and_candidate_extractor(tmp_path: Path) -> None:
    run_path = tmp_path / "v8_recovery_dry_run.json"
    selection_path = tmp_path / "v8_recovery_selection.json"
    worksheet_path = tmp_path / "v8_recovery_selection.md"

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "debate_lab" / "router_debate.py"),
            "--dry-run",
            "--topics",
            str(TOPICS_PATH),
            "--target-set",
            "v8_recovery_round4",
            "--rounds",
            "4",
            "--max-topics",
            "2",
            "--output",
            str(run_path),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "wrote_router_debate_run" in completed.stdout
    run = _load(run_path)
    assert run["summary"]["topic_count"] == 2
    assert run["summary"]["turn_count"] == 16
    assert run["summary"]["moderator_comment_count"] == 8

    extracted = subprocess.run(
        [
            sys.executable,
            "-B",
            str(EXTRACTOR_PATH),
            "--source-log",
            str(run_path),
            "--topics",
            str(TOPICS_PATH),
            "--selection",
            str(selection_path),
            "--worksheet",
            str(worksheet_path),
            "--min-score",
            "30",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "candidate_queue_prepared_from_round4_debate_log" in extracted.stdout
    selection = _load(selection_path)
    assert selection["schema_version"] == "v8-recovery-debate-candidate-selection.v1"
    assert selection["summary"]["source_topic_count"] == 2
    assert selection["summary"]["candidate_count"] == 2
    assert selection["summary"]["turn_count"] == 16
    assert all(candidate["completed_rounds"] == 4 for candidate in selection["candidates"])
    assert worksheet_path.read_text(encoding="utf-8").startswith("# V8 Recovery Debate Candidate Review Worksheet v1")