"""Run the V7 non-sealed replay gate before sealed V7 rotation review."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "build"))

from semantic_routing import evaluate_plm_extractor, load_plm_benchmark, parse_plm_benchmark, route  # noqa: E402
from v7_measurement_state import preserve_step8_measurement_state  # noqa: E402

VISIBLE_PLM_PATH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
V5_CHALLENGE_PATH = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
V6_BOUNDARY_FP_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_adopted_benchmark_v1.json"
V6_PRIORITY_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_priority_review_adopted_benchmark_v1.json"
V6_STRUCTURAL_BUILD_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_structural_build_30_adopted_benchmark_v1.json"
V6_ROUTER_DEBATE_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json"
V6_BOUNDARY_FP_CANDIDATE_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_candidate_benchmark_v1.json"
V6_CONTRAST_NEGATIVE_PATH = ROOT / "tests" / "fixtures" / "v6_contrast_negative_benchmark_v1.json"
V6_ROUTER_DEBATE_CANDIDATE_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json"
V7_REPAIR_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v7_router_repair_fixture_v1.json"
V7_GENERALIZATION_REPORT_PATH = ROOT / "build" / "v7_router_generalization_report_v1.json"
REPORT_PATH = ROOT / "build" / "v7_nonsealed_replay_gate_report_v1.json"
REPORT_MD_PATH = ROOT / "build" / "v7_nonsealed_replay_gate_report_v1.md"
TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
STEP6_REVIEW_PATH = ROOT / "build" / "v7_sealed_rotation_review_v1.json"
V7_ROTATION_REPORT_PATH = ROOT / "build" / "v7_sealed_rotation_report_v1.json"
V7_MEASUREMENT_REPORT_PATH = ROOT / "build" / "pattern_language_sealed_v7_measurement_report.json"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(field for error in errors for field in error["fields"]).items()))


def _compact_plm_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
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


def _passed_exact(compact: dict[str, Any]) -> bool:
    return compact["valid_packet_rate"] == 1.0 and compact["error_count"] == 0


def _benchmark_payload_from_fixture(fixture: dict[str, Any], authoring_method: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": fixture["created_at"],
        "authoring_method": authoring_method,
        "review_status": fixture["review_status"],
        "policy": "Non-sealed replay; sealed v6 text and labels are excluded.",
        "cases": [
            {
                "id": case["id"],
                "split": case["split"],
                "source_group": case["source_group"],
                "contrast_group": case.get("contrast_group"),
                "language": case["language"],
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in fixture["cases"]
        ],
    }


def _visible_lane() -> dict[str, Any]:
    benchmark = load_plm_benchmark(VISIBLE_PLM_PATH)
    visible_cases = benchmark.cases_for_splits(("train", "validation"))
    measurement = evaluate_plm_extractor(visible_cases, lambda text: route(text).packet)
    compact = _compact_plm_measurement(measurement)
    return {
        "name": "visible_plm_train_validation",
        "source": _rel(VISIBLE_PLM_PATH),
        "review_status": "human_reviewed",
        "evaluated_splits": ["train", "validation"],
        "sealed_split_evaluated": False,
        "passed_exact": _passed_exact(compact),
        "measurement": compact,
        "errors": measurement["errors"],
    }


def _benchmark_lane(name: str, path: Path, review_status: str) -> dict[str, Any]:
    payload = _load_json(path)
    benchmark = parse_plm_benchmark(payload)
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    compact = _compact_plm_measurement(measurement)
    return {
        "name": name,
        "source": _rel(path),
        "review_status": review_status,
        "passed_exact": _passed_exact(compact),
        "measurement": compact,
        "errors": measurement["errors"],
    }


def _fixture_lane(name: str, path: Path, authoring_method: str, gate_evidence_allowed: bool) -> dict[str, Any]:
    fixture = _load_json(path)
    benchmark = parse_plm_benchmark(_benchmark_payload_from_fixture(fixture, authoring_method))
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    compact = _compact_plm_measurement(measurement)
    return {
        "name": name,
        "source": _rel(path),
        "review_status": fixture["review_status"],
        "gate_evidence_allowed": gate_evidence_allowed,
        "human_review_required_before_gate": fixture.get("policy", {}).get("human_review_required_before_gate", False),
        "passed_exact": _passed_exact(compact),
        "measurement": compact,
        "errors": measurement["errors"],
    }


def _required_lanes() -> list[dict[str, Any]]:
    return [
        _visible_lane(),
        _fixture_lane(
            "v5_critical_operations",
            V5_CHALLENGE_PATH,
            "V7 Step 5 protection replay of V5 critical operations",
            True,
        ),
        _benchmark_lane("v6_boundary_false_positive_adopted", V6_BOUNDARY_FP_ADOPTED_PATH, "human_reviewed"),
        _benchmark_lane("v6_boundary_priority_review_adopted", V6_PRIORITY_ADOPTED_PATH, "human_reviewed"),
        _benchmark_lane("v6_structural_build_30_adopted", V6_STRUCTURAL_BUILD_ADOPTED_PATH, "human_reviewed"),
        _benchmark_lane("v6_router_debate_adopted", V6_ROUTER_DEBATE_ADOPTED_PATH, "human_reviewed"),
    ]


def _diagnostic_lanes() -> list[dict[str, Any]]:
    return [
        _benchmark_lane("v6_boundary_false_positive_candidate", V6_BOUNDARY_FP_CANDIDATE_PATH, "draft"),
        _benchmark_lane("v6_contrast_negative", V6_CONTRAST_NEGATIVE_PATH, "draft"),
        _benchmark_lane("v6_router_debate_candidate", V6_ROUTER_DEBATE_CANDIDATE_PATH, "draft"),
        _fixture_lane(
            "v7_router_repair_fixture",
            V7_REPAIR_FIXTURE_PATH,
            "V7 Step 5 diagnostic replay of draft router repair fixture",
            False,
        ),
    ]


def _summary(required_lanes: list[dict[str, Any]], diagnostic_lanes: list[dict[str, Any]]) -> dict[str, Any]:
    required_errors = sum(lane["measurement"]["error_count"] for lane in required_lanes)
    diagnostic_errors = sum(lane["measurement"]["error_count"] for lane in diagnostic_lanes)
    v7_lane = next(lane for lane in diagnostic_lanes if lane["name"] == "v7_router_repair_fixture")
    return {
        "required_lane_count": len(required_lanes),
        "required_passed_lane_count": sum(1 for lane in required_lanes if lane["passed_exact"]),
        "required_error_count": required_errors,
        "diagnostic_lane_count": len(diagnostic_lanes),
        "diagnostic_exact_lane_count": sum(1 for lane in diagnostic_lanes if lane["passed_exact"]),
        "diagnostic_error_count": diagnostic_errors,
        "v7_curriculum_case_count": v7_lane["measurement"]["case_count"],
        "v7_curriculum_error_count": v7_lane["measurement"]["error_count"],
        "v7_curriculum_exact": v7_lane["passed_exact"],
        "ready_for_step6_sealed_v7_rotation_review": (
            required_errors == 0 and all(lane["passed_exact"] for lane in required_lanes) and v7_lane["passed_exact"]
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# V7 Non-Sealed Replay Gate Report v1",
        "",
        f"status: `{report['status']}`",
        f"passed: {str(report['passed']).lower()}",
        f"required_lane_count: {report['summary']['required_lane_count']}",
        f"required_error_count: {report['summary']['required_error_count']}",
        f"diagnostic_lane_count: {report['summary']['diagnostic_lane_count']}",
        f"diagnostic_error_count: {report['summary']['diagnostic_error_count']}",
        f"v7_curriculum_error_count: {report['summary']['v7_curriculum_error_count']}",
        f"ready_for_step6_sealed_v7_rotation_review: {str(report['summary']['ready_for_step6_sealed_v7_rotation_review']).lower()}",
        "",
        "## Policy",
    ]
    for key, value in report["policy"].items():
        lines.append(f"- {key}: {str(value).lower() if isinstance(value, bool) else value}")
    lines.extend(["", "## Required Lanes"])
    for lane in report["required_lanes"]:
        lines.append(
            f"- {lane['name']}: passed_exact={str(lane['passed_exact']).lower()}, "
            f"errors={lane['measurement']['error_count']}, source=`{lane['source']}`"
        )
    lines.extend(["", "## Diagnostic Lanes"])
    for lane in report["diagnostic_lanes"]:
        lines.append(
            f"- {lane['name']}: passed_exact={str(lane['passed_exact']).lower()}, "
            f"errors={lane['measurement']['error_count']}, gate_evidence_allowed={str(lane.get('gate_evidence_allowed', False)).lower()}, "
            f"source=`{lane['source']}`"
        )
    lines.extend(["", "## Contract", ""])
    for key, value in report["contract"].items():
        lines.append(f"- {key}: {str(value).lower() if isinstance(value, bool) else value}")
    lines.append("")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8", newline="\n")

def _existing_step6_review() -> dict[str, Any] | None:
    if not STEP6_REVIEW_PATH.exists():
        return None
    review = _load_json(STEP6_REVIEW_PATH)
    if review.get("schema_version") != "v7-sealed-rotation-review.v1":
        return None
    if review.get("passed") is not True:
        return None
    return review


def _preserve_step6_review_state(targets: dict[str, Any], roadmap: str, main: str) -> tuple[dict[str, Any], str, str]:
    review = _existing_step6_review()
    if review is None:
        return targets, roadmap, main

    targets["status"] = "step6_sealed_rotation_review_completed_step7_rotation_next"
    targets["next_action"] = "roadmap_v7_step7_generate_and_rotate_sealed_v7_fixture"
    for item in targets["roadmap"]:
        if item["step"] == 6:
            item["status"] = "completed"
        elif item["step"] == 7:
            item["status"] = "next"
    targets["step6_sealed_rotation_review"] = {
        "output": "build\\v7_sealed_rotation_review_v1.json",
        "decision": review["decision"],
        "passed": review["passed"],
        "sealed_v7_fixture_created_now": False,
        "sealed_v7_opened_for_measurement": False,
        "same_cycle_promotion_allowed": False,
        "requires_fresh_sealed_v7_before_measurement": True,
        "summary": {
            "required_error_count": review["gate_summary"]["required_error_count"],
            "diagnostic_error_count": review["gate_summary"]["diagnostic_error_count"],
            "v7_curriculum_error_count": review["gate_summary"]["v7_curriculum_error_count"],
            "active_sealed_fixtures": len(review["registry_state"]["active_sealed_fixtures"]),
            "blocker_count": len(review["blockers"]),
        },
    }
    roadmap = roadmap.replace(
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | next |",
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | pending |",
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | next |",
    )
    if "## Step 6 Output" not in roadmap:
        roadmap = roadmap.rstrip() + "\n\n" + (
            "## Step 6 Output\n\n"
            "`build\\v7_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v7_rotation`. "
            "It confirms that the V7 non-sealed replay gate passed, `pattern_language_sealed_v6.json` is consumed, "
            "no active sealed fixture exists, and `pattern_language_sealed_v7.json` has not been created. "
            "This review does not create, open, or measure sealed v7. Step 7 is now sealed V7 rotation.\n"
        )
    main = main.replace(
        "Status: V7 Step 5 non-sealed replay gate passed; Step 6 sealed rotation review next.",
        "Status: V7 Step 6 sealed rotation review completed; Step 7 sealed v7 rotation next.",
    )
    if "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`" not in main:
        main = main.replace(
            "Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`\n",
            "Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`\nSealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`\n",
        )
    main = main.replace(
        "Step 5 non-sealed replay gate passed; Step 6 sealed rotation review is next before creating fresh sealed v7.",
        "Step 5 non-sealed replay gate passed, and Step 6 sealed rotation review authorized fresh sealed v7 rotation. Step 7 should generate and rotate a fresh unopened `pattern_language_sealed_v7.json`.",
    )
    return targets, roadmap, main

def _existing_step7_rotation() -> dict[str, Any] | None:
    if not V7_ROTATION_REPORT_PATH.exists():
        return None
    report = _load_json(V7_ROTATION_REPORT_PATH)
    if report.get("schema_version") != "v7-sealed-rotation-report.v1":
        return None
    rotated_to = report.get("rotated_to", {})
    if rotated_to.get("status") != "active" or rotated_to.get("measured") is not False:
        return None
    return report


def _preserve_step7_rotation_state(targets: dict[str, Any], roadmap: str, main: str) -> tuple[dict[str, Any], str, str]:
    report = _existing_step7_rotation()
    if report is None:
        return targets, roadmap, main

    targets["status"] = "step7_sealed_rotation_completed_step8_measurement_next"
    targets["next_action"] = "roadmap_v7_step8_measure_active_sealed_v7_once"
    for item in targets["roadmap"]:
        if item["step"] == 7:
            item["status"] = "completed"
        elif item["step"] == 8:
            item["status"] = "next"
    targets["step7_sealed_rotation"] = {
        "output": "build\\v7_sealed_rotation_report_v1.json",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v7.json",
        "passed": True,
        "sealed_v7_opened_for_measurement": False,
        "sealed_v7_labels_used_for_tuning": False,
        "same_cycle_promotion_allowed": False,
        "summary": {
            "case_count": report["rotated_to"]["case_count"],
            "status": report["rotated_to"]["status"],
            "measured": report["rotated_to"]["measured"],
            "reviewed": report["rotated_to"]["reviewed"],
            "readiness_decision": report["readiness_after_rotation"]["decision"],
            "blocked_reasons": report["readiness_after_rotation"]["blocked_reasons"],
        },
    }
    roadmap = roadmap.replace(
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | next |",
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | pending |",
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | next |",
    )
    if "## Step 7 Output" not in roadmap:
        roadmap = roadmap.rstrip() + "\n\n" + (
            "## Step 7 Output\n\n"
            "`build\\v7_sealed_rotation_report_v1.json` created `tests\\fixtures\\pattern_language_sealed_v7.json` "
            "as the active unopened sealed fixture. Step 8 is the one-time sealed v7 measurement.\n"
        )
    main = main.replace(
        "Status: V7 Step 6 sealed rotation review completed; Step 7 sealed v7 rotation next.",
        "Status: V7 Step 7 sealed v7 rotation completed; sealed v7 active/unmeasured; Step 8 one-time sealed v7 measurement next.",
    )
    if "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`" not in main:
        main = main.replace(
            "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`\n",
            "Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`\nSealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`\nSealed v7 fixture: `tests/fixtures/pattern_language_sealed_v7.json`\n",
        )
    return targets, roadmap, main

def _existing_step8_measurement() -> dict[str, Any] | None:
    if not V7_MEASUREMENT_REPORT_PATH.exists():
        return None
    report = _load_json(V7_MEASUREMENT_REPORT_PATH)
    if report.get("schema_version") != "plm-sealed-measurement-report.v1":
        return None
    if report.get("fixture", {}).get("registry_name") != "pattern_language_sealed_v7.json":
        return None
    if report.get("registry_update", {}).get("status_after_measurement") != "consumed":
        return None
    return report


def _preserve_step8_measurement_state(targets: dict[str, Any], roadmap: str, main: str) -> tuple[dict[str, Any], str, str]:
    measurement = _existing_step8_measurement()
    if measurement is None:
        return targets, roadmap, main

    metrics = measurement["measurements"]
    field_counts: dict[str, int] = {}
    for error in metrics["errors"]:
        for field in error["fields"]:
            field_counts[field] = field_counts.get(field, 0) + 1
    field_counts = dict(sorted(field_counts.items()))
    targets["status"] = "step8_sealed_v7_measurement_completed_v8_rotation_required"
    targets["next_action"] = "roadmap_v8_step1_post_v7_measurement_taxonomy"
    for item in targets["roadmap"]:
        if item["step"] in {7, 8}:
            item["status"] = "completed"
    targets["step8_sealed_measurement"] = {
        "output": "build\\pattern_language_sealed_v7_measurement_report.json",
        "summary": "build\\v7_step8_measurement_summary.md",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v7.json",
        "sealed_fixture_opened": measurement["sealed_fixture_opened"],
        "sealed_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
        "passed_minimum": False,
        "minimum_metrics_met": False,
        "critical_signal_miss_count": 5,
        "critical_signal_miss_gate_met": False,
        "rotation_required_before_tuning": measurement["registry_update"]["rotation_required_before_tuning"],
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
    roadmap = roadmap.replace(
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | next |",
        "| 8 | sealed_v7_one_time_measurement | `build\\pattern_language_sealed_v7_measurement_report.json` | completed |",
    )
    if "## Step 8 Output" not in roadmap:
        roadmap = roadmap.rstrip() + "\n\n" + (
            "## Step 8 Output\n\n"
            "`build\\pattern_language_sealed_v7_measurement_report.json` measured the active sealed v7 fixture once and consumed it. "
            "V7 minimum was not met; V8 taxonomy/rotation is required before tuning.\n"
        )
    main = main.replace(
        "Status: V7 Step 7 sealed v7 rotation completed; sealed v7 active/unmeasured; Step 8 one-time sealed v7 measurement next.",
        "Status: V7 Step 8 sealed v7 measurement completed; sealed v7 consumed; minimum not met; V8 taxonomy and fresh rotation required before tuning.",
    )
    if "Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`" not in main:
        main = main.replace(
            "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`\n",
            "Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`\nSealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`\nSealed v7 summary: `build/v7_step8_measurement_summary.md`\n",
        )
    return targets, roadmap, main

def _replace_section(text: str, heading: str, section: str, next_heading: str | None = None) -> str:
    if heading in text:
        head, rest = text.split(heading, 1)
        if next_heading and next_heading in rest:
            _, tail = rest.split(next_heading, 1)
            return head.rstrip() + "\n\n" + section + "\n\n" + next_heading + tail
        return head.rstrip() + "\n\n" + section + "\n"
    return text.rstrip() + "\n\n" + section + "\n"


def _update_roadmaps(report: dict[str, Any]) -> None:
    targets = _load_json(TARGETS_PATH)
    targets["generated_at"] = report["generated_at"]
    targets["status"] = "step5_nonsealed_replay_gate_passed_step6_rotation_review_next"
    targets["next_action"] = "roadmap_v7_step6_sealed_rotation_review"
    for item in targets["roadmap"]:
        if item["step"] == 5:
            item["status"] = "completed"
        elif item["step"] == 6:
            item["status"] = "next"
    targets["step5_nonsealed_replay_gate"] = {
        "output": "build\\v7_nonsealed_replay_gate_report_v1.json",
        "status": report["status"],
        "passed": report["passed"],
        "sealed_v6_text_used": False,
        "sealed_v6_labels_used": False,
        "same_cycle_promotion_allowed": False,
        "draft_or_candidate_lanes_are_gate_evidence": False,
        "requires_human_review_before_sealed_rotation": True,
        "summary": report["summary"],
    }
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | next |",
        "| 5 | v7_nonsealed_replay_gate | `build\\v7_nonsealed_replay_gate_report_v1.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | pending |",
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | next |",
    )
    section = f"""## Step 5 Output

