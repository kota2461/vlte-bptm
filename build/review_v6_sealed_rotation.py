"""Review readiness to rotate a fresh PLM sealed v6 fixture.

This Step 4 review is deliberately pre-rotation: it does not create, open, or
measure a sealed v6 fixture. It only verifies that the V6 non-sealed gate is
clean, the previous sealed fixture is consumed, and the registry has no active
sealed fixture.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
STEP3_GATE_PATH = ROOT / "build" / "v6_nonsealed_replay_gate_report_v1.json"
CURRENT_STATE_PATH = ROOT / "build" / "v6_current_state_report_v1.json"
V5_MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v5_measurement_report.json"
OUTPUT_JSON = ROOT / "build" / "v6_sealed_rotation_review_v1.json"
OUTPUT_MD = ROOT / "build" / "v6_sealed_rotation_review_v1.md"
V6_ROADMAP_PATH = ROOT / "docs" / "PLM_V6_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
SEALED_V6_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v6.json"


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


def _build_report() -> dict[str, Any]:
    gate = _load_json(STEP3_GATE_PATH)
    current = _load_json(CURRENT_STATE_PATH)
    registry = _load_json(REGISTRY_PATH)
    v5_measurement = _load_json(V5_MEASUREMENT_PATH)
    active = _active_sealed(registry)
    v5_registry = registry["fixtures"]["pattern_language_sealed_v5.json"]

    blockers: list[str] = []
    if gate["schema_version"] != "v6-nonsealed-replay-gate-report.v1":
        blockers.append("unexpected_step3_gate_schema")
    if gate["status"] != "passed" or gate["passed"] is not True:
        blockers.append("v6_nonsealed_replay_gate_not_passed")
    if gate["summary"]["ready_for_step4_sealed_v6_rotation_review"] is not True:
        blockers.append("step3_gate_did_not_authorize_step4_review")
    if gate["summary"]["required_error_count"] != 0:
        blockers.append("required_nonsealed_lane_errors_present")
    if gate["contract"]["can_use_as_sealed_measurement"] is not False:
        blockers.append("nonsealed_gate_contract_allows_sealed_measurement")
    if gate["contract"]["can_use_for_same_cycle_promotion"] is not False:
        blockers.append("same_cycle_promotion_contract_violation")
    if current["summary"]["gap_lane_count"] != 0:
        blockers.append("v6_current_state_has_gap_lanes")
    if v5_registry["status"] != "consumed" or v5_registry["measured"] is not True:
        blockers.append("previous_sealed_v5_not_consumed")
    if v5_measurement["registry_update"]["rotation_required_before_tuning"] is not True:
        blockers.append("v5_measurement_does_not_require_rotation")
    if v5_measurement["sealed_labels_used_for_tuning"] is not False:
        blockers.append("sealed_v5_labels_used_for_tuning")
    if active:
        blockers.append("active_sealed_fixture_already_exists")
    if SEALED_V6_PATH.exists():
        blockers.append("sealed_v6_fixture_already_exists")

    required_sources = [lane["source"] for lane in gate["required_lanes"]]
    diagnostic_sources = [lane["source"] for lane in gate["diagnostic_lanes"]]
    prior_sealed_sources = [
        name
        for name, entry in registry["fixtures"].items()
        if entry.get("role") == "sealed measurement only"
        or name == "pattern_language_benchmark_v1.json"
    ]

    decision = (
        "eligible_for_fresh_sealed_v6_rotation"
        if not blockers
        else "blocked"
    )
    return {
        "schema_version": "v6-sealed-rotation-review.v1",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "passed": not blockers,
        "policy": {
            "sealed_v6_fixture_created_now": False,
            "sealed_v6_opened_for_measurement": False,
            "sealed_v6_labels_used_for_tuning": False,
            "sealed_v5_text_used_for_training": False,
            "sealed_v5_labels_used_for_tuning": False,
            "sealed_v5_measurement_used_as_taxonomy_only": True,
            "nonsealed_replay_gate_required": True,
            "nonsealed_replay_gate_passed": gate["passed"],
            "draft_or_candidate_lanes_used_as_gate_evidence": False,
            "same_cycle_promotion_allowed": False,
        },
        "sources": {
            "step3_gate": _rel(STEP3_GATE_PATH),
            "current_state": _rel(CURRENT_STATE_PATH),
            "registry": _rel(REGISTRY_PATH),
            "previous_measurement": _rel(V5_MEASUREMENT_PATH),
            "backup": gate["backup"],
        },
        "gate_summary": {
            "required_lane_count": gate["summary"]["required_lane_count"],
            "required_passed_lane_count": gate["summary"]["required_passed_lane_count"],
            "required_error_count": gate["summary"]["required_error_count"],
            "diagnostic_lane_count": gate["summary"]["diagnostic_lane_count"],
            "diagnostic_exact_lane_count": gate["summary"]["diagnostic_exact_lane_count"],
            "diagnostic_error_count": gate["summary"]["diagnostic_error_count"],
            "average_nonsealed_score": gate["summary"]["average_nonsealed_score"],
        },
        "registry_state": {
            "active_sealed_fixtures": active,
            "previous_sealed": {
                "registry_name": "pattern_language_sealed_v5.json",
                "status": v5_registry["status"],
                "measured": v5_registry["measured"],
                "reviewed": v5_registry["reviewed"],
                "measurement_report": v5_registry["measurement_report"],
            },
            "planned_successor": {
                "registry_name": "pattern_language_sealed_v6.json",
                "predecessor": "pattern_language_sealed_v5.json",
                "status": "not_created",
                "measured": False,
                "reviewed": False,
            },
        },
        "previous_measurement_summary": {
            "fixture": v5_measurement["fixture"]["registry_name"],
            "sealed_fixture_opened": v5_measurement["sealed_fixture_opened"],
            "sealed_labels_used_for_tuning": v5_measurement["sealed_labels_used_for_tuning"],
            "intent_accuracy": v5_measurement["measurements"]["intent_accuracy"],
            "critical_signal_recall": v5_measurement["measurements"]["critical_signal_recall"],
            "operation_exact_match": v5_measurement["measurements"]["operation_exact_match"],
            "constraint_exact_match": v5_measurement["measurements"]["constraint_exact_match"],
            "risk_exact_match": v5_measurement["measurements"]["risk_exact_match"],
            "error_count": len(v5_measurement["measurements"]["errors"]),
            "rotation_required_before_tuning": v5_measurement["registry_update"][
                "rotation_required_before_tuning"
            ],
        },
        "planned_v6_fixture_constraints": {
            "case_count": 28,
            "cases_per_intent": 4,
            "split": "sealed",
            "must_be_unopened_until_measurement": True,
            "must_exclude_exact_text_from": {
                "prior_sealed_and_benchmark": prior_sealed_sources,
                "v6_required_nonsealed_gate_lanes": required_sources,
                "v6_diagnostic_nonsealed_lanes": diagnostic_sources,
            },
            "measurement_rule": "measure_once_then_mark_consumed",
            "labels_rule": "sealed labels remain measurement-only and may not tune the same cycle",
        },
        "blockers": blockers,
        "next_action": (
            "roadmap_step5_generate_and_rotate_sealed_v6_fixture"
            if not blockers
            else "resolve_blockers_before_sealed_v6_rotation"
        ),
    }


def _write_markdown(report: dict[str, Any]) -> None:
    planned = report["registry_state"]["planned_successor"]
    previous = report["previous_measurement_summary"]
    lines = [
        "# V6 Sealed Rotation Review v1",
        "",
        f"- status: `{report['decision']}`",
        f"- passed: `{report['passed']}`",
        f"- sealed_v6_fixture_created_now: `{report['policy']['sealed_v6_fixture_created_now']}`",
        f"- sealed_v6_opened_for_measurement: `{report['policy']['sealed_v6_opened_for_measurement']}`",
        f"- same_cycle_promotion_allowed: `{report['policy']['same_cycle_promotion_allowed']}`",
        f"- required_error_count: `{report['gate_summary']['required_error_count']}`",
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
            "Fresh sealed v6 rotation is eligible. This review does not create "
            "or open the sealed v6 fixture; it only authorizes the next "
            "roadmap step to generate and rotate it."
            if report["passed"]
            else "Fresh sealed v6 rotation is blocked. Resolve blockers first."
        ),
        "",
        f"- next_action: `{report['next_action']}`",
    ]
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _write_v6_roadmap(report: dict[str, Any]) -> None:
    status = "completed" if report["passed"] else "blocked"
    content = f"""# PLM V6 Roadmap: Boundary Calibration And Sealed Rotation

