"""Create the V8 targets, taxonomy, and rotation roadmap.

The sealed v7 fixture is consumed. This script uses the sealed v7 measurement
only as aggregate taxonomy and records the approved V8 non-sealed recovery gate
as roadmap evidence. It does not copy sealed case text or labels.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_routing.reproducibility import reproducible_now_iso
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v7_measurement_report.json"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
V8_GATE_PATH = ROOT / "build" / "v8_nonsealed_replay_gate_report_v1.json"
V8_ROTATION_REVIEW_PATH = ROOT / "build" / "v8_sealed_rotation_review_v1.json"
V8_ROTATION_REPORT_PATH = ROOT / "build" / "v8_sealed_rotation_report_v1.json"
V8_MEASUREMENT_REPORT_PATH = ROOT / "build" / "pattern_language_sealed_v8_measurement_report.json"
V8_PROVISIONAL_REPORT_PATH = ROOT / "build" / "v8_recovery_priority_review_provisional_test_report_v1.json"
V8_PRIORITY_SELECTION_PATH = ROOT / "build" / "v8_recovery_debate_candidate_priority_selection_v1.json"
OUTPUT_JSON = ROOT / "build" / "v8_targets_and_roadmap_v1.json"
OUTPUT_MD = ROOT / "docs" / "PLM_V8_ROADMAP.md"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


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


def _metric_targets() -> dict[str, Any]:
    return {
        "minimum": {
            "intent_accuracy": 0.892857,
            "critical_signal_recall": 0.857143,
            "operation_exact_match": 0.857143,
            "constraint_exact_match": 0.857143,
            "risk_exact_match": 0.892857,
            "sealed_error_count_max": 8,
            "critical_signal_miss_count_max": 2,
        },
        "stretch": {
            "intent_accuracy": 0.928571,
            "critical_signal_recall": 0.928571,
            "operation_exact_match": 0.928571,
            "constraint_exact_match": 0.928571,
            "risk_exact_match": 0.928571,
            "sealed_error_count_max": 5,
            "critical_signal_miss_count_max": 1,
        },
        "granularity": {
            "case_metric_step": 0.035714,
            "critical_signal_step": 0.071429,
        },
    }


def _taxonomy(measurement: dict[str, Any]) -> dict[str, Any]:
    metrics = measurement["measurements"]
    field_counts: Counter[str] = Counter()
    by_expected_intent: dict[str, Counter[str]] = defaultdict(Counter)
    by_predicted_intent: dict[str, Counter[str]] = defaultdict(Counter)
    transitions: Counter[str] = Counter()
    for error in metrics["errors"]:
        field_counts.update(error["fields"])
        expected = error["expected_intent"]
        predicted = error["predicted_intent"]
        by_expected_intent[expected].update(error["fields"])
        by_predicted_intent[predicted].update(error["fields"])
        if expected != predicted:
            transitions[f"{expected}->{predicted}"] += 1

    misses = {
        name: round(signal["support"] * (1.0 - signal["recall"]))
        for name, signal in metrics["critical_signals"].items()
    }

    focus_areas = [
        {
            "id": "clarify_missing_info_recovery",
            "priority": 1,
            "generalized_issue": "missing inputs and ask-first requests still drift into build or verify too early",
            "evidence": {
                "clarify_recall": metrics["per_intent"]["clarify"]["recall"],
                "missing_required_information_misses": misses["missing_required_information"],
            },
            "covered_by_v8_categories": ["missing_info", "multiple_intents"],
        },
        {
            "id": "operation_terminal_sequence",
            "priority": 1,
            "generalized_issue": "terminal actions and multi-step requests need stable operation order",
            "evidence": {
                "field": "operations",
                "count": field_counts["operations"],
                "metric": metrics["operation_exact_match"],
            },
            "covered_by_v8_categories": ["multiple_intents", "operation_terminal"],
        },
        {
            "id": "constraint_false_positive_balance",
            "priority": 1,
            "generalized_issue": "format and tone constraints must be preserved without over-firing risk or verify",
            "evidence": {
                "field": "constraints",
                "count": field_counts["constraints"],
                "metric": metrics["constraint_exact_match"],
            },
            "covered_by_v8_categories": ["constraints", "false_positive", "no-risk contrast"],
        },
        {
            "id": "risk_ladder_boundary",
            "priority": 2,
            "generalized_issue": "AI, legal, and medical terms need low/medium/high separation by actual user intent",
            "evidence": {
                "field": "risk",
                "count": field_counts["risk"],
                "metric": metrics["risk_exact_match"],
            },
            "covered_by_v8_categories": ["risk_ladder", "false_positive"],
        },
        {
            "id": "current_search_split",
            "priority": 2,
            "generalized_issue": "current-looking local context must not become unnecessary web/current routing",
            "evidence": {
                "requires_current_information_misses": misses["requires_current_information"],
            },
            "covered_by_v8_categories": ["current_search_split"],
        },
        {
            "id": "paraphrase_and_mixed_language_robustness",
            "priority": 2,
            "generalized_issue": "the same boundary should hold under paraphrase and mixed Japanese/English phrasing",
            "evidence": {
                "intent_accuracy": metrics["intent_accuracy"],
                "transitions": dict(sorted(transitions.items())),
            },
            "covered_by_v8_categories": ["paraphrase", "mixed_language"],
        },
        {
            "id": "unverified_claim_guard",
            "priority": 2,
            "generalized_issue": "vendor, legal, and report claims should trigger verification only when a claim is actually asserted",
            "evidence": {
                "contains_unverified_claims_misses": misses["contains_unverified_claims"],
            },
            "covered_by_v8_categories": ["unverified_claim", "current_search_split"],
        },
    ]
    return {
        "field_error_counts": dict(sorted(field_counts.items())),
        "critical_signal_miss_counts": misses,
        "intent_boundary_transitions": dict(sorted(transitions.items())),
        "by_expected_intent": {
            intent: dict(counter)
            for intent, counter in sorted(by_expected_intent.items())
        },
        "by_predicted_intent": {
            intent: dict(counter)
            for intent, counter in sorted(by_predicted_intent.items())
        },
        "focus_areas": focus_areas,
    }


def _roadmap() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "name": "post_v7_measurement_taxonomy",
            "output": "build\\v8_targets_and_roadmap_v1.json",
            "status": "completed",
        },
        {
            "step": 2,
            "name": "v8_recovery_debate_stock",
            "output": "debate_lab\\topics_v8_recovery_100.json",
            "status": "completed",
        },
        {
            "step": 3,
            "name": "v8_recovery_candidate_priority_selection",
            "output": "build\\v8_recovery_debate_candidate_priority_selection_v1.json",
            "status": "completed",
        },
        {
            "step": 4,
            "name": "v8_priority_review_adoption_and_replay",
            "output": "build\\v8_recovery_priority_review_provisional_test_report_v1.json",
            "status": "completed",
        },
        {
            "step": 5,
            "name": "v8_nonsealed_replay_gate",
            "output": "build\\v8_nonsealed_replay_gate_report_v1.json",
            "status": "completed",
        },
        {
            "step": 6,
            "name": "sealed_v8_rotation_review",
            "output": "build\\v8_sealed_rotation_review_v1.json",
            "status": "next",
        },
        {
            "step": 7,
            "name": "sealed_v8_rotation",
            "output": "tests\\fixtures\\pattern_language_sealed_v8.json",
            "status": "pending",
        },
        {
            "step": 8,
            "name": "sealed_v8_one_time_measurement",
            "output": "build\\pattern_language_sealed_v8_measurement_report.json",
            "status": "pending",
        },
    ]


def build_payload() -> dict[str, Any]:
    measurement = _load_json(MEASUREMENT_PATH)
    readiness = _load_json(READINESS_PATH)
    registry = _load_json(REGISTRY_PATH)
    gate = _load_json(V8_GATE_PATH)
    provisional = _load_json(V8_PROVISIONAL_REPORT_PATH)
    priority = _load_json(V8_PRIORITY_SELECTION_PATH)
    metrics = measurement["measurements"]
    fixture_name = measurement["fixture"]["registry_name"]
    registry_entry = registry["fixtures"][fixture_name]
    targets = _metric_targets()

    return {
        "schema_version": "v8-targets-and-roadmap.v1",
        "generated_at": reproducible_now_iso(),
        "status": "step5_v8_nonsealed_replay_gate_passed_step6_rotation_review_next",
        "sources": {
            "sealed_v7_measurement": _rel(MEASUREMENT_PATH),
            "readiness_review": _rel(READINESS_PATH),
            "fixture_registry": _rel(REGISTRY_PATH),
            "v8_priority_selection": _rel(V8_PRIORITY_SELECTION_PATH),
            "v8_provisional_replay": _rel(V8_PROVISIONAL_REPORT_PATH),
            "v8_nonsealed_replay_gate": _rel(V8_GATE_PATH),
        },
        "policy": {
            "sealed_v7_consumed": registry_entry["status"] == "consumed",
            "sealed_v7_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
            "sealed_v7_text_used_for_training": False,
            "sealed_v7_measurement_used_as_taxonomy_only": True,
            "v8_priority_review_human_approved": gate["policy"]["v8_priority_review_human_approved"],
            "v8_nonsealed_replay_gate_passed": gate["passed"],
            "prior_v8_provisional_replay_was_gate": provisional["current_route_measurement_is_gate"],
            "raw_debate_logs_direct_training_allowed": False,
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_successor_required_before_measurement": True,
        },
        "baseline": {
            "fixture": fixture_name,
            "case_count": metrics["case_count"],
            "intent_accuracy": metrics["intent_accuracy"],
            "critical_signal_recall": metrics["critical_signal_recall"],
            "operation_exact_match": metrics["operation_exact_match"],
            "constraint_exact_match": metrics["constraint_exact_match"],
            "risk_exact_match": metrics["risk_exact_match"],
            "sealed_error_count": len(metrics["errors"]),
            "readiness_decision_after_measurement": "blocked",
            "blocked_reasons": ["sealed_fixture_not_available"],
        },
        "targets": targets,
        "taxonomy": _taxonomy(measurement),
        "nonsealed_recovery_summary": {
            "source_topic_count": priority["summary"]["source_candidate_count"],
            "priority_review_count": priority["summary"]["priority_review_count"],
            "priority_category_counts": priority["summary"]["priority_category_counts"],
            "v8_gate_required_error_count": gate["summary"]["required_error_count"],
            "v8_gate_case_count": gate["summary"]["v8_priority_review_case_count"],
            "v8_gate_exact": gate["summary"]["v8_priority_review_exact"],
        },
        "pre_rotation_gates": {
            "prior_v7_nonsealed_gate_required": True,
            "v8_priority_review_exact_required": True,
            "v8_nonsealed_gate_error_count_max": 0,
            "sealed_overlap_count_required": 0,
        },
        "roadmap": _roadmap(),
        "next_action": "roadmap_v8_step6_sealed_rotation_review",
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]
    targets = payload["targets"]
    taxonomy = payload["taxonomy"]
    lines = [
        "# PLM V8 Roadmap: Recovery Gate And Fresh Rotation",
        "",
        "Updated: 2026-06-25",
        "",
        "## Contract",
        "",
        "- Sealed v7 is consumed and may be used only as aggregate taxonomy.",
        "- Sealed v7 text and labels must not be copied into training, review, or non-sealed fixtures.",
        "- V8 uses human-approved non-sealed recovery samples and a separate non-sealed replay gate.",
        "- Same-cycle promotion remains disallowed.",
        "- A fresh sealed v8 fixture is required before the next adjudicating measurement.",
        "",
        "## Baseline And Targets",
        "",
        "| Metric | V7 sealed | V8 minimum | V8 stretch |",
        "|---|---:|---:|---:|",
        f"| intent_accuracy | {baseline['intent_accuracy']:.6f} | {targets['minimum']['intent_accuracy']:.6f} | {targets['stretch']['intent_accuracy']:.6f} |",
        f"| critical_signal_recall | {baseline['critical_signal_recall']:.6f} | {targets['minimum']['critical_signal_recall']:.6f} | {targets['stretch']['critical_signal_recall']:.6f} |",
        f"| operation_exact_match | {baseline['operation_exact_match']:.6f} | {targets['minimum']['operation_exact_match']:.6f} | {targets['stretch']['operation_exact_match']:.6f} |",
        f"| constraint_exact_match | {baseline['constraint_exact_match']:.6f} | {targets['minimum']['constraint_exact_match']:.6f} | {targets['stretch']['constraint_exact_match']:.6f} |",
        f"| risk_exact_match | {baseline['risk_exact_match']:.6f} | {targets['minimum']['risk_exact_match']:.6f} | {targets['stretch']['risk_exact_match']:.6f} |",
        f"| sealed_error_count | {baseline['sealed_error_count']} | <= {targets['minimum']['sealed_error_count_max']} | <= {targets['stretch']['sealed_error_count_max']} |",
        "",
        "## Error Taxonomy",
        "",
        "| Field | Count |",
        "|---|---:|",
    ]
    for field, count in taxonomy["field_error_counts"].items():
        lines.append(f"| {field} | {count} |")
    lines.extend(["", "## Focus Areas", ""])
    for item in taxonomy["focus_areas"]:
        lines.append(f"{item['priority']}. {item['id']}: {item['generalized_issue']}")
    lines.extend(["", "## Roadmap", "", "| Step | Name | Output | Status |", "|---:|---|---|---|"])
    for step in payload["roadmap"]:
        lines.append(f"| {step['step']} | {step['name']} | `{step['output']}` | {step['status']} |")
    lines.extend(
        [
            "",
            "## Step 5 Output",
            "",
            "`build\\v8_nonsealed_replay_gate_report_v1.json` passed after human approval of the V8 priority review set. It confirms the prior V7 non-sealed gate, replays the 30-case V8 approved benchmark exactly, and keeps the earlier provisional replay marked as non-gate evidence. Step 6 is sealed V8 rotation review.",
        ]
    )
    if payload.get("step6_sealed_rotation_review"):
        lines.extend(
            [
                "",
                "## Step 6 Output",
                "",
                "`build\\v8_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v8_rotation`. It confirms that the V8 non-sealed replay gate passed, `pattern_language_sealed_v7.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v8.json` has not been created. This review does not create, open, or measure sealed v8. Step 7 is now sealed V8 rotation.",
            ]
        )
    if payload.get("step7_sealed_rotation"):
        lines.extend(
            [
                "",
                "## Step 7 Output",
                "",
                "`build\\v8_sealed_rotation_report_v1.json` created `tests\\fixtures\\pattern_language_sealed_v8.json` as the active unopened sealed fixture. Step 8 is the one-time sealed v8 measurement.",
            ]
        )
    if payload.get("step8_sealed_measurement"):
        measurement = payload["step8_sealed_measurement"]["measurements"]
        lines.extend(
            [
                "",
                "## Step 8 Output",
                "",
                f"`build\\pattern_language_sealed_v8_measurement_report.json` measured the active sealed v8 fixture once and consumed it. Results: intent_accuracy `{measurement['intent_accuracy']:.6f}`, critical_signal_recall `{measurement['critical_signal_recall']:.6f}`, operation_exact_match `{measurement['operation_exact_match']:.6f}`, constraint_exact_match `{measurement['constraint_exact_match']:.6f}`, risk_exact_match `{measurement['risk_exact_match']:.6f}`, errors `{measurement['error_count']}`. Sealed labels remain measurement-only and V9 taxonomy/rotation is required before tuning.",
            ]
        )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _update_v7_roadmap() -> None:
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    section = (
        "## Step 9 Output\n\n"
        "`build\\v8_targets_and_roadmap_v1.json` and `docs\\PLM_V8_ROADMAP.md` "
        "convert the consumed sealed v7 result into aggregate V8 taxonomy, "
        "record the human-approved V8 non-sealed replay gate, and set Step 6 "
        "as sealed V8 rotation review. Sealed v7 text and labels remain excluded from training.\n"
    )
    if "## Step 9 Output" in roadmap:
        head, _ = roadmap.split("## Step 9 Output", 1)
        roadmap = head.rstrip() + "\n\n" + section
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section
    V7_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")


def _update_main_roadmap(payload: dict[str, Any]) -> None:
    marker = "## PLM V8: Recovery Gate And Fresh Rotation"
    baseline = payload["baseline"]
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    step6_done = bool(payload.get("step6_sealed_rotation_review"))
    step7_done = bool(payload.get("step7_sealed_rotation"))
    step8_done = bool(payload.get("step8_sealed_measurement"))
    if step8_done:
        m = payload["step8_sealed_measurement"]["measurements"]
        status_line = "V8 Step 8 sealed v8 measurement completed; sealed v8 consumed; V9 taxonomy and fresh rotation required before tuning."
        review_line = "Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`\nSealed v8 rotation report: `build/v8_sealed_rotation_report_v1.json`\nSealed v8 measurement: `build/pattern_language_sealed_v8_measurement_report.json`\nSealed v8 summary: `build/v8_step8_measurement_summary.md`\n"
        final_sentence = f"Step 8 measured sealed v8 once and consumed it: intent_accuracy {m['intent_accuracy']:.6f}, critical_signal_recall {m['critical_signal_recall']:.6f}, operation_exact_match {m['operation_exact_match']:.6f}, constraint_exact_match {m['constraint_exact_match']:.6f}, risk_exact_match {m['risk_exact_match']:.6f}, errors {m['error_count']}. Sealed labels remain measurement-only; use this result for V9 taxonomy and fresh rotation planning, not same-cycle tuning."
    elif step7_done:
        status_line = "V8 Step 7 sealed v8 rotation completed; sealed v8 active/unmeasured; Step 8 one-time sealed v8 measurement next."
        review_line = "Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`\nSealed v8 rotation report: `build/v8_sealed_rotation_report_v1.json`\nSealed v8 fixture: `tests/fixtures/pattern_language_sealed_v8.json`\n"
        final_sentence = "The approved V8 priority review replay is exact on 30 non-sealed cases, Step 6 sealed rotation review authorized fresh sealed v8 rotation, and Step 7 rotated a fresh unopened `pattern_language_sealed_v8.json` into the active measurement slot. Step 8 is the one-time adjudicating measurement."
    elif step6_done:
        status_line = "V8 Step 6 sealed rotation review completed; Step 7 sealed v8 rotation next."
        review_line = "Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`\n"
        final_sentence = "The approved V8 priority review replay is exact on 30 non-sealed cases, and Step 6 sealed rotation review authorized fresh sealed v8 rotation. Step 7 should generate and rotate a fresh unopened `pattern_language_sealed_v8.json`."
    else:
        status_line = "V8 Step 5 non-sealed replay gate passed; Step 6 sealed rotation review next."
        review_line = ""
        final_sentence = "The approved V8 priority review replay is exact on 30 non-sealed cases; Step 6 should review eligibility for fresh sealed v8 rotation before any adjudicating measurement."
    section = f"""
{marker}

