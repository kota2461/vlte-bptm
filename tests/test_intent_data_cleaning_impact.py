import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPORT_PATH = ROOT / "build" / "intent_data_cleaning_impact_v1.json"
WORKSHEET_PATH = ROOT / "build" / "intent_data_cleaning_impact_v1.md"


def _load_report():
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def test_intent_data_cleaning_impact_is_diagnostic_only() -> None:
    report = _load_report()

    assert report["schema_version"] == "intent-data-cleaning-impact.v1"
    assert report["policy"]["diagnostic_only"] is True
    assert report["policy"]["sealed_fixtures_used"] is False
    assert report["policy"]["writes_training_corpus"] is False
    assert report["policy"]["writes_deployed_model"] is False
    assert report["policy"]["writes_candidate_model"] is False
    assert report["policy"]["same_batch_tuning"] is False

    for path in report["inputs"].values():
        assert "sealed" not in path.lower()


def test_intent_data_cleaning_scenarios_are_reviewable_ablations() -> None:
    report = _load_report()
    scenarios = {item["name"]: item for item in report["scenario_ablations"]}

    assert report["baseline"]["filtered_examples"] > 0
    assert report["suspect_review"]["suspect_count"] > 0
    assert report["suspect_review"]["high_priority_count"] > 0
    assert "high_priority_actionable" in scenarios
    assert "all_suspects_diagnostic" in scenarios

    for scenario in scenarios.values():
        assert scenario["removed_count"] == len(scenario["removed_indices"])
        assert scenario["removed_count"] > 0
        assert len(scenario["removed_indices"]) == len(set(scenario["removed_indices"]))
        assert scenario["proposed_action"] != "delete"
        assert set(scenario["delta_vs_baseline"]) == {
            "kfold_accuracy",
            "kfold_macro_accuracy",
            "accumulation_end_to_end_accuracy",
            "accumulation_failed",
            "critical_underprocessing",
        }
        assert set(scenario["accumulation_route_eval"]) == {
            "case_count",
            "reviewed_count",
            "semantic_intent_accuracy",
            "processing_plan_accuracy",
            "end_to_end_route_accuracy",
            "passed",
            "failed",
            "critical_underprocessing",
            "category_failures",
        }

    assert (
        scenarios["all_suspects_diagnostic"]["evidence_label"]
        == "diagnostic_only_too_broad"
    )


def test_high_priority_rows_have_individual_ablation_evidence() -> None:
    report = _load_report()
    rows = report["individual_high_priority"]

    assert len(rows) == report["suspect_review"]["high_priority_count"]
    for item in rows:
        assert item["removed_count"] == 1
        assert item["row"]["recommendation"] in {
            "exclude",
            "exclude_or_negative",
            "exclude_or_relabel_clarify",
        }
        assert item["row"]["corpus_index"] == item["removed_indices"][0]
        assert item["evidence_label"] in {
            "adoptable_quarantine_candidate",
            "neutral_but_safe_review_candidate",
            "needs_more_evidence_before_removal",
            "reject_gate_regression",
        }


def test_intent_data_cleaning_worksheet_explains_quarantine_rule() -> None:
    worksheet = WORKSHEET_PATH.read_text(encoding="utf-8")

    assert "Diagnostic only" in worksheet
    assert "Scenario Ablations" in worksheet
    assert "Individual High-Priority Rows" in worksheet
    assert "adoptable_quarantine_candidate" in worksheet
    assert "quarantine" in worksheet
