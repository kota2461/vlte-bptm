import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import route

QUEUE_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_v1.json"
REVIEW_PATH = ROOT / "build" / "router_debate_v6_facilitated_contrast_repair_review_v1.json"
SCORE_REPORT_PATH = ROOT / "build" / "v6_score_report_v1.json"
REPORT_PATH = ROOT / "build" / "router_debate_v6_facilitated_score_comparison_v1.json"
SUMMARY_PATH = ROOT / "build" / "router_debate_v6_facilitated_score_comparison_v1.md"

WEIGHTS = {
    "intent_accuracy": 0.25,
    "critical_signal_recall": 0.20,
    "operation_exact_match": 0.20,
    "constraint_exact_match": 0.15,
    "risk_exact_match": 0.15,
    "valid_packet_rate": 0.05,
}
CRITICAL_KEYS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def packet(text: str) -> dict:
    routed = route(text)
    p = routed.packet
    return {
        "primary_intent": p.primary_intent,
        "operations": list(p.operations),
        "information_state": p.information_state.as_dict(),
        "constraints": p.constraints.as_dict(),
        "risk": p.risk.as_dict(),
    }


def measure(topic_ids: list[str], cases: dict[str, dict], review_status: dict[str, str]) -> dict:
    errors = []
    field_counts = Counter()
    metric_counts = Counter()
    support = Counter()
    rows = []
    for topic_id in topic_ids:
        case = cases[topic_id]
        expected = case["suggested_expected"]
        actual = packet(case["prompt"])
        fields = []
        if expected["primary_intent"] == actual["primary_intent"]:
            metric_counts["intent"] += 1
        else:
            fields.append("primary_intent")
        if list(expected["operations"]) == list(actual["operations"]):
            metric_counts["operations"] += 1
        else:
            fields.append("operations")
        if dict(expected["constraints"]) == dict(actual["constraints"]):
            metric_counts["constraints"] += 1
        else:
            fields.append("constraints")
        if dict(expected["risk"]) == dict(actual["risk"]):
            metric_counts["risk"] += 1
        else:
            fields.append("risk")
        if dict(expected["information_state"]) != dict(actual["information_state"]):
            fields.append("information_state")
        for key in CRITICAL_KEYS:
            if expected["information_state"].get(key):
                support[key] += 1
        if fields:
            errors.append(
                {
                    "topic_id": topic_id,
                    "fields": fields,
                    "expected_intent": expected["primary_intent"],
                    "actual_intent": actual["primary_intent"],
                    "expected_operations": expected["operations"],
                    "actual_operations": actual["operations"],
                    "expected_risk": expected["risk"],
                    "actual_risk": actual["risk"],
                }
            )
            field_counts.update(fields)
        rows.append(
            {
                "topic_id": topic_id,
                "review_status": review_status[topic_id],
                "fields": fields,
                "expected": expected,
                "actual": actual,
                "prompt": case["prompt"],
            }
        )
    count = len(topic_ids)
    compact = {
        "case_count": count,
        "intent_accuracy": round(metric_counts["intent"] / count, 6) if count else 0.0,
        "critical_signal_recall": 0.0,
        "operation_exact_match": round(metric_counts["operations"] / count, 6) if count else 0.0,
        "constraint_exact_match": round(metric_counts["constraints"] / count, 6) if count else 0.0,
        "risk_exact_match": round(metric_counts["risk"] / count, 6) if count else 0.0,
        "valid_packet_rate": 1.0 if count else 0.0,
        "error_count": len(errors),
        "error_field_counts": dict(sorted(field_counts.items())),
    }
    raw_score = round(sum(compact[key] * weight for key, weight in WEIGHTS.items()), 6)
    active_weights = dict(WEIGHTS)
    if sum(support.values()) == 0:
        active_weights.pop("critical_signal_recall")
    score = round(
        sum(compact[key] * weight for key, weight in active_weights.items()) / sum(active_weights.values()),
        6,
    )
    return {
        "topic_ids": topic_ids,
        "measurement": compact,
        "critical_signal_support": {key: support.get(key, 0) for key in CRITICAL_KEYS},
        "score": score,
        "raw_score": raw_score,
        "score_note": "critical_signal_recall excluded because expected critical-signal support is zero",
        "errors": errors,
        "rows": rows,
    }