Status: {status_line}

Primary roadmap: `docs/PLM_V8_ROADMAP.md`
Targets and taxonomy: `build/v8_targets_and_roadmap_v1.json`
Recovery priority selection: `build/v8_recovery_debate_candidate_priority_selection_v1.json`
Approved priority replay: `build/v8_recovery_priority_review_provisional_test_report_v1.json`
Non-sealed replay gate report: `build/v8_nonsealed_replay_gate_report_v1.json`
{review_line}Baseline sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`

V8 uses sealed v7 measurement only as aggregate taxonomy. Sealed v7 text and labels are not training data. V7 measured intent_accuracy {baseline['intent_accuracy']:.6f}, critical_signal_recall {baseline['critical_signal_recall']:.6f}, operation_exact_match {baseline['operation_exact_match']:.6f}, constraint_exact_match {baseline['constraint_exact_match']:.6f}, risk_exact_match {baseline['risk_exact_match']:.6f}, errors {baseline['sealed_error_count']}. {final_sentence}
""".strip()
    if marker in main:
        head, rest = main.split(marker, 1)
        idx = rest.find("\n## ")
        if idx == -1:
            main = head.rstrip() + "\n\n" + section + "\n"
        else:
            main = head.rstrip() + "\n\n" + section + "\n\n" + rest[idx + 1 :]
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def _existing_step6_review() -> dict[str, Any] | None:
    if not V8_ROTATION_REVIEW_PATH.exists():
        return None
    review = _load_json(V8_ROTATION_REVIEW_PATH)
    if review.get("schema_version") != "v8-sealed-rotation-review.v1":
        return None
    if review.get("passed") is not True:
        return None
    return review


def _preserve_step6_review_state(payload: dict[str, Any]) -> dict[str, Any]:
    review = _existing_step6_review()
    if review is None:
        return payload
    payload["generated_at"] = review["reviewed_at"]
    payload["status"] = "step6_sealed_rotation_review_completed_step7_rotation_next"
    payload["next_action"] = "roadmap_v8_step7_generate_and_rotate_sealed_v8_fixture"
    for item in payload["roadmap"]:
        if item["step"] == 6:
            item["status"] = "completed"
        elif item["step"] == 7:
            item["status"] = "next"
    payload["step6_sealed_rotation_review"] = {
        "output": "build\\v8_sealed_rotation_review_v1.json",
        "decision": review["decision"],
        "passed": review["passed"],
        "sealed_v8_fixture_created_now": False,
        "sealed_v8_opened_for_measurement": False,
        "same_cycle_promotion_allowed": False,
        "requires_fresh_sealed_v8_before_measurement": True,
        "summary": {
            "required_error_count": review["gate_summary"]["required_error_count"],
            "active_sealed_fixtures": len(review["registry_state"]["active_sealed_fixtures"]),
            "blocker_count": len(review["blockers"]),
        },
    }
    return payload


def _existing_step7_rotation() -> dict[str, Any] | None:
    if not V8_ROTATION_REPORT_PATH.exists():
        return None
    report = _load_json(V8_ROTATION_REPORT_PATH)
    if report.get("schema_version") != "v8-sealed-rotation-report.v1":
        return None
    rotated_to = report.get("rotated_to", {})
    if rotated_to.get("status") != "active" or rotated_to.get("measured") is not False:
        return None
    return report


def _preserve_step7_rotation_state(payload: dict[str, Any]) -> dict[str, Any]:
    report = _existing_step7_rotation()
    if report is None:
        return payload
    payload["generated_at"] = report["rotated_at"]
    payload["status"] = "step7_sealed_rotation_completed_step8_measurement_next"
    payload["next_action"] = "roadmap_v8_step8_measure_active_sealed_v8_once"
    for item in payload["roadmap"]:
        if item["step"] in {6, 7}:
            item["status"] = "completed"
        elif item["step"] == 8:
            item["status"] = "next"
    payload["step7_sealed_rotation"] = {
        "output": "build\\v8_sealed_rotation_report_v1.json",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v8.json",
        "passed": True,
        "sealed_v8_opened_for_measurement": False,
        "sealed_v8_labels_used_for_tuning": False,
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
    return payload


def _field_counts(errors: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for error in errors:
        for field in error["fields"]:
            counts[field] = counts.get(field, 0) + 1
    return dict(sorted(counts.items()))


def _critical_signal_miss_count(signals: dict[str, dict[str, Any]]) -> int:
    misses = 0
    for signal in signals.values():
        misses += round(signal["support"] * (1.0 - signal["recall"]))
    return misses


def _existing_step8_measurement() -> dict[str, Any] | None:
    if not V8_MEASUREMENT_REPORT_PATH.exists():
        return None
    report = _load_json(V8_MEASUREMENT_REPORT_PATH)
    if report.get("schema_version") != "plm-sealed-measurement-report.v1":
        return None
    if report.get("fixture", {}).get("registry_name") != "pattern_language_sealed_v8.json":
        return None
    if report.get("registry_update", {}).get("status_after_measurement") != "consumed":
        return None
    return report


def _preserve_step8_measurement_state(payload: dict[str, Any]) -> dict[str, Any]:
    measurement = _existing_step8_measurement()
    if measurement is None:
        return payload
    metrics = measurement["measurements"]
    minimum = payload["targets"]["minimum"]
    field_counts = _field_counts(metrics["errors"])
    critical_signal_miss_count = _critical_signal_miss_count(metrics["critical_signals"])
    minimum_metrics_met = (
        metrics["intent_accuracy"] >= minimum["intent_accuracy"]
        and metrics["critical_signal_recall"] >= minimum["critical_signal_recall"]
        and metrics["operation_exact_match"] >= minimum["operation_exact_match"]
        and metrics["constraint_exact_match"] >= minimum["constraint_exact_match"]
        and metrics["risk_exact_match"] >= minimum["risk_exact_match"]
        and len(metrics["errors"]) <= minimum["sealed_error_count_max"]
    )
    critical_signal_miss_gate_met = critical_signal_miss_count <= minimum["critical_signal_miss_count_max"]
    payload["generated_at"] = measurement["measured_at"]
    payload["status"] = "step8_sealed_v8_measurement_completed_v9_rotation_required"
    payload["next_action"] = "roadmap_v9_step1_post_v8_measurement_taxonomy"
    for item in payload["roadmap"]:
        item["status"] = "completed"
    payload["step8_sealed_measurement"] = {
        "output": "build\\pattern_language_sealed_v8_measurement_report.json",
        "summary": "build\\v8_step8_measurement_summary.md",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v8.json",
        "sealed_fixture_opened": measurement["sealed_fixture_opened"],
        "sealed_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
        "passed_minimum": minimum_metrics_met and critical_signal_miss_gate_met,
        "minimum_metrics_met": minimum_metrics_met,
        "critical_signal_miss_count": critical_signal_miss_count,
        "critical_signal_miss_gate_met": critical_signal_miss_gate_met,
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
    return payload


def main() -> None:
    payload = _preserve_step8_measurement_state(_preserve_step7_rotation_state(_preserve_step6_review_state(build_payload())))
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(payload)
    _update_v7_roadmap()
    _update_main_roadmap(payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "output": _rel(OUTPUT_JSON),
                "roadmap": _rel(OUTPUT_MD),
                "next_action": payload["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
