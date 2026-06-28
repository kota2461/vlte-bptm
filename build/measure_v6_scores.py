"""Measure V6 score lanes after boundary false-positive adoption.

This report measures current route() on non-sealed lanes and reads existing
sealed reports only. It does not open any sealed fixture or act as a promotion
gate.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, load_plm_benchmark, parse_plm_benchmark, route  # noqa: E402

VISIBLE_PLM_PATH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
V6_BOUNDARY_FP_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_adopted_benchmark_v1.json"
V6_BOUNDARY_PRIORITY_REVIEW_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_priority_review_adopted_benchmark_v1.json"
V6_STRUCTURAL_BUILD_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_structural_build_30_adopted_benchmark_v1.json"
V6_BOUNDARY_FP_CANDIDATE_PATH = ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_candidate_benchmark_v1.json"
V6_CONTRAST_NEGATIVE_PATH = ROOT / "tests" / "fixtures" / "v6_contrast_negative_benchmark_v1.json"
V6_ROUTER_DEBATE_ADOPTED_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json"
V6_ROUTER_DEBATE_CANDIDATE_PATH = ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json"
V6_BOUNDARY_SELECTION_PATH = ROOT / "build" / "v6_boundary_debate_log_selection_v1.json"
SEALED_V5_REPORT_PATH = ROOT / "build" / "pattern_language_sealed_v5_measurement_report.json"
REPORT_PATH = ROOT / "build" / "v6_score_report_v1.json"
SUMMARY_PATH = ROOT / "build" / "v6_score_summary_v1.md"

WEIGHTS = {
    "intent_accuracy": 0.25,
    "critical_signal_recall": 0.20,
    "operation_exact_match": 0.20,
    "constraint_exact_match": 0.15,
    "risk_exact_match": 0.15,
    "valid_packet_rate": 0.05,
}
PLM_METRICS = tuple(WEIGHTS)
CRITICAL_SIGNALS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def critical_support(cases: Sequence[Any]) -> dict[str, int]:
    support = Counter()
    for case in cases:
        expected = case.expected
        if expected.missing_required_information:
            support["missing_required_information"] += 1
        if expected.contains_unverified_claims:
            support["contains_unverified_claims"] += 1
        if expected.requires_current_information:
            support["requires_current_information"] += 1
        if expected.multiple_intents:
            support["multiple_intents"] += 1
    return {signal: support.get(signal, 0) for signal in CRITICAL_SIGNALS}


def compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    error_fields = Counter(field for error in measurement["errors"] for field in error.get("fields", []))
    return {
        "case_count": measurement["case_count"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "error_count": len(measurement["errors"]),
        "error_field_counts": dict(sorted(error_fields.items())),
    }


def raw_score(compact: dict[str, Any]) -> float:
    return round(sum(compact[key] * weight for key, weight in WEIGHTS.items()), 6)


def observable_score(compact: dict[str, Any], support: dict[str, int]) -> float:
    active_weights = dict(WEIGHTS)
    if sum(support.values()) == 0:
        active_weights.pop("critical_signal_recall")
    denominator = sum(active_weights.values())
    return round(sum(compact[key] * weight for key, weight in active_weights.items()) / denominator, 6)


def lane_payload(
    *,
    source: Path,
    review_status: str,
    evaluated_splits: list[str],
    cases: Sequence[Any],
    measurement: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    compact = compact_measurement(measurement)
    support = critical_support(cases)
    payload = {
        "source": rel(source),
        "review_status": review_status,
        "evaluated_splits": evaluated_splits,
        "measurement": compact,
        "critical_signal_support": support,
        "score": observable_score(compact, support),
        "raw_score": raw_score(compact),
        "score_note": (
            "critical_signal_recall excluded from score because this lane has no expected critical signals"
            if sum(support.values()) == 0
            else "all weighted metrics included"
        ),
        "passed_exact": compact["valid_packet_rate"] == 1.0 and compact["error_count"] == 0,
        "errors": measurement["errors"],
    }
    if extra:
        payload.update(extra)
    return payload


def measure_benchmark(path: Path, *, splits: tuple[str, ...] | None = None) -> dict[str, Any]:
    payload = load_json(path)
    benchmark = parse_plm_benchmark(payload)
    cases = benchmark.cases_for_splits(splits) if splits else benchmark.cases
    measurement = evaluate_plm_extractor(cases, lambda text: route(text).packet)
    return lane_payload(
        source=path,
        review_status=payload["review_status"],
        evaluated_splits=list(splits) if splits else sorted({case.split for case in benchmark.cases}),
        cases=cases,
        measurement=measurement,
    )


def measure_visible_plm() -> dict[str, Any]:
    benchmark = load_plm_benchmark(VISIBLE_PLM_PATH)
    cases = benchmark.cases_for_splits(("train", "validation"))
    measurement = evaluate_plm_extractor(cases, lambda text: route(text).packet)
    return lane_payload(
        source=VISIBLE_PLM_PATH,
        review_status=benchmark.review_status,
        evaluated_splits=["train", "validation"],
        cases=cases,
        measurement=measurement,
        extra={"sealed_split_evaluated": False},
    )


def sealed_v5_existing() -> dict[str, Any]:
    if not SEALED_V5_REPORT_PATH.exists():
        return {
            "source": rel(SEALED_V5_REPORT_PATH),
            "available": False,
            "note": "existing sealed v5 measurement report not found; no sealed fixture opened",
        }
    report = load_json(SEALED_V5_REPORT_PATH)
    measurement = report.get("measurements", report.get("measurement", {}))
    compact = {
        "case_count": measurement.get("case_count"),
        "intent_accuracy": measurement.get("intent_accuracy"),
        "critical_signal_recall": measurement.get("critical_signal_recall"),
        "operation_exact_match": measurement.get("operation_exact_match"),
        "constraint_exact_match": measurement.get("constraint_exact_match"),
        "risk_exact_match": measurement.get("risk_exact_match"),
        "valid_packet_rate": measurement.get("valid_packet_rate"),
        "error_count": len(measurement.get("errors", [])),
    }
    support = {
        signal: details.get("support", 0)
        for signal, details in measurement.get("critical_signals", {}).items()
    }
    for signal in CRITICAL_SIGNALS:
        support.setdefault(signal, 0)
    score = observable_score(compact, support) if all(compact[key] is not None for key in PLM_METRICS) else None
    raw = raw_score(compact) if all(compact[key] is not None for key in PLM_METRICS) else None
    return {
        "source": rel(SEALED_V5_REPORT_PATH),
        "available": True,
        "read_only_existing_report": True,
        "sealed_fixture_opened_now": False,
        "status": report.get("status", report.get("schema_version")),
        "measurement": compact,
        "critical_signal_support": support,
        "score": score,
        "raw_score": raw,
    }


def build_report() -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    lanes = {
        "visible_plm_train_validation": measure_visible_plm(),
        "v6_boundary_false_positive_adopted": measure_benchmark(V6_BOUNDARY_FP_ADOPTED_PATH),
        "v6_boundary_priority_review_adopted": measure_benchmark(V6_BOUNDARY_PRIORITY_REVIEW_ADOPTED_PATH),
        "v6_structural_build_30_adopted": measure_benchmark(V6_STRUCTURAL_BUILD_ADOPTED_PATH),
        "v6_boundary_false_positive_candidate": measure_benchmark(V6_BOUNDARY_FP_CANDIDATE_PATH),
        "v6_contrast_negative": measure_benchmark(V6_CONTRAST_NEGATIVE_PATH),
        "v6_router_debate_adopted": measure_benchmark(V6_ROUTER_DEBATE_ADOPTED_PATH),
        "v6_router_debate_candidate": measure_benchmark(V6_ROUTER_DEBATE_CANDIDATE_PATH),
    }
    selection = load_json(V6_BOUNDARY_SELECTION_PATH) if V6_BOUNDARY_SELECTION_PATH.exists() else None
    sealed_v5 = sealed_v5_existing()
    exact_lanes = [name for name, lane in lanes.items() if lane["passed_exact"]]
    gap_lanes = [name for name, lane in lanes.items() if not lane["passed_exact"]]
    average_score = round(sum(lane["score"] for lane in lanes.values()) / len(lanes), 6)
    average_raw_score = round(sum(lane["raw_score"] for lane in lanes.values()) / len(lanes), 6)
    report = {
        "schema_version": "v6-score-report.v1",
        "generated_at": generated_at,
        "status": "completed",
        "policy": {
            "sealed_fixture_opened_now": False,
            "sealed_measurement_used_for_tuning": False,
            "nonsealed_current_route_measurement_is_gate": False,
            "same_cycle_promotion_allowed": False,
        },
        "score_formula": {
            "raw_score": WEIGHTS,
            "score": "weighted score over observable metrics; critical_signal_recall is excluded when a lane has zero expected critical-signal support",
        },
        "summary": {
            "lane_count": len(lanes),
            "exact_lane_count": len(exact_lanes),
            "gap_lane_count": len(gap_lanes),
            "exact_lanes": exact_lanes,
            "gap_lanes": gap_lanes,
            "average_nonsealed_score": average_score,
            "average_nonsealed_raw_score": average_raw_score,
            "boundary_false_positive_adopted_score": lanes["v6_boundary_false_positive_adopted"]["score"],
            "boundary_false_positive_adopted_raw_score": lanes["v6_boundary_false_positive_adopted"]["raw_score"],
            "boundary_false_positive_adopted_errors": lanes["v6_boundary_false_positive_adopted"]["measurement"]["error_count"],
            "boundary_priority_review_adopted_score": lanes["v6_boundary_priority_review_adopted"]["score"],
            "boundary_priority_review_adopted_raw_score": lanes["v6_boundary_priority_review_adopted"]["raw_score"],
            "boundary_priority_review_adopted_errors": lanes["v6_boundary_priority_review_adopted"]["measurement"]["error_count"],
            "structural_build_30_adopted_score": lanes["v6_structural_build_30_adopted"]["score"],
            "structural_build_30_adopted_raw_score": lanes["v6_structural_build_30_adopted"]["raw_score"],
            "structural_build_30_adopted_errors": lanes["v6_structural_build_30_adopted"]["measurement"]["error_count"],
            "selection_summary": selection.get("summary") if selection else None,
        },
        "lanes": lanes,
        "sealed_v5_existing_report": sealed_v5,
    }
    return report


def write_summary(report: dict[str, Any]) -> None:
    lines = [
        "# V6 Score Summary v1",
        "",
        "This is a non-sealed current route score report. It does not open sealed fixtures and is not a promotion gate.",
        "",
        "## Summary",
        "",
        f"- lane_count: {report['summary']['lane_count']}",
        f"- exact_lane_count: {report['summary']['exact_lane_count']}",
        f"- gap_lane_count: {report['summary']['gap_lane_count']}",
        f"- average_nonsealed_score: {report['summary']['average_nonsealed_score']:.3f}",
        f"- average_nonsealed_raw_score: {report['summary']['average_nonsealed_raw_score']:.3f}",
        f"- boundary_false_positive_adopted_score: {report['summary']['boundary_false_positive_adopted_score']:.3f}",
        f"- boundary_false_positive_adopted_raw_score: {report['summary']['boundary_false_positive_adopted_raw_score']:.3f}",
        f"- boundary_false_positive_adopted_errors: {report['summary']['boundary_false_positive_adopted_errors']}",
        f"- boundary_priority_review_adopted_score: {report['summary']['boundary_priority_review_adopted_score']:.3f}",
        f"- boundary_priority_review_adopted_raw_score: {report['summary']['boundary_priority_review_adopted_raw_score']:.3f}",
        f"- boundary_priority_review_adopted_errors: {report['summary']['boundary_priority_review_adopted_errors']}",
        f"- structural_build_30_adopted_score: {report['summary']['structural_build_30_adopted_score']:.3f}",
        f"- structural_build_30_adopted_raw_score: {report['summary']['structural_build_30_adopted_raw_score']:.3f}",
        f"- structural_build_30_adopted_errors: {report['summary']['structural_build_30_adopted_errors']}",
        "",
        "## Lanes",
        "",
        "| lane | cases | score | raw | errors | intent | critical | operation | constraint | risk |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, lane in report["lanes"].items():
        m = lane["measurement"]
        lines.append(
            "| "
            f"{name} | {m['case_count']} | {lane['score']:.3f} | {lane['raw_score']:.3f} | {m['error_count']} | "
            f"{m['intent_accuracy']:.3f} | {m['critical_signal_recall']:.3f} | "
            f"{m['operation_exact_match']:.3f} | {m['constraint_exact_match']:.3f} | "
            f"{m['risk_exact_match']:.3f} |"
        )
    sealed = report["sealed_v5_existing_report"]
    lines.extend(["", "## Sealed V5 Existing Report", ""])
    if sealed.get("available"):
        m = sealed["measurement"]
        lines.append(
            f"Read-only existing report `{sealed['source']}`: status `{sealed.get('status')}`, "
            f"score {sealed.get('score')}, raw {sealed.get('raw_score')}, errors {m.get('error_count')}."
        )
    else:
        lines.append("No existing sealed v5 report was read; no sealed fixture was opened.")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    report = build_report()
    write_json(REPORT_PATH, report)
    write_summary(report)
    print(json.dumps({
        "status": report["status"],
        "summary": report["summary"],
        "score_report": rel(REPORT_PATH),
        "score_summary": rel(SUMMARY_PATH),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
