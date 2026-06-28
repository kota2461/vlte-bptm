import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "select_v10_thought_color_bridge_candidates.py"
SELECTION_PATH = ROOT / "build" / "v10_thought_color_bridge_candidate_selection_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v10_thought_color_bridge_review_worksheet_v1.md"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v10_thought_color_bridge_selection_contract() -> None:
    selection = _load(SELECTION_PATH)

    assert selection["schema_version"] == "v10-thought-color-bridge-candidate-selection.v1"
    assert selection["status"] == "thought_color_bridge_candidates_selected_for_v10_review"
    assert selection["policy"] == {
        "source_scope": "thought_color_experiment_only",
        "source_mainline_training_allowed": False,
        "source_experiment_training_allowed": True,
        "sealed_fixtures_used_as_sources": False,
        "sealed_text_used": False,
        "sealed_labels_used": False,
        "bridge_selection_is_training_data": False,
        "raw_thought_color_samples_direct_training_allowed": False,
        "human_review_required_before_fixture_adoption": True,
        "human_rewrite_required_before_gate": True,
        "same_cycle_gate_use_allowed": False,
    }
    assert selection["summary"]["source_sample_count"] == 373
    assert selection["summary"]["primary_review_count"] == 72
    assert selection["summary"]["primary_category_counts"] == {
        "constraint_bridge": 18,
        "information_state_bridge": 14,
        "intent_boundary_bridge": 10,
        "operation_bridge": 14,
        "risk_bridge": 16,
    }


def test_v10_bridge_candidates_are_review_only_and_unique_primary_inputs() -> None:
    selection = _load(SELECTION_PATH)
    primary = selection["primary_review"]
    inputs = [" ".join(row["input"].split()).lower() for row in primary]

    assert len(inputs) == len(set(inputs))
    for row in primary:
        assert row["selection_bucket"] == "primary_review"
    for row in selection["reserve_review"]:
        assert row["selection_bucket"] == "reserve_review"
    for row in primary + selection["reserve_review"]:
        assert row["training_status"] == "not_training_data"
        assert row["allowed_use"] == "mainline_bridge_review_only"
        assert row["human_review_required"] is True
        assert "semantic_packet_bridge_hint" in row
        assert "Rewrite into a short self-contained" in row["rewrite_instruction"]


def test_v10_bridge_selection_uses_v9_failure_taxonomy() -> None:
    selection = _load(SELECTION_PATH)

    assert selection["summary"]["v9_error_field_counts"] == {
        "constraints": 10,
        "information_state": 6,
        "operations": 5,
        "primary_intent": 3,
        "risk": 7,
    }
    assert selection["summary"]["v9_critical_miss_counts"] == {
        "contains_unverified_claims": 1,
        "missing_required_information": 0,
        "multiple_intents": 1,
        "requires_current_information": 0,
    }
    assert selection["summary"]["category_deficits"] == {}


def test_v10_bridge_script_regenerates_same_selection_shape() -> None:
    spec = importlib.util.spec_from_file_location("select_v10_thought_color_bridge_candidates", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    generated = module.build_selection()
    persisted = _load(SELECTION_PATH)

    assert generated["summary"] == persisted["summary"]
    assert [row["source_sample_id"] for row in generated["primary_review"]] == [
        row["source_sample_id"] for row in persisted["primary_review"]
    ]


def test_v10_bridge_worksheet_written_for_human_review() -> None:
    text = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "# V10 Thought Color Bridge Review Worksheet v1" in text
    assert "## Primary Review" in text
    assert "## Primary Inputs For Rewrite" in text
    assert "training_status: not_training_data" in text
    assert "source_mainline_training_allowed: false" in text
