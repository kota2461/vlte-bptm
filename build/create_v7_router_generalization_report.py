"""Create the V7 Step 4 router generalization report."""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "build"))

from semantic_routing import evaluate_plm_extractor
from semantic_routing.reproducibility import reproducible_now_iso
from semantic_routing.adapter import route
from semantic_routing.benchmark import parse_plm_benchmark
from v7_measurement_state import preserve_step8_measurement_state  # noqa: E402


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v7_router_repair_fixture_v1.json"
STEP3_REPORT_PATH = ROOT / "build" / "v7_router_repair_fixture_replay_v1.json"
REPORT_PATH = ROOT / "build" / "v7_router_generalization_report_v1.json"
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"

METRIC_KEYS = [
    "intent_accuracy",
    "critical_signal_recall",
    "operation_exact_match",
    "constraint_exact_match",
    "risk_exact_match",
]


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _field_counts(errors):
    counter = Counter(field for error in errors for field in error["fields"])
    return dict(sorted(counter.items()))


def _compact(measurement: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "case_count": measurement["case_count"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "error_count": len(measurement["errors"]),
        "error_field_counts": _field_counts(measurement["errors"]),
    }


def _benchmark_payload(fixture: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": "V7 Step 4 non-sealed router generalization check",
        "review_status": fixture["review_status"],
        "policy": "Diagnostic only; no sealed v6 fixture text or labels used.",
        "cases": [
            {
                "id": case["id"],
                "split": case["split"],
                "source_group": case["source_group"],
                "contrast_group": None,
                "language": case["language"],
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in fixture["cases"]
        ],
    }


def _measure(fixture: Dict[str, Any]) -> Dict[str, Any]:
    benchmark = parse_plm_benchmark(_benchmark_payload(fixture))
    return evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    fixture = _load(FIXTURE_PATH)
    step3_report = _load(STEP3_REPORT_PATH)
    before_full = step3_report["current_route_measurement"]
    before = _compact(before_full)
    after_full = _measure(fixture)
    after = _compact(after_full)
    delta = {key: round(after[key] - before[key], 6) for key in METRIC_KEYS}
    delta["error_count"] = after["error_count"] - before["error_count"]
    now = reproducible_now_iso()
    meets_step5_entry_threshold = (
        after["intent_accuracy"] >= 0.95
        and after["critical_signal_recall"] >= 0.90
        and after["operation_exact_match"] >= 0.90
        and after["constraint_exact_match"] >= 0.90
        and after["risk_exact_match"] >= 0.90
        and after["valid_packet_rate"] == 1.0
    )

    report = {
        "schema_version": "v7-router-generalization-report.v1",
        "generated_at": now,
        "status": "completed_not_a_gate",
        "policy": {
            "sealed_v6_text_used": False,
            "sealed_v6_labels_used": False,
            "source_fixture": "tests\\fixtures\\v7_router_repair_fixture_v1.json",
            "source_fixture_review_status": fixture["review_status"],
            "current_route_measurement_is_gate": False,
            "human_review_required_before_gate": True,
            "same_cycle_promotion_allowed": False,
        },
        "before": before,
        "after": after,
        "delta": delta,
        "remaining_errors": after_full["errors"],
        "change_summary": [
            "Added V7 generalized repair signals for missing scope, ask-first routing, current/source lookup, and low-risk term mentions.",
            "Preserved multi-operation routes for clarify-then-build, clarify-then-verify, build-then-verify, explore-then-compare, and source-backed verify.",
            "Expanded constraint preservation for response length, no_table/no_web_search, cite_sources, neutrality, general-information-only, and avoid-diagnosis.",
            "Calibrated risk so low-risk medical/legal words stay low while license checks, future/political/risk comparison, legal, medical, and security cases keep severity.",
            "Kept this replay diagnostic only; it is not sealed evidence and not promotion evidence.",
        ],
        "meets_step5_entry_threshold": meets_step5_entry_threshold,
        "next_step": {
            "step": 5,
            "name": "v7_nonsealed_replay_gate",
            "output": "build\\v7_nonsealed_replay_gate_report_v1.json",
        },
    }
    _write_json(REPORT_PATH, report)

    targets = _load(TARGETS_PATH)
    targets["generated_at"] = now
    targets["status"] = "step4_router_generalization_completed_step5_gate_next"
    for item in targets["roadmap"]:
        if item["step"] in {1, 2, 3, 4}:
            item["status"] = "completed"
        elif item["step"] == 5:
            item["status"] = "next"
        else:
            item["status"] = "pending"
    targets["next_action"] = "roadmap_v7_step5_nonsealed_replay_gate"
    targets["step4_router_generalization"] = {
        "output": "build\\v7_router_generalization_report_v1.json",
        "status": "completed_not_a_gate",
        "sealed_v6_text_used": False,
        "sealed_v6_labels_used": False,
        "current_route_measurement_is_gate": False,
        "before": before,
        "after": after,
        "delta": delta,
        "meets_step5_entry_threshold": meets_step5_entry_threshold,
    }
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | next |",
        "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | pending |",
        "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | next |",
    )
    step4_section = f"""
## Step 4 Output

`build\\v7_router_generalization_report_v1.json` is completed as a diagnostic, non-gate replay against the Step 3 non-sealed draft fixture. Before -> after: intent_accuracy {before['intent_accuracy']:.6f} -> {after['intent_accuracy']:.6f}, critical_signal_recall {before['critical_signal_recall']:.6f} -> {after['critical_signal_recall']:.6f}, operation_exact_match {before['operation_exact_match']:.6f} -> {after['operation_exact_match']:.6f}, constraint_exact_match {before['constraint_exact_match']:.6f} -> {after['constraint_exact_match']:.6f}, risk_exact_match {before['risk_exact_match']:.6f} -> {after['risk_exact_match']:.6f}, errors {before['error_count']} -> {after['error_count']}. Sealed v6 text and labels remain excluded. Step 5 is now the non-sealed replay gate.
""".strip()
    if "## Step 4 Output" in roadmap:
        head, _ = roadmap.split("## Step 4 Output", 1)
        roadmap = head.rstrip() + "\n\n" + step4_section + "\n"
    else:
        roadmap = roadmap.rstrip() + "\n\n" + step4_section + "\n"
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    marker = "## PLM V7: Constraint And Critical Signal Recovery"
    section = f"""
{marker}

Status: V7 Step 4 router generalization completed; Step 5 non-sealed replay gate next.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`
Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`
Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`
Router generalization report: `build/v7_router_generalization_report_v1.json`
Baseline sealed v6 measurement: `build/pattern_language_sealed_v6_measurement_report.json`

The V7 Step 4 router repair replays the 72-case non-sealed draft fixture diagnostically at intent_accuracy {after['intent_accuracy']:.6f}, critical_signal_recall {after['critical_signal_recall']:.6f}, operation_exact_match {after['operation_exact_match']:.6f}, constraint_exact_match {after['constraint_exact_match']:.6f}, risk_exact_match {after['risk_exact_match']:.6f}, with errors {after['error_count']}. This is not gate evidence; Step 5 must run the non-sealed replay gate before sealed v7 rotation.
""".strip()
    if marker in main:
        head, _ = main.split(marker, 1)
        main = head.rstrip() + "\n\n" + section + "\n"
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    targets, roadmap, main = preserve_step8_measurement_state(ROOT, targets, roadmap, main)
    _write_json(TARGETS_PATH, targets)
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")

    print(json.dumps({"report": str(REPORT_PATH.relative_to(ROOT)), "before": before, "after": after, "delta": delta}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()