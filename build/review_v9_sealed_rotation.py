"""Review readiness to rotate a fresh PLM sealed v9 fixture.

This Step 6 review is deliberately pre-rotation: it does not create, open, or
measure a sealed v9 fixture. It verifies that the V9 non-sealed replay gate is
clean, sealed v8 is consumed, and no active sealed fixture exists.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
STEP5_GATE_PATH = ROOT / "build" / "v9_nonsealed_replay_gate_report_v1.json"
V8_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v8_measurement_report.json"
OUTPUT_JSON = ROOT / "build" / "v9_sealed_rotation_review_v1.json"
OUTPUT_MD = ROOT / "build" / "v9_sealed_rotation_review_v1.md"
SEALED_V9_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v9.json"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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
    v8_measurement = _load_json(V8_MEASUREMENT_PATH)
    active = _active_sealed(registry)
    v8_registry = registry["fixtures"].get("pattern_language_sealed_v8.json", {})

    blockers: list[str] = []
    if gate["schema_version"] != "v9-nonsealed-replay-gate-report.v1":
        blockers.append("unexpected_step5_gate_schema")
    if gate["status"] != "passed" or gate["passed"] is not True:
        blockers.append("v9_nonsealed_replay_gate_not_passed")
    if gate["summary"]["ready_for_step6_sealed_v9_rotation_review"] is not True:
        blockers.append("step5_gate_did_not_authorize_step6_review")
    if gate["summary"]["required_error_count"] != 0:
        blockers.append("required_nonsealed_lane_errors_present")
    if gate["contract"]["can_use_as_sealed_measurement"] is not False:
        blockers.append("nonsealed_gate_contract_allows_sealed_measurement")
    if gate["contract"]["can_use_for_same_cycle_promotion"] is not False:
        blockers.append("same_cycle_promotion_contract_violation")
    if v8_registry.get("status") != "consumed" or v8_registry.get("measured") is not True:
        blockers.append("previous_sealed_v8_not_consumed")
    if v8_measurement["registry_update"]["rotation_required_before_tuning"] is not True:
        blockers.append("v8_measurement_does_not_require_rotation")
    if v8_measurement["sealed_labels_used_for_tuning"] is not False:
        blockers.append("sealed_v8_labels_used_for_tuning")
    if active:
        blockers.append("active_sealed_fixture_already_exists")
    if SEALED_V9_PATH.exists():
        blockers.append("sealed_v9_fixture_already_exists")

    decision = "eligible_for_fresh_sealed_v9_rotation" if not blockers else "blocked"
    return {
        "schema_version": "v9-sealed-rotation-review.v1",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "passed": not blockers,
        "policy": {
            "sealed_v9_fixture_created_now": False,
            "sealed_v9_opened_for_measurement": False,
            "sealed_v9_labels_used_for_tuning": False,
            "sealed_v8_text_used_for_training": False,
            "sealed_v8_labels_used_for_tuning": False,
            "sealed_v8_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": gate["passed"],
            "same_cycle_promotion_allowed": False,
        },
        "sources": {
            "step5_gate": _rel(STEP5_GATE_PATH),
            "registry": _rel(REGISTRY_PATH),
            "previous_measurement": _rel(V8_MEASUREMENT_PATH),
        },
        "gate_summary": gate["summary"],
        "registry_state": {
            "active_sealed_fixtures": active,
            "previous_sealed": {
                "registry_name": "pattern_language_sealed_v8.json",
                "status": v8_registry.get("status"),
                "measured": v8_registry.get("measured"),
                "reviewed": v8_registry.get("reviewed"),
                "measurement_report": v8_registry.get("measurement_report"),
            },
            "planned_successor": {
                "registry_name": "pattern_language_sealed_v9.json",
                "predecessor": "pattern_language_sealed_v8.json",
                "status": "not_created",
                "measured": False,
                "reviewed": False,
            },
        },
        "previous_measurement_summary": {
            "fixture": v8_measurement["fixture"]["registry_name"],
            "sealed_fixture_opened": v8_measurement["sealed_fixture_opened"],
            "sealed_labels_used_for_tuning": v8_measurement["sealed_labels_used_for_tuning"],
            "intent_accuracy": v8_measurement["measurements"]["intent_accuracy"],
            "critical_signal_recall": v8_measurement["measurements"]["critical_signal_recall"],
            "operation_exact_match": v8_measurement["measurements"]["operation_exact_match"],
            "constraint_exact_match": v8_measurement["measurements"]["constraint_exact_match"],
            "risk_exact_match": v8_measurement["measurements"]["risk_exact_match"],
            "error_count": len(v8_measurement["measurements"]["errors"]),
            "rotation_required_before_tuning": v8_measurement["registry_update"]["rotation_required_before_tuning"],
        },
        "planned_v9_fixture_constraints": {
            "case_count": 28,
            "cases_per_intent": 4,
            "split": "sealed",
            "must_be_unopened_until_measurement": True,
            "must_exclude_exact_text_from": {
                "prior_sealed_and_benchmark": _sealed_sources(registry),
                "v9_required_nonsealed_gate_lanes": [lane["source"] for lane in gate["required_lanes"]],
            },
            "measurement_rule": "measure_once_then_mark_consumed",
            "labels_rule": "sealed labels remain measurement-only and may not tune the same cycle",
        },
        "blockers": blockers,
        "next_action": (
            "roadmap_v9_step7_generate_and_rotate_sealed_v9_fixture"
            if not blockers
            else "resolve_blockers_before_sealed_v9_rotation"
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    previous = report["previous_measurement_summary"]
    lines = [
        "# V9 Sealed Rotation Review v1",
        "",
        f"- status: `{report['decision']}`",
        f"- passed: `{report['passed']}`",
        f"- sealed_v9_fixture_created_now: `{report['policy']['sealed_v9_fixture_created_now']}`",
        f"- sealed_v9_opened_for_measurement: `{report['policy']['sealed_v9_opened_for_measurement']}`",
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
            "Fresh sealed v9 rotation is eligible. This review does not create "
            "or open the sealed v9 fixture; it only authorizes the next roadmap "
            "step to generate and rotate it."
            if report["passed"]
            else "Fresh sealed v9 rotation is blocked. Resolve blockers first."
        ),
        "",
        f"- next_action: `{report['next_action']}`",
    ]
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    report = build_report()
    _write_json(OUTPUT_JSON, report)
    _write_markdown(report)
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
