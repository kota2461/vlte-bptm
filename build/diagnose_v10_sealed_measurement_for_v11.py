"""Diagnose consumed sealed v10 measurement for V11 taxonomy planning.

This report may inspect consumed sealed v10 labels only as post-measurement
taxonomy. It is not training data, not a replay gate, and not same-cycle
promotion evidence.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_sealed_fixture, route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso


SEALED_V10_PATH = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v10.json"
MEASUREMENT_PATH = ROOT / "build" / "pattern_language_sealed_v10_measurement_report.json"
BRIDGE_PATH = ROOT / "tests" / "fixtures" / "v10_thought_color_bridge_isolated_benchmark_v1.json"
OUTPUT_JSON = ROOT / "build" / "v11_post_v10_measurement_diagnostic_v1.json"
OUTPUT_MD = ROOT / "build" / "v11_post_v10_measurement_diagnostic_v1.md"


CRITICAL_SIGNALS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _packet_core(packet: Any) -> dict[str, Any]:
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
    }


def _expected_core(case: Any) -> dict[str, Any]:
    expected = case.expected.as_dict()
    return {
        "primary_intent": expected["primary_intent"],
        "operations": expected["operations"],
        "information_state": expected["information_state"],
        "constraints": expected["constraints"],
        "risk": expected["risk"],
    }


def _diff_values(expected: dict[str, Any], predicted: dict[str, Any]) -> dict[str, Any]:
    diff: dict[str, Any] = {}
    for field in ("primary_intent", "operations"):
        if expected[field] != predicted[field]:
            diff[field] = {"expected": expected[field], "predicted": predicted[field]}
    for field in ("information_state", "constraints", "risk"):
        subdiff = {}
        for key, expected_value in expected[field].items():
            predicted_value = predicted[field][key]
            if expected_value != predicted_value:
                subdiff[key] = {"expected": expected_value, "predicted": predicted_value}
        if subdiff:
            diff[field] = subdiff
    return diff


def _field_set(diff: dict[str, Any]) -> list[str]:
    return [field for field in ("primary_intent", "information_state", "constraints", "risk", "operations") if field in diff]


def _mode(expected: dict[str, Any], predicted: dict[str, Any]) -> str:
    if expected["primary_intent"] != predicted["primary_intent"]:
        return "intent_mismatch"
    return "intent_correct_field_mismatch"


def _signature(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _case_distribution(cases: list[dict[str, Any]]) -> dict[str, Any]:
    language_counts: Counter[str] = Counter()
    intent_counts: Counter[str] = Counter()
    operation_signatures: Counter[str] = Counter()
    response_length_counts: Counter[str] = Counter()
    constraint_must_counts: Counter[str] = Counter()
    constraint_must_not_counts: Counter[str] = Counter()
    constraint_format_counts: Counter[str] = Counter()
    risk_level_counts: Counter[str] = Counter()
    risk_flag_counts: Counter[str] = Counter()
    critical_positive_counts: Counter[str] = Counter()
    source_group_counts: Counter[str] = Counter()
    contrast_group_counts: Counter[str] = Counter()
    text_lengths = []
    synthetic_prefix = 0
    terminal_phrase = 0
    main_issue_phrase = 0
    boundary_phrase = 0
    ask_before_phrase = 0
    japanese_like = 0

    for case in cases:
        text = case["input"]
        expected = case["expected"]
        language_counts[case.get("language", "und")] += 1
        source_group_counts[case.get("source_group", "")] += 1
        contrast_group_counts[str(case.get("contrast_group"))] += 1
        intent_counts[expected["primary_intent"]] += 1
        operation_signatures[_signature(expected["operations"])] += 1
        constraints = expected["constraints"]
        response_length_counts[constraints["response_length"]] += 1
        constraint_must_counts.update(constraints["must"])
        constraint_must_not_counts.update(constraints["must_not"])
        constraint_format_counts.update(constraints["formats"])
        risk = expected["risk"]
        risk_level_counts[risk["level"]] += 1
        risk_flag_counts.update(risk["flags"])
        information = expected["information_state"]
        for signal in CRITICAL_SIGNALS:
            if information[signal]:
                critical_positive_counts[signal] += 1
        text_lengths.append(len(text))
        lower = text.lower()
        synthetic_prefix += text.startswith("Bridge rewrite case")
        terminal_phrase += "keep the terminal operation" in lower
        main_issue_phrase += "the main issue is" in lower
        boundary_phrase += "boundary" in lower
        ask_before_phrase += "ask before" in lower or "ask me" in lower
        japanese_like += any("\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff" for char in text)

    count = len(cases)
    return {
        "case_count": count,
        "language_counts": dict(sorted(language_counts.items())),
        "intent_counts": dict(sorted(intent_counts.items())),
        "operation_signature_counts": dict(sorted(operation_signatures.items())),
        "response_length_counts": dict(sorted(response_length_counts.items())),
        "constraint_must_counts": dict(sorted(constraint_must_counts.items())),
        "constraint_must_not_counts": dict(sorted(constraint_must_not_counts.items())),
        "constraint_format_counts": dict(sorted(constraint_format_counts.items())),
        "risk_level_counts": dict(sorted(risk_level_counts.items())),
        "risk_flag_counts": dict(sorted(risk_flag_counts.items())),
        "critical_positive_counts": dict(sorted(critical_positive_counts.items())),
        "source_group_counts": dict(sorted(source_group_counts.items())),
        "contrast_group_counts": dict(sorted(contrast_group_counts.items())),
        "style_markers": {
            "synthetic_bridge_prefix_rate": round(synthetic_prefix / count, 6) if count else 0.0,
            "terminal_operation_phrase_rate": round(terminal_phrase / count, 6) if count else 0.0,
            "main_issue_phrase_rate": round(main_issue_phrase / count, 6) if count else 0.0,
            "boundary_word_rate": round(boundary_phrase / count, 6) if count else 0.0,
            "ask_before_phrase_rate": round(ask_before_phrase / count, 6) if count else 0.0,
            "japanese_script_rate": round(japanese_like / count, 6) if count else 0.0,
            "average_char_length": round(sum(text_lengths) / count, 3) if count else 0.0,
        },
    }


def _distribution_gap(bridge: dict[str, Any], sealed: dict[str, Any]) -> dict[str, Any]:
    bridge_style = bridge["style_markers"]
    sealed_style = sealed["style_markers"]
    style_delta = {
        key: round(sealed_style[key] - bridge_style[key], 6)
        for key in bridge_style
        if isinstance(bridge_style[key], (int, float))
    }
    return {
        "style_marker_delta_sealed_minus_bridge": style_delta,
        "bridge_template_overfit_risk": (
            bridge_style["synthetic_bridge_prefix_rate"] == 1.0
            and sealed_style["synthetic_bridge_prefix_rate"] == 0.0
        ),
        "language_shift": {
            "bridge": bridge["language_counts"],
            "sealed_v10": sealed["language_counts"],
        },
        "critical_signal_support_shift": {
            "bridge": bridge["critical_positive_counts"],
            "sealed_v10": sealed["critical_positive_counts"],
        },
        "constraint_must_shift": {
            "bridge": bridge["constraint_must_counts"],
            "sealed_v10": sealed["constraint_must_counts"],
        },
    }


def build_payload() -> dict[str, Any]:
    measurement = _load_json(MEASUREMENT_PATH)
    fixture = parse_plm_sealed_fixture(_load_json(SEALED_V10_PATH))
    bridge_payload = _load_json(BRIDGE_PATH)
    errors_by_id = {error["id"]: error for error in measurement["measurements"]["errors"]}

    case_diagnostics = []
    mode_counts: Counter[str] = Counter()
    mode_field_counts: dict[str, Counter[str]] = defaultdict(Counter)
    field_value_counts: dict[str, Counter[str]] = defaultdict(Counter)
    critical_misses: Counter[str] = Counter()
    intent_transitions: Counter[str] = Counter()

    for case in fixture.cases:
        expected = _expected_core(case)
        packet = route(case.input_text).packet
        predicted = _packet_core(packet)
        diff = _diff_values(expected, predicted)
        fields = _field_set(diff)
        if not diff:
            continue
        mode = _mode(expected, predicted)
        mode_counts[mode] += 1
        mode_field_counts[mode].update(fields)
        if "primary_intent" in diff:
            intent_transitions[f"{expected['primary_intent']}->{predicted['primary_intent']}"] += 1
        for field, value in diff.items():
            if isinstance(value, dict) and "expected" in value:
                field_value_counts[field][f"{value['expected']} -> {value['predicted']}"] += 1
            elif isinstance(value, dict):
                for key, subvalue in value.items():
                    field_value_counts[f"{field}.{key}"][f"{subvalue['expected']} -> {subvalue['predicted']}"] += 1
        for signal in CRITICAL_SIGNALS:
            if expected["information_state"][signal] and not predicted["information_state"][signal]:
                critical_misses[signal] += 1
        case_diagnostics.append(
            {
                "id": case.case_id,
                "input": case.input_text,
                "mode": mode,
                "measurement_error_fields": errors_by_id.get(case.case_id, {}).get("fields", fields),
                "expected_intent": expected["primary_intent"],
                "predicted_intent": predicted["primary_intent"],
                "value_diff": diff,
                "trace": route(case.input_text).trace,
            }
        )

    bridge_distribution = _case_distribution(bridge_payload["cases"])
    sealed_distribution = _case_distribution([case.as_dict() for case in fixture.cases])
    metrics = measurement["measurements"]
    v9 = _load_json(ROOT / "build" / "pattern_language_sealed_v9_measurement_report.json")["measurements"]
    metric_regression = {
        name: {
            "v9": v9[name],
            "v10": metrics[name],
            "delta_v10_minus_v9": round(metrics[name] - v9[name], 6),
        }
        for name in (
            "intent_accuracy",
            "critical_signal_recall",
            "operation_exact_match",
            "constraint_exact_match",
            "risk_exact_match",
        )
    }

    focus_areas = [
        {
            "id": "value_level_diff_instrumentation",
            "priority": 1,
            "finding": "field-level errors hide whether failures are value vocabulary drift or routing logic defects",
            "evidence": {"diagnosed_case_count": len(case_diagnostics)},
            "v11_action": "make value_diff mandatory in post-sealed taxonomy reports",
        },
        {
            "id": "clarify_boundary_collapse",
            "priority": 1,
            "finding": "clarify recall collapsed and clarify cases dispersed across respond, verify, and explore",
            "evidence": {
                "clarify_recall": metrics["per_intent"]["clarify"]["recall"],
                "intent_transitions": dict(sorted(intent_transitions.items())),
            },
            "v11_action": "create independent clarify boundary diagnostic and nonsealed repair lane before fresh rotation",
        },
        {
            "id": "multiple_intent_under_detection",
            "priority": 1,
            "finding": "multiple_intents is the largest critical-signal miss after v10",
            "evidence": {
                "critical_misses": dict(sorted(critical_misses.items())),
                "multiple_intents_recall": metrics["critical_signals"]["multiple_intents"]["recall"],
                "multiple_intents_support": metrics["critical_signals"]["multiple_intents"]["support"],
            },
            "v11_action": "treat multiple intent detection as its own target, not a generic information_state item",
        },
        {
            "id": "bridge_non_transfer",
            "priority": 1,
            "finding": "isolated bridge replay was exact, but sealed v10 regressed on all five metrics",
            "evidence": {
                "metric_regression": metric_regression,
                "distribution_gap": _distribution_gap(bridge_distribution, sealed_distribution),
            },
            "v11_action": "block another bridge-only cycle until template/style distribution gap is explicitly tested",
        },
        {
            "id": "intent_correct_field_mismatch_lane",
            "priority": 2,
            "finding": "cases with correct primary intent still miss constraints/risk/operations and need a separate exactness lane",
            "evidence": {
                "mode_counts": dict(sorted(mode_counts.items())),
                "mode_field_counts": {mode: dict(sorted(counter.items())) for mode, counter in sorted(mode_field_counts.items())},
            },
            "v11_action": "separate field-exactness repair from intent-boundary repair",
        },
    ]

    return {
        "schema_version": "v11-post-v10-measurement-diagnostic.v1",
        "generated_at": reproducible_now_iso(),
        "status": "diagnostic_completed_v11_step1_ready",
        "sources": {
            "sealed_v10_measurement": _rel(MEASUREMENT_PATH),
            "sealed_v10_fixture_consumed": _rel(SEALED_V10_PATH),
            "v10_bridge_isolated_benchmark": _rel(BRIDGE_PATH),
        },
        "policy": {
            "sealed_v10_status": "consumed",
            "sealed_v10_labels_used_for_tuning": False,
            "sealed_v10_values_used_for_taxonomy_only": True,
            "diagnostic_is_training_data": False,
            "diagnostic_is_replay_gate": False,
            "same_cycle_promotion_allowed": False,
            "fresh_sealed_v11_required_before_next_adjudication": True,
        },
        "metric_regression": metric_regression,
        "failure_mode_summary": {
            "mode_counts": dict(sorted(mode_counts.items())),
            "mode_field_counts": {mode: dict(sorted(counter.items())) for mode, counter in sorted(mode_field_counts.items())},
            "intent_transitions": dict(sorted(intent_transitions.items())),
            "critical_signal_misses": dict(sorted(critical_misses.items())),
            "field_value_diff_counts": {field: dict(sorted(counter.items())) for field, counter in sorted(field_value_counts.items())},
        },
        "bridge_transfer_diagnostic": {
            "bridge_distribution": bridge_distribution,
            "sealed_v10_distribution": sealed_distribution,
            "distribution_gap": _distribution_gap(bridge_distribution, sealed_distribution),
        },
        "case_diagnostics": case_diagnostics,
        "focus_areas": focus_areas,
        "next_action": "roadmap_v11_step1_build_taxonomy_from_value_diff_and_transfer_gap",
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# V11 Post-V10 Measurement Diagnostic v1",
        "",
        "This diagnostic inspects consumed sealed v10 only as post-measurement taxonomy. It is not training data and is not a replay gate.",
        "",
        "## Metric Regression",
        "",
        "| Metric | V9 | V10 | Delta |",
        "|---|---:|---:|---:|",
    ]
    for name, item in payload["metric_regression"].items():
        lines.append(f"| {name} | {item['v9']:.6f} | {item['v10']:.6f} | {item['delta_v10_minus_v9']:.6f} |")
    summary = payload["failure_mode_summary"]
    lines.extend(
        [
            "",
            "## Failure Modes",
            "",
            f"- mode_counts: `{summary['mode_counts']}`",
            f"- critical_signal_misses: `{summary['critical_signal_misses']}`",
            f"- intent_transitions: `{summary['intent_transitions']}`",
            "",
            "## Bridge Transfer Gap",
            "",
        ]
    )
    gap = payload["bridge_transfer_diagnostic"]["distribution_gap"]
    lines.append(f"- bridge_template_overfit_risk: `{gap['bridge_template_overfit_risk']}`")
    lines.append(f"- language_shift: `{gap['language_shift']}`")
    lines.append(f"- style_marker_delta_sealed_minus_bridge: `{gap['style_marker_delta_sealed_minus_bridge']}`")
    lines.extend(["", "## V11 Focus Areas", ""])
    for item in payload["focus_areas"]:
        lines.append(f"{item['priority']}. {item['id']}: {item['finding']}")
    lines.extend(["", "## Decision", "", f"- next_action: `{payload['next_action']}`"])
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(payload)
    print(json.dumps({"status": payload["status"], "output": _rel(OUTPUT_JSON), "case_diagnostic_count": len(payload["case_diagnostics"]), "next_action": payload["next_action"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
