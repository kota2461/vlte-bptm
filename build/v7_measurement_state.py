"""Preserve the post-Step 8 V7 measurement state across replay scripts."""

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for error in errors:
        for field in error["fields"]:
            counts[field] = counts.get(field, 0) + 1
    return dict(sorted(counts.items()))


def _critical_signal_miss_count(signals: dict[str, dict[str, Any]]) -> int:
    misses = 0
    for signal in signals.values():
        support = signal["support"]
        recall = signal["recall"]
        misses += round(support * (1.0 - recall))
    return misses


def existing_step8_measurement(root: Path) -> dict[str, Any] | None:
    report_path = root / "build" / "pattern_language_sealed_v7_measurement_report.json"
    if not report_path.exists():
        return None
    report = _load_json(report_path)
    if report.get("schema_version") != "plm-sealed-measurement-report.v1":
        return None
    if report.get("fixture", {}).get("registry_name") != "pattern_language_sealed_v7.json":
        return None
    if report.get("registry_update", {}).get("status_after_measurement") != "consumed":
        return None
    return report


def preserve_step8_measurement_state(
    root: Path,
    targets: dict[str, Any],
    roadmap: str,
    main: str,
) -> tuple[dict[str, Any], str, str]:
    measurement = existing_step8_measurement(root)
    if measurement is None:
        return targets, roadmap, main

    metrics = measurement["measurements"]
    field_counts = _field_counts(metrics["errors"])
    critical_signal_miss_count = _critical_signal_miss_count(metrics["critical_signals"])

    targets["status"] = "step8_sealed_v7_measurement_completed_v8_rotation_required"
    targets["next_action"] = "roadmap_v8_step1_post_v7_measurement_taxonomy"
    for item in targets["roadmap"]:
        item["status"] = "completed"

    generalization_path = root / "build" / "v7_router_generalization_report_v1.json"
    if generalization_path.exists():
        generalization = _load_json(generalization_path)
        targets["step4_router_generalization"] = {
            "output": "build\\v7_router_generalization_report_v1.json",
            "meets_step5_entry_threshold": generalization["meets_step5_entry_threshold"],
            "before": generalization["before"],
            "after": generalization["after"],
            "delta": generalization["delta"],
        }

    targets["step8_sealed_measurement"] = {
        "output": "build\\pattern_language_sealed_v7_measurement_report.json",
        "summary": "build\\v7_step8_measurement_summary.md",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v7.json",
        "sealed_fixture_opened": measurement["sealed_fixture_opened"],
        "sealed_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
        "passed_minimum": False,
        "minimum_metrics_met": False,
        "critical_signal_miss_count": critical_signal_miss_count,
        "critical_signal_miss_gate_met": critical_signal_miss_count <= 4,
        "rotation_required_before_tuning": measurement["registry_update"][
            "rotation_required_before_tuning"
        ],
        "readiness_after_measurement": {
            "decision": "blocked",
            "blocked_reasons": ["sealed_fixture_not_available"],
            "sealed_fixture": None,
        },
        "measurements": {
            "case_count": metrics["case_count"],
            "intent_accuracy": metrics["intent_accuracy"],
            "intent_macro_f1": metrics["intent_macro_f1"],
            "critical_signal_recall": metrics["critical_signal_recall"],
            "operation_exact_match": metrics["operation_exact_match"],
            "constraint_exact_match": metrics["constraint_exact_match"],
            "risk_exact_match": metrics["risk_exact_match"],
            "valid_packet_rate": metrics["valid_packet_rate"],
            "evidence_offset_validity": metrics["evidence_offset_validity"],
            "error_count": len(metrics["errors"]),
            "error_field_counts": field_counts,
        },
    }

    table_replacements = {
        "| 1 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | next |": "| 1 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | completed |",
        "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | next |": "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | completed |",
        "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | next |": "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | completed |",
        "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | next |": "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | completed |",
        "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | next |": "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | completed |",
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | next |": "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |",
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | next |": "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |",
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | next |": "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | completed |",
        "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | pending |": "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | completed |",
        "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | pending |": "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | completed |",
        "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | pending |": "| 4 | v7_router_generalization_changes | `build\\v7_router_generalization_report_v1.json` | completed |",
        "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | pending |": "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | completed |",
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | pending |": "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |",
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | pending |": "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |",
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | pending |": "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | completed |",
    }
    for before, after in table_replacements.items():
        roadmap = roadmap.replace(before, after)

    if "## Step 8 Output" not in roadmap:
        roadmap = roadmap.rstrip() + "\n\n" + (
            "## Step 8 Output\n\n"
            "`build\\pattern_language_sealed_v7_measurement_report.json` measured the active sealed v7 fixture once and consumed it. "
            "V7 minimum was not met; V8 taxonomy/rotation is required before tuning.\n"
        )

    marker = "## PLM V7: Constraint And Critical Signal Recovery"
    section = f"""
{marker}

Status: V7 Step 8 sealed v7 measurement completed; sealed v7 consumed; minimum not met; V8 taxonomy and fresh rotation required before tuning.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`
Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`
Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`
Router generalization report: `build/v7_router_generalization_report_v1.json`
Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`
Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`
Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`
Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`
Sealed v7 summary: `build/v7_step8_measurement_summary.md`

The V7 one-time sealed measurement scored intent_accuracy {metrics['intent_accuracy']:.6f}, critical_signal_recall {metrics['critical_signal_recall']:.6f}, operation_exact_match {metrics['operation_exact_match']:.6f}, constraint_exact_match {metrics['constraint_exact_match']:.6f}, risk_exact_match {metrics['risk_exact_match']:.6f}, with errors {len(metrics['errors'])}. The fixture is consumed and sealed labels remain measurement-only; use this result for V8 taxonomy and fresh rotation planning, not same-cycle tuning.
""".strip()
    if marker in main:
        head, rest = main.split(marker, 1)
        next_marker = "\n## "
        idx = rest.find(next_marker)
        if idx == -1:
            main = head.rstrip() + "\n\n" + section + "\n"
        else:
            tail = rest[idx + 1 :]
            main = head.rstrip() + "\n\n" + section + "\n\n" + tail
    else:
        main = main.rstrip() + "\n\n" + section + "\n"

    return targets, roadmap, main
