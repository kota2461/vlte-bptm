import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "build" / "diagnose_v10_sealed_measurement_for_v11.py"
REPORT_PATH = ROOT / "build" / "v11_post_v10_measurement_diagnostic_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v11_post_v10_measurement_diagnostic_v1.md"


def _regenerate() -> None:
    """Regenerate the shared build/ artifact from its deterministic inputs.

    The report is an untracked artifact in build/ that multiple scripts write.
    Reading it without regenerating first makes these tests depend on whatever
    state a prior test or manual run left on disk (order-dependence). Running
    the generator here guarantees every read-assert below sees fresh, canonical
    output regardless of suite order.
    """
    subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


@pytest.fixture(scope="module", autouse=True)
def _regenerate_report():
    _regenerate()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v11_post_v10_diagnostic_records_policy_and_metric_regression() -> None:
    report = _load(REPORT_PATH)

    assert report["schema_version"] == "v11-post-v10-measurement-diagnostic.v1"
    assert report["status"] == "diagnostic_completed_v11_step1_ready"
    assert report["policy"] == {
        "sealed_v10_status": "consumed",
        "sealed_v10_labels_used_for_tuning": False,
        "sealed_v10_values_used_for_taxonomy_only": True,
        "diagnostic_is_training_data": False,
        "diagnostic_is_replay_gate": False,
        "same_cycle_promotion_allowed": False,
        "fresh_sealed_v11_required_before_next_adjudication": True,
    }
    assert report["metric_regression"] == {
        "intent_accuracy": {"v9": 0.892857, "v10": 0.785714, "delta_v10_minus_v9": -0.107143},
        "critical_signal_recall": {"v9": 0.857143, "v10": 0.4, "delta_v10_minus_v9": -0.457143},
        "operation_exact_match": {"v9": 0.821429, "v10": 0.642857, "delta_v10_minus_v9": -0.178572},
        "constraint_exact_match": {"v9": 0.642857, "v10": 0.535714, "delta_v10_minus_v9": -0.107143},
        "risk_exact_match": {"v9": 0.75, "v10": 0.678571, "delta_v10_minus_v9": -0.071429},
    }


def test_v11_post_v10_diagnostic_splits_failure_modes_and_value_diffs() -> None:
    report = _load(REPORT_PATH)
    summary = report["failure_mode_summary"]

    assert summary["mode_counts"] == {
        "intent_correct_field_mismatch": 17,
        "intent_mismatch": 6,
    }
    assert summary["critical_signal_misses"] == {
        "contains_unverified_claims": 1,
        "missing_required_information": 3,
        "multiple_intents": 5,
    }
    assert summary["intent_transitions"] == {
        "clarify->explore": 1,
        "clarify->respond": 1,
        "clarify->verify": 1,
        "explain->verify": 1,
        "explore->respond": 1,
        "respond->build": 1,
    }
    assert summary["field_value_diff_counts"]["information_state.multiple_intents"] == {
        "False -> True": 2,
        "True -> False": 5,
    }
    assert summary["field_value_diff_counts"]["constraints.must"]["['avoid_overclaim'] -> []"] == 1
    assert len(report["case_diagnostics"]) == 23
    first = report["case_diagnostics"][0]
    assert first["mode"] in {"intent_correct_field_mismatch", "intent_mismatch"}
    assert first["value_diff"]
    assert "trace" in first


def test_v11_post_v10_diagnostic_records_bridge_transfer_gap() -> None:
    report = _load(REPORT_PATH)
    gap = report["bridge_transfer_diagnostic"]["distribution_gap"]

    assert gap["bridge_template_overfit_risk"] is True
    assert gap["language_shift"] == {
        "bridge": {"en": 72},
        "sealed_v10": {"en": 14, "ja": 14},
    }
    assert gap["style_marker_delta_sealed_minus_bridge"]["synthetic_bridge_prefix_rate"] == -1.0
    assert gap["style_marker_delta_sealed_minus_bridge"]["japanese_script_rate"] == 0.5
    assert report["bridge_transfer_diagnostic"]["bridge_distribution"]["style_markers"]["synthetic_bridge_prefix_rate"] == 1.0
    assert report["bridge_transfer_diagnostic"]["sealed_v10_distribution"]["style_markers"]["synthetic_bridge_prefix_rate"] == 0.0


def test_v11_post_v10_diagnostic_focus_areas_and_script_regenerate() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_PATH)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "diagnostic_completed_v11_step1_ready" in completed.stdout

    report = _load(REPORT_PATH)
    report_md = REPORT_MD_PATH.read_text(encoding="utf-8")
    assert [item["id"] for item in report["focus_areas"]] == [
        "value_level_diff_instrumentation",
        "clarify_boundary_collapse",
        "multiple_intent_under_detection",
        "bridge_non_transfer",
        "intent_correct_field_mismatch_lane",
    ]
    assert report["next_action"] == "roadmap_v11_step1_build_taxonomy_from_value_diff_and_transfer_gap"
    assert "V11 Post-V10 Measurement Diagnostic v1" in report_md
    assert "bridge_template_overfit_risk" in report_md