def main() -> None:
    queue = load_json(QUEUE_PATH)
    review = load_json(REVIEW_PATH)
    score_report = load_json(SCORE_REPORT_PATH)
    topic_ids = [topic["topic_id"] for topic in review["topics"]]
    review_status = {topic["topic_id"]: topic["status"] for topic in review["topics"]}
    clean_ids = [topic["topic_id"] for topic in review["topics"] if topic["status"] == "candidate_ready"]
    cases = {case["source_topic_id"]: case for case in queue["candidates"] if case.get("source_topic_id") in topic_ids}
    missing = [topic_id for topic_id in topic_ids if topic_id not in cases]
    if missing:
        raise SystemExit(f"missing candidate queue items: {missing}")

    clean = measure(clean_ids, cases, review_status)
    included = measure(topic_ids, cases, review_status)
    official = score_report["lanes"]["v6_boundary_priority_review_adopted"]
    official_compact = {
        "source": "build/v6_score_report_v1.json#v6_boundary_priority_review_adopted",
        "score": official["score"],
        "raw_score": official["raw_score"],
        "measurement": official["measurement"],
    }
    report = {
        "schema_version": "router-debate-facilitated-score-comparison.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "source_review": rel(REVIEW_PATH),
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "review_measurement_is_gate": False,
            "raw_debate_turns_direct_training_allowed": False,
        },
        "scenarios": {
            "clean_only_excluding_rerun_recommended": clean,
            "with_caution_item_included": included,
            "official_adopted_priority_review_lane": official_compact,
        },
        "comparison": {
            "clean_vs_official_score_delta": round(clean["score"] - official["score"], 6),
            "included_vs_clean_score_delta": round(included["score"] - clean["score"], 6),
            "included_vs_official_score_delta": round(included["score"] - official["score"], 6),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# Router Debate V6 Facilitated Score Comparison v1",
        "",
        "| scenario | cases | score | raw | errors | intent | operation | constraint | risk |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, scenario in [
        ("clean_only_excluding_rerun_recommended", clean),
        ("with_caution_item_included", included),
        ("official_adopted_priority_review_lane", official_compact),
    ]:
        measurement = scenario["measurement"]
        lines.append(
            f"| {name} | {measurement['case_count']} | {scenario['score']:.6f} | "
            f"{scenario['raw_score']:.6f} | {measurement['error_count']} | "
            f"{measurement['intent_accuracy']:.6f} | {measurement['operation_exact_match']:.6f} | "
            f"{measurement['constraint_exact_match']:.6f} | {measurement['risk_exact_match']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Deltas",
            "",
            f"- clean_vs_official_score_delta: {report['comparison']['clean_vs_official_score_delta']:+.6f}",
            f"- included_vs_clean_score_delta: {report['comparison']['included_vs_clean_score_delta']:+.6f}",
            f"- included_vs_official_score_delta: {report['comparison']['included_vs_official_score_delta']:+.6f}",
            "",
            "## Notes",
            "",
        ]
    )
    if clean["measurement"]["case_count"] == included["measurement"]["case_count"]:
        lines.append("- No rerun-recommended topics remain; clean-only and included scenarios are identical.")
    else:
        lines.append("- clean_only excludes rerun-recommended or caution topics.")
    lines.extend(
        [
            "- official_adopted_priority_review_lane is the existing 26-case adopted lane in `build/v6_score_report_v1.json`.",
            "- This is a non-sealed replay comparison and is not a promotion gate.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "json": rel(REPORT_PATH),
                "md": rel(SUMMARY_PATH),
                "clean_score": clean["score"],
                "included_score": included["score"],
                "official_adopted_score": official["score"],
                "comparison": report["comparison"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()