Updated: 2026-06-24

## Contract

- Sealed v5 is consumed and may be used only as measurement taxonomy.
- Sealed v5 input text and labels must not be copied into training, review, or non-sealed fixtures.
- V6 tuning uses visible/human-reviewed non-sealed lanes plus diagnostic draft lanes only as diagnostics.
- Draft/candidate lanes are not gate evidence.
- Same-cycle promotion remains disallowed.
- A fresh sealed v6 fixture must be generated and rotated before the next adjudicating measurement.

## Baseline

| Metric | V5 sealed |
|---|---:|
| intent_accuracy | {report['previous_measurement_summary']['intent_accuracy']:.6f} |
| critical_signal_recall | {report['previous_measurement_summary']['critical_signal_recall']:.6f} |
| operation_exact_match | {report['previous_measurement_summary']['operation_exact_match']:.6f} |
| constraint_exact_match | {report['previous_measurement_summary']['constraint_exact_match']:.6f} |
| risk_exact_match | {report['previous_measurement_summary']['risk_exact_match']:.6f} |
| sealed_error_count | {report['previous_measurement_summary']['error_count']} |

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | backup_checkpoint | `archive\\2026-06-24_v6-nonsealed-exact-pre-roadmap-gate` | completed |
| 2 | current_state_report | `build\\v6_current_state_report_v1.json` | completed |
| 3 | nonsealed_replay_gate | `build\\v6_nonsealed_replay_gate_report_v1.json` | completed |
| 4 | sealed_v6_rotation_review | `build\\v6_sealed_rotation_review_v1.json` | {status} |
| 5 | sealed_v6_rotation | `tests\\fixtures\\pattern_language_sealed_v6.json` | next |
| 6 | sealed_v6_one_time_measurement | `build\\pattern_language_sealed_v6_measurement_report.json` | pending |
| 7 | post_v6_measurement_taxonomy | `build\\v7_targets_and_roadmap_v1.json` | pending |

