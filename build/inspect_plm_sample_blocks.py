"""Inspect non-sealed PLM sample blocks for strong negative signals.

This is diagnostic only. It does not mutate fixtures, training data, router
rules, or sealed measurement state. Sealed fixtures are intentionally excluded.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import extract_semantic_packet, load_plm_benchmark  # noqa: E402

OUTPUT_JSON = ROOT / "build" / "plm_sample_block_negative_scan_v1.json"
OUTPUT_MD = ROOT / "build" / "plm_sample_block_negative_scan_v1.md"
FIXTURE_ROOT = ROOT / "tests" / "fixtures"

CRITICAL_SIGNALS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)
SYNTHETIC_PREFIXES = (
    "Answer the practical request",
    "Explain the concept at a general level",
    "Ask the missing-context question",
    "Draft the requested artifact",
    "Check the claim or plan",
    "Summarize the decisions",
    "Compare the trade-offs",
)

FIELD_WEIGHTS = {
    "primary_intent": 3.0,
    "information_state": 1.5,
    "operations": 1.4,
    "constraints": 1.2,
    "risk": 1.3,
}


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _fixture_paths() -> list[Path]:
    paths = []
    for path in sorted(FIXTURE_ROOT.glob("*.json")):
        name = path.name
        if name.startswith("pattern_language_sealed_"):
            continue
        if name in {"sealed_boundary_slice_v1.json", "sealed_boundary_slice_v2.json"}:
            continue
        paths.append(path)
    return paths


def _load_nonsealed_plm_fixtures() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    fixtures: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for path in _fixture_paths():
        try:
            benchmark = load_plm_benchmark(path)
        except Exception as error:
            skipped.append({"path": _rel(path), "reason": str(error).splitlines()[0]})
            continue
        if any(case.split == "sealed" for case in benchmark.cases):
            skipped.append({"path": _rel(path), "reason": "contains sealed split"})
            continue
        fixtures.append({"path": path, "benchmark": benchmark})
    return fixtures, skipped


def _id_prefix(case_id: str) -> str:
    value = re.sub(r"[-_]?\d+$", "", case_id)
    value = re.sub(r"[-_](?:en|ja)$", "", value, flags=re.I)
    return value or case_id


def _is_synthetic_bridge(text: str) -> bool:
    return any(text.startswith(prefix) for prefix in SYNTHETIC_PREFIXES)


def _expected_dict(case: Any) -> dict[str, Any]:
    return case.expected.as_dict()


def _packet_dict(text: str) -> dict[str, Any]:
    payload = extract_semantic_packet(text).as_dict()
    return {
        "primary_intent": payload["intent_candidates"][0]["intent"],
        "operations": payload["operations"],
        "information_state": payload["information_state"],
        "constraints": payload["constraints"],
        "risk": payload["risk"],
        "evidence": payload["evidence"],
        "unknowns": payload["unknowns"],
        "conflicts": payload["conflicts"],
    }


def _risk_rank(level: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(level, 0)


def _case_diagnostic(fixture_path: Path, case: Any) -> dict[str, Any]:
    expected = _expected_dict(case)
    predicted = _packet_dict(case.input_text)
    fields: list[str] = []
    value_diff: dict[str, Any] = {}

    if predicted["primary_intent"] != expected["primary_intent"]:
        fields.append("primary_intent")
        value_diff["primary_intent"] = f"{expected['primary_intent']} -> {predicted['primary_intent']}"

    expected_state = expected["information_state"]
    predicted_state = predicted["information_state"]
    critical_misses = []
    critical_false_positives = []
    for signal in CRITICAL_SIGNALS:
        if expected_state[signal] and not predicted_state[signal]:
            critical_misses.append(signal)
        if not expected_state[signal] and predicted_state[signal]:
            critical_false_positives.append(signal)
    if expected_state != predicted_state:
        fields.append("information_state")
        value_diff["information_state"] = {
            signal: f"{expected_state[signal]} -> {predicted_state[signal]}"
            for signal in CRITICAL_SIGNALS
            if expected_state[signal] != predicted_state[signal]
        }

    expected_constraints = expected["constraints"]
    predicted_constraints = predicted["constraints"]
    constraint_omissions = []
    if expected_constraints != predicted_constraints:
        fields.append("constraints")
        if expected_constraints["must"] and not predicted_constraints["must"]:
            constraint_omissions.append("constraints.must")
        if expected_constraints["formats"] and not predicted_constraints["formats"]:
            constraint_omissions.append("constraints.formats")
        if (
            expected_constraints["response_length"] != "unspecified"
            and predicted_constraints["response_length"] == "unspecified"
        ):
            constraint_omissions.append("constraints.response_length")
        value_diff["constraints"] = {
            "expected": expected_constraints,
            "predicted": predicted_constraints,
        }

    if predicted["operations"] != expected["operations"]:
        fields.append("operations")
        value_diff["operations"] = {
            "expected": expected["operations"],
            "predicted": predicted["operations"],
        }

    expected_risk = expected["risk"]
    predicted_risk = predicted["risk"]
    risk_overfire = False
    risk_underfire = False
    if expected_risk != predicted_risk:
        fields.append("risk")
        risk_overfire = _risk_rank(predicted_risk["level"]) > _risk_rank(expected_risk["level"])
        risk_underfire = _risk_rank(predicted_risk["level"]) < _risk_rank(expected_risk["level"])
        if not expected_risk["flags"] and predicted_risk["flags"]:
            risk_overfire = True
        value_diff["risk"] = {"expected": expected_risk, "predicted": predicted_risk}

    weighted_score = round(sum(FIELD_WEIGHTS[field] for field in set(fields)), 3)
    if critical_misses:
        weighted_score += 1.2 * len(critical_misses)
    if critical_false_positives:
        weighted_score += 0.6 * len(critical_false_positives)
    if constraint_omissions:
        weighted_score += 0.5 * len(constraint_omissions)
    if risk_overfire:
        weighted_score += 0.7
    weighted_score = round(weighted_score, 3)

    return {
        "id": case.case_id,
        "fixture": _rel(fixture_path),
        "split": case.split,
        "source_group": case.source_group,
        "contrast_group": case.contrast_group,
        "id_prefix": _id_prefix(case.case_id),
        "language": case.language,
        "input_length": len(case.input_text),
        "synthetic_bridge_prefix": _is_synthetic_bridge(case.input_text),
        "mismatch_fields": fields,
        "weighted_negative_score": weighted_score,
        "critical_misses": critical_misses,
        "critical_false_positives": critical_false_positives,
        "constraint_omissions": constraint_omissions,
        "risk_overfire": risk_overfire,
        "risk_underfire": risk_underfire,
        "value_diff": value_diff,
    }


def _new_group(kind: str, key: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "key": key,
        "case_count": 0,
        "error_count": 0,
        "weighted_negative_score_sum": 0.0,
        "mismatch_field_counts": Counter(),
        "critical_miss_counts": Counter(),
        "critical_false_positive_counts": Counter(),
        "constraint_omission_counts": Counter(),
        "risk_overfire_count": 0,
        "risk_underfire_count": 0,
        "synthetic_bridge_prefix_count": 0,
        "language_counts": Counter(),
        "case_ids": [],
        "top_error_cases": [],
    }


def _add_case(group: dict[str, Any], case: dict[str, Any]) -> None:
    group["case_count"] += 1
    group["weighted_negative_score_sum"] += case["weighted_negative_score"]
    group["language_counts"][case["language"]] += 1
    group["case_ids"].append(case["id"])
    if case["synthetic_bridge_prefix"]:
        group["synthetic_bridge_prefix_count"] += 1
    if case["mismatch_fields"]:
        group["error_count"] += 1
        group["top_error_cases"].append(
            {
                "id": case["id"],
                "score": case["weighted_negative_score"],
                "fields": case["mismatch_fields"],
                "critical_misses": case["critical_misses"],
                "critical_false_positives": case["critical_false_positives"],
                "constraint_omissions": case["constraint_omissions"],
                "risk_overfire": case["risk_overfire"],
            }
        )
    group["mismatch_field_counts"].update(case["mismatch_fields"])
    group["critical_miss_counts"].update(case["critical_misses"])
    group["critical_false_positive_counts"].update(case["critical_false_positives"])
    group["constraint_omission_counts"].update(case["constraint_omissions"])
    group["risk_overfire_count"] += int(case["risk_overfire"])
    group["risk_underfire_count"] += int(case["risk_underfire"])


def _ratio(n: int | float, d: int) -> float:
    return round(float(n) / d, 6) if d else 0.0


def _finalize_group(group: dict[str, Any]) -> dict[str, Any]:
    case_count = group["case_count"]
    error_count = group["error_count"]
    synthetic_count = group["synthetic_bridge_prefix_count"]
    avg_score = _ratio(group["weighted_negative_score_sum"], case_count)
    top_error_cases = sorted(
        group["top_error_cases"],
        key=lambda item: (-item["score"], item["id"]),
    )[:8]
    risk_flags = []
    if error_count and case_count >= 3 and _ratio(error_count, case_count) >= 0.5:
        risk_flags.append("high_error_rate")
    if error_count and case_count <= 2 and _ratio(error_count, case_count) == 1.0 and avg_score >= 2.0:
        risk_flags.append("small_block_all_failed")
    if avg_score >= 2.0:
        risk_flags.append("high_weighted_negative_score")
    if _ratio(group["risk_overfire_count"], case_count) >= 0.3 and group["risk_overfire_count"]:
        risk_flags.append("risk_overfire_cluster")
    if _ratio(sum(group["constraint_omission_counts"].values()), case_count) >= 0.3 and group["constraint_omission_counts"]:
        risk_flags.append("constraint_omission_cluster")
    if synthetic_count == case_count and case_count >= 10:
        risk_flags.append("template_transfer_risk")
    if group["language_counts"].get("en", 0) == case_count and case_count >= 20:
        risk_flags.append("english_only_large_block")

    if any(flag in risk_flags for flag in ("high_error_rate", "high_weighted_negative_score", "small_block_all_failed")):
        severity = "strong_negative_candidate"
    elif any(flag in risk_flags for flag in ("risk_overfire_cluster", "constraint_omission_cluster")):
        severity = "focused_repair_candidate"
    elif any(flag in risk_flags for flag in ("template_transfer_risk", "english_only_large_block")):
        severity = "transfer_risk_candidate"
    else:
        severity = "ok_or_low_signal"

    return {
        "kind": group["kind"],
        "key": group["key"],
        "case_count": case_count,
        "error_count": error_count,
        "error_rate": _ratio(error_count, case_count),
        "weighted_negative_score_avg": avg_score,
        "mismatch_field_counts": dict(sorted(group["mismatch_field_counts"].items())),
        "critical_miss_counts": dict(sorted(group["critical_miss_counts"].items())),
        "critical_false_positive_counts": dict(sorted(group["critical_false_positive_counts"].items())),
        "constraint_omission_counts": dict(sorted(group["constraint_omission_counts"].items())),
        "risk_overfire_count": group["risk_overfire_count"],
        "risk_underfire_count": group["risk_underfire_count"],
        "synthetic_bridge_prefix_rate": _ratio(synthetic_count, case_count),
        "language_counts": dict(sorted(group["language_counts"].items())),
        "risk_flags": risk_flags,
        "severity": severity,
        "case_ids": group["case_ids"],
        "top_error_cases": top_error_cases,
    }


def _summarize_groups(cases: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for case in cases:
        keys = [
            ("fixture", case["fixture"]),
            ("source_group", f"{case['fixture']}::{case['source_group']}"),
            ("id_prefix", f"{case['fixture']}::{case['id_prefix']}"),
        ]
        if case["contrast_group"]:
            keys.append(("contrast_group", f"{case['fixture']}::{case['contrast_group']}"))
        for kind, key in keys:
            groups.setdefault((kind, key), _new_group(kind, key))
            _add_case(groups[(kind, key)], case)
    finalized = [_finalize_group(group) for group in groups.values()]
    return sorted(
        finalized,
        key=lambda item: (
            item["severity"] != "strong_negative_candidate",
            item["severity"] != "focused_repair_candidate",
            item["severity"] != "transfer_risk_candidate",
            -item["weighted_negative_score_avg"],
            -item["error_rate"],
            item["kind"],
            item["key"],
        ),
    )


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# PLM Sample Block Negative Scan v1",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Policy",
        "",
        "- Diagnostic only; no training data, fixture, or router mutation.",
        "- Sealed fixtures are excluded and active sealed fixtures are not opened.",
        "- Strong negative means current-route mismatch concentration or high weighted error, not automatic deletion.",
        "",
        "## Summary",
        "",
        f"- fixtures_scanned: {report['summary']['fixtures_scanned']}",
        f"- cases_scanned: {report['summary']['cases_scanned']}",
        f"- strong_negative_blocks: {report['summary']['strong_negative_blocks']}",
        f"- focused_repair_blocks: {report['summary']['focused_repair_blocks']}",
        f"- transfer_risk_blocks: {report['summary']['transfer_risk_blocks']}",
        "",
        "## Strong Negative Candidates",
        "",
        "| kind | key | cases | errors | score | flags | top errors |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for item in report["ranked_blocks"]:
        if item["severity"] != "strong_negative_candidate":
            continue
        top = ", ".join(case["id"] for case in item["top_error_cases"][:4])
        lines.append(
            f"| {item['kind']} | `{item['key']}` | {item['case_count']} | {item['error_count']} "
            f"| {item['weighted_negative_score_avg']:.3f} | {', '.join(item['risk_flags'])} | {top} |"
        )
    lines.extend([
        "",
        "## Focused Repair Candidates",
        "",
        "| kind | key | cases | errors | score | flags | field counts |",
        "|---|---|---:|---:|---:|---|---|",
    ])
    for item in report["ranked_blocks"]:
        if item["severity"] != "focused_repair_candidate":
            continue
        lines.append(
            f"| {item['kind']} | `{item['key']}` | {item['case_count']} | {item['error_count']} "
            f"| {item['weighted_negative_score_avg']:.3f} | {', '.join(item['risk_flags'])} | `{item['mismatch_field_counts']}` |"
        )
    lines.extend([
        "",
        "## Transfer Risk Candidates",
        "",
        "| kind | key | cases | errors | synthetic rate | language | flags |",
        "|---|---|---:|---:|---:|---|---|",
    ])
    for item in report["ranked_blocks"]:
        if item["severity"] != "transfer_risk_candidate":
            continue
        lines.append(
            f"| {item['kind']} | `{item['key']}` | {item['case_count']} | {item['error_count']} "
            f"| {item['synthetic_bridge_prefix_rate']:.3f} | `{item['language_counts']}` | {', '.join(item['risk_flags'])} |"
        )
    lines.extend([
        "",
        "## Recommended Handling",
        "",
        "1. Do not delete or quarantine automatically from this scan alone.",
        "2. Inspect strong_negative_candidate blocks first; these are possible mislabeled or over-narrow samples.",
        "3. For focused_repair_candidate blocks, prefer code/guard audit when omission or overfire dominates.",
        "4. For transfer_risk_candidate blocks, keep samples quarantined from mainline unless naturalized transfer probes also pass.",
    ])
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    fixtures, skipped = _load_nonsealed_plm_fixtures()
    case_diagnostics: list[dict[str, Any]] = []
    fixture_summaries = []
    for item in fixtures:
        path = item["path"]
        benchmark = item["benchmark"]
        fixture_cases = []
        for case in benchmark.cases:
            diagnostic = _case_diagnostic(path, case)
            fixture_cases.append(diagnostic)
            case_diagnostics.append(diagnostic)
        errors = sum(1 for case in fixture_cases if case["mismatch_fields"])
        fixture_summaries.append(
            {
                "path": _rel(path),
                "case_count": len(fixture_cases),
                "error_count": errors,
                "error_rate": _ratio(errors, len(fixture_cases)),
                "synthetic_bridge_prefix_rate": _ratio(
                    sum(1 for case in fixture_cases if case["synthetic_bridge_prefix"]),
                    len(fixture_cases),
                ),
                "language_counts": dict(sorted(Counter(case["language"] for case in fixture_cases).items())),
            }
        )

    ranked_blocks = _summarize_groups(case_diagnostics)
    summary = {
        "fixtures_scanned": len(fixtures),
        "cases_scanned": len(case_diagnostics),
        "skipped_files": len(skipped),
        "strong_negative_blocks": sum(1 for item in ranked_blocks if item["severity"] == "strong_negative_candidate"),
        "focused_repair_blocks": sum(1 for item in ranked_blocks if item["severity"] == "focused_repair_candidate"),
        "transfer_risk_blocks": sum(1 for item in ranked_blocks if item["severity"] == "transfer_risk_candidate"),
    }
    report = {
        "schema_version": "plm-sample-block-negative-scan.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "diagnostic_completed_no_mutation",
        "policy": {
            "diagnostic_only": True,
            "writes_training_data": False,
            "mutates_router": False,
            "sealed_fixtures_opened": False,
            "active_sealed_opened": False,
            "automatic_quarantine": False,
        },
        "scope": {
            "fixture_root": _rel(FIXTURE_ROOT),
            "included_schema": "pattern-language-benchmark.v1",
            "excluded": ["pattern_language_sealed_*.json", "sealed_boundary_slice_v*.json"],
        },
        "summary": summary,
        "fixture_summaries": sorted(fixture_summaries, key=lambda item: item["path"]),
        "ranked_blocks": ranked_blocks,
        "case_diagnostics": case_diagnostics,
        "skipped_files": skipped,
        "recommended_next_action": "review strong_negative_candidate blocks, then audit constraint omission and hook overfire before quarantine",
    }
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _write_markdown(report)
    print(json.dumps({"status": report["status"], "summary": summary, "outputs": [_rel(OUTPUT_JSON), _rel(OUTPUT_MD)]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()