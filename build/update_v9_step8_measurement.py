"""Record V9 Step 8 sealed measurement state in targets and roadmaps."""

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v9_measurement_report.json"
TARGETS_PATH = ROOT / "build" / "v9_targets_and_roadmap_v1.json"
ROADMAP_PATH = ROOT / "docs" / "PLM_V9_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"
SUMMARY_PATH = ROOT / "build" / "v9_step8_measurement_summary.md"
READINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


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


def _replace_section(text: str, heading: str, section: str) -> str:
    if heading not in text:
        return text.rstrip() + "\n\n" + section + "\n"
    head, rest = text.split(heading, 1)
    idx = rest.find("\n## ")
    if idx == -1:
        return head.rstrip() + "\n\n" + section + "\n"
    return head.rstrip() + "\n\n" + section + "\n\n" + rest[idx + 1 :]


def build_update() -> dict[str, Any]:
    measurement = _load_json(MEASUREMENT_PATH)
    readiness = _load_json(READINESS_PATH)
    targets = _load_json(TARGETS_PATH)
    metrics = measurement["measurements"]
    minimum = targets["targets"]["minimum"]
    field_counts = _field_counts(metrics["errors"])
    critical_miss_count = _critical_signal_miss_count(metrics["critical_signals"])
    minimum_metrics_met = (
        metrics["intent_accuracy"] >= minimum["intent_accuracy"]
        and metrics["critical_signal_recall"] >= minimum["critical_signal_recall"]
        and metrics["operation_exact_match"] >= minimum["operation_exact_match"]
        and metrics["constraint_exact_match"] >= minimum["constraint_exact_match"]
        and metrics["risk_exact_match"] >= minimum["risk_exact_match"]
        and len(metrics["errors"]) <= minimum["sealed_error_count_max"]
    )
    critical_miss_gate_met = critical_miss_count <= minimum["critical_signal_miss_count_max"]
    passed_minimum = minimum_metrics_met and critical_miss_gate_met

    targets["generated_at"] = measurement["measured_at"]
    targets["status"] = "step8_sealed_v9_measurement_completed_v10_rotation_required"
    targets["next_action"] = "roadmap_v10_step1_post_v9_measurement_taxonomy"
    targets["sources"]["sealed_v9_measurement"] = "build\\pattern_language_sealed_v9_measurement_report.json"
    for item in targets["roadmap"]:
        item["status"] = "completed"
    targets["step8_sealed_measurement"] = {
        "output": "build\\pattern_language_sealed_v9_measurement_report.json",
        "summary": "build\\v9_step8_measurement_summary.md",
        "fixture": "tests\\fixtures\\pattern_language_sealed_v9.json",
        "sealed_fixture_opened": measurement["sealed_fixture_opened"],
        "sealed_labels_used_for_tuning": measurement["sealed_labels_used_for_tuning"],
        "passed_minimum": passed_minimum,
        "minimum_metrics_met": minimum_metrics_met,
        "critical_signal_miss_count": critical_miss_count,
        "critical_signal_miss_gate_met": critical_miss_gate_met,
        "rotation_required_before_tuning": measurement["registry_update"][
            "rotation_required_before_tuning"
        ],
        "readiness_after_measurement": {
            "decision": readiness["decision"],
            "blocked_reasons": readiness["blocked_reasons"],
            "sealed_fixture": readiness["sealed_fixture"],
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
    _write_json(TARGETS_PATH, targets)

    lines = [
        "# V9 Step 8 Sealed Measurement Summary",
        "",
        f"- fixture: `{measurement['fixture']['registry_name']}`",
        f"- measured_at: `{measurement['measured_at']}`",
        f"- sealed_fixture_opened: `{measurement['sealed_fixture_opened']}`",
        f"- sealed_labels_used_for_tuning: `{measurement['sealed_labels_used_for_tuning']}`",
        f"- status_after_measurement: `{measurement['registry_update']['status_after_measurement']}`",
        f"- rotation_required_before_tuning: `{measurement['registry_update']['rotation_required_before_tuning']}`",
        f"- minimum_passed: `{passed_minimum}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value | Target |",
        "|---|---:|---:|",
        f"| case_count | {metrics['case_count']} | 28 |",
        f"| intent_accuracy | {metrics['intent_accuracy']:.6f} | {minimum['intent_accuracy']:.6f} |",
        f"| critical_signal_recall | {metrics['critical_signal_recall']:.6f} | {minimum['critical_signal_recall']:.6f} |",
        f"| operation_exact_match | {metrics['operation_exact_match']:.6f} | {minimum['operation_exact_match']:.6f} |",
        f"| constraint_exact_match | {metrics['constraint_exact_match']:.6f} | {minimum['constraint_exact_match']:.6f} |",
        f"| risk_exact_match | {metrics['risk_exact_match']:.6f} | {minimum['risk_exact_match']:.6f} |",
        f"| error_count | {len(metrics['errors'])} | <= {minimum['sealed_error_count_max']} |",
        "",
        "## Critical Signals",
        "",
        "| Signal | Recall | Support |",
        "|---|---:|---:|",
    ]
    for signal, item in metrics["critical_signals"].items():
        lines.append(f"| {signal} | {item['recall']:.6f} | {item['support']} |")
    lines.extend(["", "## Error Field Counts", "", "| Field | Count |", "|---|---:|"])
    for field, count in field_counts.items():
        lines.append(f"| {field} | {count} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "V9 met the sealed minimum target, but the sealed v9 fixture is consumed. "
                "Sealed labels remain measurement-only, and fresh rotation is still required before any tuning from this result."
                if passed_minimum
                else "V9 did not meet the sealed minimum target. The sealed v9 fixture is consumed, sealed labels remain measurement-only, and fresh rotation is required before tuning from this result."
            ),
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 8 | sealed_v9_one_time_measurement | `build\\pattern_language_sealed_v9_measurement_report.json` | next |",
        "| 8 | sealed_v9_one_time_measurement | `build\\pattern_language_sealed_v9_measurement_report.json` | completed |",
    )
    section = (
        "## Step 8 Output\n\n"
        "`build\\pattern_language_sealed_v9_measurement_report.json` measured the active sealed v9 fixture once and consumed it. "
        f"Results: intent_accuracy `{metrics['intent_accuracy']:.6f}`, "
        f"critical_signal_recall `{metrics['critical_signal_recall']:.6f}`, "
        f"operation_exact_match `{metrics['operation_exact_match']:.6f}`, "
        f"constraint_exact_match `{metrics['constraint_exact_match']:.6f}`, "
        f"risk_exact_match `{metrics['risk_exact_match']:.6f}`, errors `{len(metrics['errors'])}`. "
        "Sealed labels remain measurement-only and V10 taxonomy/rotation is required before tuning."
    )
    ROADMAP_PATH.write_text(
        _replace_section(roadmap, "## Step 8 Output", section),
        encoding="utf-8",
        newline="\n",
    )

    marker = "## PLM V9: Exactness Recovery And Fresh Rotation"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    main_section = f"""
{marker}

Status: V9 Step 8 sealed v9 measurement completed; sealed v9 consumed; V10 taxonomy and fresh rotation required before tuning.

Primary roadmap: `docs/PLM_V9_ROADMAP.md`
Targets and taxonomy: `build/v9_targets_and_roadmap_v1.json`
Candidate selection: `build/v9_accumulated_log_candidate_selection_v1.json`
Primary review replay: `build/v9_accumulated_primary_review_replay_report_v1.json`
Constraint/operation extension replay: `build/v9_constraint_operation_extension_replay_report_v1.json`
Non-sealed replay gate report: `build/v9_nonsealed_replay_gate_report_v1.json`
Sealed v9 rotation review: `build/v9_sealed_rotation_review_v1.json`
Sealed v9 rotation report: `build/v9_sealed_rotation_report_v1.json`
Sealed v9 measurement: `build/pattern_language_sealed_v9_measurement_report.json`
Sealed v9 summary: `build/v9_step8_measurement_summary.md`
Baseline sealed v8 measurement: `build/pattern_language_sealed_v8_measurement_report.json`

Step 8 measured sealed v9 once and consumed it: intent_accuracy {metrics['intent_accuracy']:.6f}, critical_signal_recall {metrics['critical_signal_recall']:.6f}, operation_exact_match {metrics['operation_exact_match']:.6f}, constraint_exact_match {metrics['constraint_exact_match']:.6f}, risk_exact_match {metrics['risk_exact_match']:.6f}, errors {len(metrics['errors'])}. Sealed labels remain measurement-only; use this result for V10 taxonomy and fresh rotation planning, not same-cycle tuning.
""".strip()
    MAIN_ROADMAP_PATH.write_text(
        _replace_section(main, marker, main_section),
        encoding="utf-8",
        newline="\n",
    )

    return {
        "passed_minimum": passed_minimum,
        "minimum_metrics_met": minimum_metrics_met,
        "critical_signal_miss_count": critical_miss_count,
        "critical_signal_miss_gate_met": critical_miss_gate_met,
        "error_field_counts": field_counts,
    }


def main() -> None:
    print(json.dumps(build_update(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
