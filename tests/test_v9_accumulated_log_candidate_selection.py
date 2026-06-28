import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SELECTION_PATH = ROOT / "build" / "v9_accumulated_log_candidate_selection_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v9_accumulated_log_candidate_selection_v1.md"
SCRIPT_PATH = ROOT / "build" / "select_v9_accumulated_log_candidates.py"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v9_accumulated_log_selection_contract() -> None:
    selection = _load(SELECTION_PATH)

    assert selection["schema_version"] == "v9-accumulated-log-candidate-selection.v1"
    assert selection["status"] == "accumulated_log_candidates_selected_for_v9_review"
    assert selection["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "raw_debate_logs_direct_training_allowed": False,
        "llm_turn_text_direct_training_allowed": False,
        "selection_is_training_data": False,
        "human_rewrite_required_before_fixture_adoption": True,
        "human_review_required_before_gate": True,
        "same_cycle_gate_use_allowed": False,
    }
    assert selection["summary"]["source_candidate_count"] == 100
    assert selection["summary"]["already_used_v8_priority_count"] == 30
    assert selection["summary"]["ready_pool_count"] == 62
    assert selection["summary"]["primary_review_count"] == 34
    assert selection["summary"]["rerun_before_use_count"] == 8
    assert selection["summary"]["reserve_review_count"] == 28


def test_v9_selection_excludes_already_used_and_requires_rewrite() -> None:
    selection = _load(SELECTION_PATH)
    already_used = {row["id"] for row in selection["already_used_excluded"]}
    primary_ids = {row["id"] for row in selection["primary_review"]}
    rerun_ids = {row["id"] for row in selection["rerun_before_use"]}
    reserve_ids = {row["id"] for row in selection["reserve_review"]}

    assert primary_ids.isdisjoint(already_used)
    assert rerun_ids.isdisjoint(already_used)
    assert reserve_ids.isdisjoint(already_used)
    assert len(primary_ids | rerun_ids | reserve_ids | already_used) == 100
    for row in selection["primary_review"] + selection["rerun_before_use"] + selection["reserve_review"]:
        assert row["training_status"] == "not_training_data"
        assert row["allowed_use"] == "human_review_and_rewrite_only"
        assert "do not copy raw LLM prose" in row["rewrite_instruction"]


def test_v9_selection_prioritizes_v8_miss_categories() -> None:
    selection = _load(SELECTION_PATH)

    assert selection["summary"]["field_error_counts_from_v8"] == {
        "constraints": 6,
        "information_state": 6,
        "operations": 6,
        "primary_intent": 2,
        "risk": 6,
    }
    assert selection["summary"]["critical_miss_counts_from_v8"] == {
        "contains_unverified_claims": 0,
        "missing_required_information": 0,
        "multiple_intents": 1,
        "requires_current_information": 1,
    }
    assert selection["summary"]["primary_category_counts"] == {
        "constraints": 5,
        "current_search_split": 5,
        "false_positive": 2,
        "missing_info": 3,
        "mixed_language": 1,
        "multiple_intents": 5,
        "operation_terminal": 5,
        "paraphrase": 1,
        "risk_ladder": 5,
        "unverified_claim": 2,
    }


def test_v9_selection_script_regenerates_same_bucket_shape() -> None:
    spec = importlib.util.spec_from_file_location("select_v9_accumulated_log_candidates", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    generated = module.build_selection()
    persisted = _load(SELECTION_PATH)

    assert generated["summary"] == persisted["summary"]
    assert [row["id"] for row in generated["primary_review"]] == [
        row["id"] for row in persisted["primary_review"]
    ]


def test_v9_selection_worksheet_written_for_review() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "# V9 Accumulated Log Candidate Selection v1" in text
    assert "## Primary Review" in text
    assert "## Rerun Before Use" in text
    assert "Raw debate logs are not training data" in text