## Step 4 Output

`build\\v6_sealed_rotation_review_v1.json` reports `{report['decision']}`. It confirms that the V6 non-sealed replay gate passed, no active sealed fixture is present, and `pattern_language_sealed_v5.json` is consumed. It does not create, open, or measure `pattern_language_sealed_v6.json`.

## Step 5 Fixture Constraints

- 28 sealed cases, four per intent.
- No exact text overlap with prior benchmark/sealed fixtures.
- No exact text overlap with V6 required non-sealed gate lanes.
- No exact text overlap with V6 diagnostic non-sealed lanes.
- Measure once, then mark consumed before any tuning based on the result.
"""
    V6_ROADMAP_PATH.write_text(content, encoding="utf-8", newline="\n")


def _update_main_roadmap(report: dict[str, Any]) -> None:
    marker = "## PLM V6: Boundary Calibration And Sealed Rotation"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    section = f"""
{marker}

Status: V6 Step 4 sealed v6 rotation review completed; fresh sealed v6 rotation is next.

Primary roadmap: `docs/PLM_V6_ROADMAP.md`
Current state report: `build/v6_current_state_report_v1.json`
Non-sealed replay gate report: `build/v6_nonsealed_replay_gate_report_v1.json`
Sealed v6 rotation review: `build/v6_sealed_rotation_review_v1.json`

V6 non-sealed required lanes are exact and the replay gate passed with zero required errors. Draft/candidate lanes remain diagnostic rather than gate evidence. Sealed v5 is consumed and may be used only as measurement taxonomy. Step 4 did not create or open a sealed v6 fixture; Step 5 should generate and rotate a fresh unopened `pattern_language_sealed_v6.json`.
""".strip()
    if marker in main:
        head, _ = main.split(marker, 1)
        main = head.rstrip() + "\n\n" + section + "\n"
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    report = _build_report()
    _write_json(OUTPUT_JSON, report)
    _write_markdown(report)
    _write_v6_roadmap(report)
    _update_main_roadmap(report)
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
