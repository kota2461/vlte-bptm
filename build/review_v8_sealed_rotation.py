"""Review readiness to rotate a fresh PLM sealed v8 fixture.

This Step 6 review is deliberately pre-rotation: it does not create, open, or
measure a sealed v8 fixture. It verifies that the V8 non-sealed replay gate is
clean, sealed v7 is consumed, and no active sealed fixture exists.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
STEP5_GATE_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.json"
V7_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v7_measurement_report.json"
OUTPUT_JSON = ROOT / "build" / "v8_sealed_rotation_review_v1.json"
OUTPUT_MD = ROOT / "build" / "v8_sealed_rotation_review_v1.md"
V8_TARGETS_PATH = ROOT / "build" / "v8_targets_and_roadmap_v1.json"
V8_ROADMAP_PATH = ROOT / "docs" / "PLM_V8_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
SEALED_V8_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v8.json"


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


def build_report() -> dict[str, Any]:
    gate = _load_json(STEP5_GATE_PATH)
    registry = _load_json(REGISTRY_PATH)
    v7_measurement = _load_json(V7_MEASUREMENT_PATH)
    active = _active_sealed(registry)
    v7_registry = registry["fixtures"].get("pattern_language_sealed_v7.json", {})

    blockers: list[str] = []
    if gate["schema_version"] != "v8-nonsealed-replay-gate-report.v1":
        blockers.append("unexpected_step5_gate_schema")
    if gate["status"] != "passed" or gate["passed"] is not True:
        blockers.append("v8_nonsealed_replay_gate_not_passed")
    if gate["summary"]["ready_for_step6_sealed_v8_rotation_review"] is not True:
        blockers.append("step5_gate_did_not_authorize_step6_review")
    if gate["summary"]["required_error_count"] != 0:
        blockers.append("required_nonsealed_lane_errors_present")
    if gate["contract"]["can_use_as_sealed_measurement"] is not False:
        blockers.append("nonsealed_gate_contract_allows_sealed_measurement")
    if gate["contract"]["can_use_for_same_cycle_promotion"] is not False:
        blockers.append("same_cycle_promotion_contract_violation")
    if v7_registry.get("status") != "consumed" or v7_registry.get("measured") is not True:
        blockers.append("previous_sealed_v7_not_consumed")
    if v7_measurement["registry_update"]["rotation_required_before_tuning"] is not True:
        blockers.append("v7_measurement_does_not_require_rotation")
    if v7_measurement["sealed_labels_used_for_tuning"] is not False:
        blockers.append("sealed_v7_labels_used_for_tuning")
    if active:
        blockers.append("active_sealed_fixture_already_exists")
    if SEALED_V8_PATH.exists():
        blockers.append("sealed_v8_fixture_already_exists")

    decision = "eligible_for_fresh_sealed_v8_rotation" if not blockers else "blocked"
    return {
        "schema_version": "v8-sealed-rotation-review.v1",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "passed": not blockers,
        "policy": {
            "sealed_v8_fixture_created_now": False,
            "sealed_v8_opened_for_measurement": False,
            "sealed_v8_labels_used_for_tuning": False,
            "sealed_v7_text_used_for_training": False,
            "sealed_v7_labels_used_for_tuning": False,
            "sealed_v7_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": gate["passed"],
            "same_cycle_promotion_allowed": False,
        },
        "sources": {
            "step5_gate": _rel(STEP5_GATE_PATH),
            "registry": _rel(REGISTRY_PATH),
            "previous_measurement": _rel(V7_MEASUREMENT_PATH),
        },
        "gate_summary": gate["summary"],
        "registry_state": {
            "active_sealed_fixtures": active,
            "previous_sealed": {
                "registry_name": "pattern_language_sealed_v7.json",
                "status": v7_registry.get("status"),
                "measured": v7_registry.get("measured"),
                "reviewed": v7_registry.get("reviewed"),
                "measurement_report": v7_registry.get("measurement_report"),
            },
            "planned_successor": {
                "registry_name": "pattern_language_sealed_v8.json",
                "predecessor": "pattern_language_sealed_v7.json",
                "status": "not_created",
                "measured": False,
                "reviewed": False,
            },
        },
        "previous_measurement_summary": {
            "fixture": v7_measurement["fixture"]["registry_name"],
            "sealed_fixture_opened": v7_measurement["sealed_fixture_opened"],
            "sealed_labels_used_for_tuning": v7_measurement["sealed_labels_used_for_tuning"],
            "intent_accuracy": v7_measurement["measurements"]["intent_accuracy"],
            "critical_signal_recall": v7_measurement["measurements"]["critical_signal_recall"],
            "operation_exact_match": v7_measurement["measurements"]["operation_exact_match"],
            "constraint_exact_match": v7_measurement["measurements"]["constraint_exact_match"],
            "risk_exact_match": v7_measurement["measurements"]["risk_exact_match"],
            "error_count": len(v7_measurement["measurements"]["errors"]),
            "rotation_required_before_tuning": v7_measurement["registry_update"][
                "rotation_required_before_tuning"
            ],
        },
        "planned_v8_fixture_constraints": {
            "case_count": 28,
            "cases_per_intent": 4,
            "split": "sealed",
            "must_be_unopened_until_measurement": True,
            "must_exclude_exact_text_from": {
                "prior_sealed_and_benchmark": _sealed_sources(registry),
                "v8_required_nonsealed_gate_lanes": [
                    lane["source"] for lane in gate["required_lanes"]
                ],
            },
            "measurement_rule": "measure_once_then_mark_consumed",
            "labels_rule": "sealed labels remain measurement-only and may not tune the same cycle",
        },
        "blockers": blockers,
        "next_action": (
            "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"
            if not blockers
            else "resolve_blockers_before_sealed_v8_rotation"
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    previous = report["previous_measurement_summary"]
    lines = [
        "# V8 Sealed Rotation Review v1",
        "",
        f"- status: `{report['decision']}`",
        f"- passed: `{report['passed']}`",
        f"- sealed_v8_fixture_created_now: `{report['policy']['sealed_v8_fixture_created_now']}`",
        f"- sealed_v8_opened_for_measurement: `{report['policy']['sealed_v8_opened_for_measurement']}`",
        f"- same_cycle_promotion_allowed: `{report['policy']['same_cycle_promotion_allowed']}`",
        f"- required_error_count: `{report['gate_summary']['required_error_count']}`",
        f"- active_sealed_fixtures: `{len(report['registry_state']['active_sealed_fixtures'])}`",
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
            "Fresh sealed v8 rotation is eligible. This review does not create "
            "or open the sealed v8 fixture; it only authorizes the next roadmap "
            "step to generate and rotate it."
            if report["passed"]
            else "Fresh sealed v8 rotation is blocked. Resolve blockers first."
        ),
        "",
        f"- next_action: `{report['next_action']}`",
    ]
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _update_roadmaps(report: dict[str, Any]) -> None:
    targets = _load_json(V8_TARGETS_PATH)
    targets["generated_at"] = report["reviewed_at"]
    targets["status"] = "step6_sealed_rotation_review_completed_step7_rotation_next"
    targets["next_action"] = "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"
    for item in targets["roadmap"]:
        if item["step"] == 6:
            item["status"] = "completed"
        elif item["step"] == 7:
            item["status"] = "next"
    targets["step6_sealed_rotation_review"] = {
        "output": "build\\v8_sealed_rotation_review_v1.json",
        "decision": report["decision"],
        "passed": report["passed"],
        "sealed_v8_fixture_created_now": False,
        "sealed_v8_opened_for_measurement": False,
        "same_cycle_promotion_allowed": False,
        "requires_fresh_sealed_v8_before_measurement": True,
        "summary": {
            "required_error_count": report["gate_summary"]["required_error_count"],
            "active_sealed_fixtures": len(report["registry_state"]["active_sealed_fixtures"]),
            "blocker_count": len(report["blockers"]),
        },
    }
    _write_json(V8_TARGETS_PATH, targets)

    roadmap = V8_ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 6 | sealed_v8_rotation_review | `build\\v8_sealed_rotation_review_v1.json` | next |",
        "| 6 | sealed_v8_rotation_review | `build\\v8_sealed_rotation_review_v1.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 7 | sealed_v8_rotation | `tests\\fixtures\\pattern_language_sealed_v8.json` | pending |",
        "| 7 | sealed_v8_rotation | `tests\\fixtures\\pattern_language_sealed_v8.json` | next |",
    )
    section = (
        "## Step 6 Output\n\n"
        f"`build\\v8_sealed_rotation_review_v1.json` reports `{report['decision']}`. "
        "It confirms that the V8 non-sealed replay gate passed, "
        "`pattern_language_sealed_v7.json` is consumed, no active sealed fixture exists, "
        "and `pattern_language_sealed_v8.json` has not been created. This review does "
        "not create, open, or measure sealed v8. Step 7 is now sealed V8 rotation.\n"
    )
    if "## Step 6 Output" in roadmap:
        head, _ = roadmap.split("## Step 6 Output", 1)
        roadmap = head.rstrip() + "\n\n" + section
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section
    V8_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")

    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    main = main.replace(
        "Status: V8 Step 5 non-sealed replay gate passed; Step 6 sealed rotation review next.",
        "Status: V8 Step 6 sealed rotation review completed; Step 7 sealed v8 rotation next.",
    )
    if "Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`" not in main:
        main = main.replace(
            "Non-sealed replay gate report: `build/v8_nonsealed_replay_gate_report_v1.json`\n",
            "Non-sealed replay gate report: `build/v8_nonsealed_replay_gate_report_v1.json`\nSealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`\n",
        )
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    report = build_report()
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
