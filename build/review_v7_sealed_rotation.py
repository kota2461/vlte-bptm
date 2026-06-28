"""Review readiness to rotate a fresh PLM sealed v7 fixture.

This Step 6 review is deliberately pre-rotation: it does not create, open, or
measure a sealed v7 fixture. It verifies that the V7 non-sealed replay gate is
clean, sealed v6 is consumed, and no active sealed fixture exists.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "build"))

from v7_measurement_state import preserve_step8_measurement_state  # noqa: E402

REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
STEP5_GATE_PATH = ROOT / "build" / "v7_nonsealed_replay_gate_report_v1.json"
V6_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v6_measurement_report.json"
OUTPUT_JSON = ROOT / "build" / "v7_sealed_rotation_review_v1.json"
OUTPUT_MD = ROOT / "build" / "v7_sealed_rotation_review_v1.md"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
SEALED_V7_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v7.json"


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


def _active_sealed(registry: dict[str, Any]) -> list[str]:
    return [
        name
        for name, entry in registry["fixtures"].items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]


def _sealed_sources(registry: dict[str, Any]) -> list[str]:
    return [
        name
        for name, entry in registry["fixtures"].items()
        if entry.get("role") == "sealed measurement only"
        or name == "pattern_language_benchmark_v1.json"
    ]


def _build_report() -> dict[str, Any]:
    gate = _load_json(STEP5_GATE_PATH)
    registry = _load_json(REGISTRY_PATH)
    v6_measurement = _load_json(V6_MEASUREMENT_PATH)
    active = _active_sealed(registry)
    v6_registry = registry["fixtures"].get("pattern_language_sealed_v6.json", {})

    blockers: list[str] = []
    if gate["schema_version"] != "v7-nonsealed-replay-gate-report.v1":
        blockers.append("unexpected_step5_gate_schema")
    if gate["status"] != "passed" or gate["passed"] is not True:
        blockers.append("v7_nonsealed_replay_gate_not_passed")
    if gate["summary"]["ready_for_step6_sealed_v7_rotation_review"] is not True:
        blockers.append("step5_gate_did_not_authorize_step6_review")
    if gate["summary"]["required_error_count"] != 0:
        blockers.append("required_nonsealed_lane_errors_present")
    if gate["summary"]["v7_curriculum_error_count"] != 0:
        blockers.append("v7_curriculum_replay_errors_present")
    if gate["contract"]["can_use_as_sealed_measurement"] is not False:
        blockers.append("nonsealed_gate_contract_allows_sealed_measurement")
    if gate["contract"]["can_use_for_same_cycle_promotion"] is not False:
        blockers.append("same_cycle_promotion_contract_violation")
    if v6_registry.get("status") != "consumed" or v6_registry.get("measured") is not True:
        blockers.append("previous_sealed_v6_not_consumed")
    if v6_measurement["registry_update"]["rotation_required_before_tuning"] is not True:
        blockers.append("v6_measurement_does_not_require_rotation")
    if v6_measurement["sealed_labels_used_for_tuning"] is not False:
        blockers.append("sealed_v6_labels_used_for_tuning")
    if active:
        blockers.append("active_sealed_fixture_already_exists")
    if SEALED_V7_PATH.exists():
        blockers.append("sealed_v7_fixture_already_exists")

    required_sources = [lane["source"] for lane in gate["required_lanes"]]
    diagnostic_sources = [lane["source"] for lane in gate["diagnostic_lanes"]]
    decision = "eligible_for_fresh_sealed_v7_rotation" if not blockers else "blocked"

    return {
        "schema_version": "v7-sealed-rotation-review.v1",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "passed": not blockers,
        "policy": {
            "sealed_v7_fixture_created_now": False,
            "sealed_v7_opened_for_measurement": False,
            "sealed_v7_labels_used_for_tuning": False,
            "sealed_v6_text_used_for_training": False,
            "sealed_v6_labels_used_for_tuning": False,
            "sealed_v6_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": gate["passed"],
            "draft_or_candidate_lanes_used_as_gate_evidence": False,
            "same_cycle_promotion_allowed": False,
        },
        "sources": {
            "step5_gate": _rel(STEP5_GATE_PATH),
            "registry": _rel(REGISTRY_PATH),
            "previous_measurement": _rel(V6_MEASUREMENT_PATH),
            "source_generalization_report": gate["source_generalization_report"],
        },
        "gate_summary": gate["summary"],
        "registry_state": {
            "active_sealed_fixtures": active,
            "previous_sealed": {
                "registry_name": "pattern_language_sealed_v6.json",
                "status": v6_registry.get("status"),
                "measured": v6_registry.get("measured"),
                "reviewed": v6_registry.get("reviewed"),
                "measurement_report": v6_registry.get("measurement_report"),
            },
            "planned_successor": {
                "registry_name": "pattern_language_sealed_v7.json",
                "predecessor": "pattern_language_sealed_v6.json",
                "status": "not_created",
                "measured": False,
                "reviewed": False,
            },
        },
        "previous_measurement_summary": {
            "fixture": v6_measurement["fixture"]["registry_name"],
            "sealed_fixture_opened": v6_measurement["sealed_fixture_opened"],
            "sealed_labels_used_for_tuning": v6_measurement["sealed_labels_used_for_tuning"],
            "intent_accuracy": v6_measurement["measurements"]["intent_accuracy"],
            "critical_signal_recall": v6_measurement["measurements"]["critical_signal_recall"],
            "operation_exact_match": v6_measurement["measurements"]["operation_exact_match"],
            "constraint_exact_match": v6_measurement["measurements"]["constraint_exact_match"],
            "risk_exact_match": v6_measurement["measurements"]["risk_exact_match"],
            "error_count": len(v6_measurement["measurements"]["errors"]),
            "rotation_required_before_tuning": v6_measurement["registry_update"][
                "rotation_required_before_tuning"
            ],
        },
        "planned_v7_fixture_constraints": {
            "case_count": 28,
            "cases_per_intent": 4,
            "split": "sealed",
            "must_be_unopened_until_measurement": True,
            "must_exclude_exact_text_from": {
                "prior_sealed_and_benchmark": _sealed_sources(registry),
                "v7_required_nonsealed_gate_lanes": required_sources,
                "v7_diagnostic_nonsealed_lanes": diagnostic_sources,
            },
            "measurement_rule": "measure_once_then_mark_consumed",
            "labels_rule": "sealed labels remain measurement-only and may not tune the same cycle",
        },
        "blockers": blockers,
        "next_action": (
            "roadmap_v7_step7_generate_and_rotate_sealed_v7_fixture"
            if not blockers
            else "resolve_blockers_before_sealed_v7_rotation"
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    planned = report["registry_state"]["planned_successor"]
    previous = report["previous_measurement_summary"]
    lines = [
        "# V7 Sealed Rotation Review v1",
        "",
        f"- status: `{report['decision']}`",
        f"- passed: `{report['passed']}`",
        f"- sealed_v7_fixture_created_now: `{report['policy']['sealed_v7_fixture_created_now']}`",
        f"- sealed_v7_opened_for_measurement: `{report['policy']['sealed_v7_opened_for_measurement']}`",
        f"- same_cycle_promotion_allowed: `{report['policy']['same_cycle_promotion_allowed']}`",
        f"- required_error_count: `{report['gate_summary']['required_error_count']}`",
        f"- v7_curriculum_error_count: `{report['gate_summary']['v7_curriculum_error_count']}`",
        f"- active_sealed_fixtures: `{len(report['registry_state']['active_sealed_fixtures'])}`",
        f"- planned_successor: `{planned['registry_name']}`",
        "",
        "## Previous Sealed Measurement",
        "",
        f"- fixture: `{previous['fixture']}`",
        f"- intent_accuracy: `{previous['intent_accuracy']:.6f}`",
        f"- critical_signal_recall: `{previous['critical_signal_recall']:.6f}`",
        f"- operation_exact_match: `{previous['operation_exact_match']:.6f}`",
        f"- constraint_exact_match: `{previous['constraint_exact_match']:.6f}`",
        f"- risk_exact_match: `{previous['risk_exact_match']:.6f}`",
        f"- error_count: `{previous['error_count']}`",
        "",
        "## Decision",
        "",
        (
            "Fresh sealed v7 rotation is eligible. This review does not create "
            "or open the sealed v7 fixture; it only authorizes the next roadmap "
            "step to generate and rotate it."
            if report["passed"]
            else "Fresh sealed v7 rotation is blocked. Resolve blockers first."
        ),
        "",
        f"- next_action: `{report['next_action']}`",
    ]
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _replace_section(text: str, heading: str, section: str) -> str:
    if heading not in text:
        return text.rstrip() + "\n\n" + section + "\n"
    head, rest = text.split(heading, 1)
    marker = "\n## "
    idx = rest.find(marker)
    if idx == -1:
        return head.rstrip() + "\n\n" + section + "\n"
    tail = rest[idx + 1 :]
    return head.rstrip() + "\n\n" + section + "\n\n" + tail


def _update_roadmaps(report: dict[str, Any]) -> None:
    targets_path = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
    targets = _load_json(targets_path)
    targets["generated_at"] = report["reviewed_at"]
    targets["status"] = "step6_sealed_rotation_review_completed_step7_rotation_next"
    targets["next_action"] = "roadmap_v7_step7_generate_and_rotate_sealed_v7_fixture"
    for item in targets["roadmap"]:
        if item["step"] == 6:
            item["status"] = "completed"
        elif item["step"] == 7:
            item["status"] = "next"
    targets["step6_sealed_rotation_review"] = {
        "output": "build\\v7_sealed_rotation_review_v1.json",
        "decision": report["decision"],
        "passed": report["passed"],
        "sealed_v7_fixture_created_now": False,
        "sealed_v7_opened_for_measurement": False,
        "same_cycle_promotion_allowed": False,
        "requires_fresh_sealed_v7_before_measurement": True,
        "summary": {
            "required_error_count": report["gate_summary"]["required_error_count"],
            "diagnostic_error_count": report["gate_summary"]["diagnostic_error_count"],
            "v7_curriculum_error_count": report["gate_summary"]["v7_curriculum_error_count"],
            "active_sealed_fixtures": len(report["registry_state"]["active_sealed_fixtures"]),
            "blocker_count": len(report["blockers"]),
        },
    }
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | next |",
        "| 6 | sealed_v7_rotation_review | `build\\v7_sealed_rotation_review_v1.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | pending |",
        "| 7 | sealed_v7_rotation | `tests\\fixtures\\pattern_language_sealed_v7.json` | next |",
    )
    section = f"""## Step 6 Output

`build\\v7_sealed_rotation_review_v1.json` reports `{report['decision']}`. It confirms that the V7 non-sealed replay gate passed, `pattern_language_sealed_v6.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v7.json` has not been created. This review does not create, open, or measure sealed v7. Step 7 is now sealed V7 rotation."""
    roadmap = _replace_section(roadmap, "## Step 6 Output", section)
    V7_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
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
    targets, roadmap, main = preserve_step8_measurement_state(ROOT, targets, roadmap, main)
    _write_json(targets_path, targets)
    V7_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    report = _build_report()
    _write_json(OUTPUT_JSON, report)
    _write_markdown(report)
    _update_roadmaps(report)
    print(
        json.dumps(
            {
                "status": report["decision"],
                "passed": report["passed"],
                "output": _rel(OUTPUT_JSON),
                "next_action": report["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