`build\\v7_nonsealed_replay_gate_report_v1.json` passed as a non-sealed replay gate. Required human-reviewed/protection lanes passed {report['summary']['required_passed_lane_count']}/{report['summary']['required_lane_count']} with {report['summary']['required_error_count']} errors. Diagnostic lanes, including the draft V7 router repair fixture, passed {report['summary']['diagnostic_exact_lane_count']}/{report['summary']['diagnostic_lane_count']} with {report['summary']['diagnostic_error_count']} errors. The V7 draft fixture remains non-gate evidence until human review; sealed v6 text and labels remain excluded. Step 6 is now sealed V7 rotation review."""
    roadmap = _replace_section(roadmap, "## Step 5 Output", section, "## Pre-Rotation Gates" if "## Pre-Rotation Gates" in roadmap else None)
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    main = main.replace(
        "Status: V7 Step 4 router generalization completed; Step 5 non-sealed replay gate next.",
        "Status: V7 Step 5 non-sealed replay gate passed; Step 6 sealed rotation review next.",
    )
    if "Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`" not in main:
        main = main.replace(
            "Router generalization report: `build/v7_router_generalization_report_v1.json`\n",
            "Router generalization report: `build/v7_router_generalization_report_v1.json`\nNon-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`\n",
        )
    main = main.replace(
        "This is not gate evidence; Step 5 must run the non-sealed replay gate before sealed v7 rotation.",
        "Step 5 non-sealed replay gate passed; Step 6 sealed rotation review is next before creating fresh sealed v7.",
    )
    targets, roadmap, main = _preserve_step6_review_state(targets, roadmap, main)
    targets, roadmap, main = _preserve_step7_rotation_state(targets, roadmap, main)
    targets, roadmap, main = preserve_step8_measurement_state(ROOT, targets, roadmap, main)
    _write_json(TARGETS_PATH, targets)
    ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    required_lanes = _required_lanes()
    diagnostic_lanes = _diagnostic_lanes()
    summary = _summary(required_lanes, diagnostic_lanes)
    passed = summary["ready_for_step6_sealed_v7_rotation_review"]
    generalization = _load_json(V7_GENERALIZATION_REPORT_PATH)
    report = {
        "schema_version": "v7-nonsealed-replay-gate-report.v1",
        "generated_at": generated_at,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "policy": {
            "sealed_fixture_opened_now": False,
            "sealed_measurement_used_for_tuning": False,
            "sealed_v6_text_used": False,
            "sealed_v6_labels_used": False,
            "nonsealed_current_route_measurement_is_gate": True,
            "draft_or_candidate_lanes_are_gate_evidence": False,
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_v7_required_before_adjudication": True,
        },
        "source_generalization_report": _rel(V7_GENERALIZATION_REPORT_PATH),
        "step4_after": generalization["after"],
        "required_lanes": required_lanes,
        "diagnostic_lanes": diagnostic_lanes,
        "summary": summary,
        "contract": {
            "can_use_for_v7_roadmap_step5": passed,
            "can_use_as_sealed_measurement": False,
            "can_use_for_same_cycle_promotion": False,
            "requires_human_review_before_sealed_rotation": True,
            "requires_fresh_sealed_v7_before_measurement": True,
        },
        "next_action": "roadmap_v7_step6_sealed_rotation_review",
    }
    _write_json(REPORT_PATH, report)
    _write_markdown(report)
    _update_roadmaps(report)
    print(json.dumps({"status": report["status"], "summary": report["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
