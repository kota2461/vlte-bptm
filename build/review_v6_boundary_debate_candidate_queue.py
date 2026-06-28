"""Review the V6 boundary debate candidate queue.

This is a non-sealed, non-gate review report. It ranks human-review candidates
from the 48-item queue and highlights current route() gaps, especially
false-positive overfire on low-risk contrast examples.
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import route  # noqa: E402

QUEUE_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_v1.json"
REPORT_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_review_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_review_v1.md"

LOW_RISK_OVERFIRE_FIELDS = {"risk", "information_state", "operations", "constraints", "primary_intent"}
PRIORITY_TARGET_SETS = {
    "contrast_negative_repair",
    "false_positive_set",
    "paraphrase_set",
    "no_risk_contrast",
    "mixed_ja_en",
}

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "candidate_queue_is_training_data": False,
    "review_measurement_is_gate": False,
    "human_review_required_before_training": True,
    "human_review_required_before_gate": True,
    "same_cycle_gate_use_allowed": False,
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def route_summary(text: str) -> dict[str, Any]:
    routed = route(text)
    packet = routed.packet
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
        "retrieval": routed.retrieval.as_dict(),
    }


def expected_core(candidate: dict[str, Any]) -> dict[str, Any]:
    expected = candidate["suggested_expected"]
    return {
        "primary_intent": expected["primary_intent"],
        "operations": list(expected["operations"]),
        "information_state": dict(expected["information_state"]),
        "constraints": dict(expected["constraints"]),
        "risk": dict(expected["risk"]),
    }


def compare_packet(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    if expected["primary_intent"] != actual["primary_intent"]:
        fields.append("primary_intent")
    if list(expected["operations"]) != list(actual["operations"]):
        fields.append("operations")
    if dict(expected["information_state"]) != dict(actual["information_state"]):
        fields.append("information_state")
    if dict(expected["constraints"]) != dict(actual["constraints"]):
        fields.append("constraints")
    if dict(expected["risk"]) != dict(actual["risk"]):
        fields.append("risk")
    return fields


def is_low_risk_overfire(candidate: dict[str, Any], actual: dict[str, Any]) -> bool:
    expected = candidate["suggested_expected"]
    if expected["risk"]["level"] != "low":
        return False
    if actual["risk"]["level"] != "low" or actual["risk"].get("flags"):
        return True
    if actual["information_state"].get("requires_current_information"):
        return True
    if "search" in actual["operations"]:
        return True
    if any(item in actual["constraints"].get("must", []) for item in ["cite_sources", "ask_first", "preserve_neutrality", "avoid_overclaim"]):
        return True
    return False


def review_action(candidate: dict[str, Any], fields: list[str], actual: dict[str, Any]) -> str:
    if candidate["status"].startswith("hold"):
        return "hold_ladder_review"
    if candidate["candidate_type"] == "current_search_positive":
        return "positive_current_counterpart_review"
    if is_low_risk_overfire(candidate, actual):
        return "priority_suppression_review"
    if candidate["target_set"] == "contrast_negative_repair" and fields:
        return "priority_contrast_negative_review"
    if fields:
        return "route_gap_review"
    return "coverage_keep"


def candidate_score(candidate: dict[str, Any], fields: list[str], action: str, actual: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if candidate["status"] == "ready_for_human_review":
        score += 2
        reasons.append("ready_for_human_review")
    if candidate["target_set"] in PRIORITY_TARGET_SETS:
        score += 2
        reasons.append("priority_boundary_target")
    if candidate["target_set"] == "contrast_negative_repair":
        score += 3
        reasons.append("new_contrast_negative_repair")
    if fields:
        score += 2
        reasons.append("current_route_gap")
    if is_low_risk_overfire(candidate, actual):
        score += 3
        reasons.append("low_risk_overfire")
    if candidate["candidate_type"] in {"metalinguistic_suppression", "no_risk_contrast", "contrast_negative_repair"}:
        score += 1
        reasons.append("suppression_signature")
    if candidate["candidate_type"] == "current_search_positive":
        score += 1
        reasons.append("positive_counterpart")
    return score, reasons


def review_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    expected = expected_core(candidate)
    actual = route_summary(candidate["prompt"])
    fields = compare_packet(expected, actual)
    action = review_action(candidate, fields, actual)
    score, reasons = candidate_score(candidate, fields, action, actual)
    return {
        "id": candidate["id"],
        "source_topic_id": candidate["source_topic_id"],
        "target_set": candidate["target_set"],
        "candidate_type": candidate["candidate_type"],
        "status": candidate["status"],
        "action": action,
        "priority_score": score,
        "priority_reasons": reasons,
        "fields": fields,
        "expected": expected,
        "actual": actual,
        "prompt": candidate["prompt"],
        "review_focus": candidate["review_focus"],
        "training_allowed": False,
        "gate_use_allowed": False,
        "human_review_required": True,
    }


def summarize(items: list[dict[str, Any]], queue: dict[str, Any]) -> dict[str, Any]:
    by_action = Counter(item["action"] for item in items)
    by_target = Counter(item["target_set"] for item in items)
    by_type = Counter(item["candidate_type"] for item in items)
    by_field: Counter[str] = Counter(field for item in items for field in item["fields"])
    by_risk = Counter(item["expected"]["risk"]["level"] for item in items)
    ready_items = [item for item in items if item["status"] == "ready_for_human_review"]
    high_priority = [item for item in items if item["priority_score"] >= 9 and item["action"] != "hold_ladder_review"]
    exact_items = [item for item in items if not item["fields"]]
    overfire_items = [item for item in items if item["action"] == "priority_suppression_review"]
    priority_by_target: dict[str, int] = defaultdict(int)
    for item in high_priority:
        priority_by_target[item["target_set"]] += 1
    return {
        "queue_candidate_count": queue["summary"]["candidate_count"],
        "review_item_count": len(items),
        "ready_item_count": len(ready_items),
        "held_item_count": len(items) - len(ready_items),
        "exact_current_route_count": len(exact_items),
        "route_gap_count": len(items) - len(exact_items),
        "priority_review_count": len(high_priority),
        "suppression_overfire_count": len(overfire_items),
        "contrast_negative_repair_count": by_target.get("contrast_negative_repair", 0),
        "contrast_negative_priority_count": priority_by_target.get("contrast_negative_repair", 0),
        "by_action": dict(sorted(by_action.items())),
        "by_target_set": dict(sorted(by_target.items())),
        "by_candidate_type": dict(sorted(by_type.items())),
        "by_expected_risk": dict(sorted(by_risk.items())),
        "error_field_counts": dict(sorted(by_field.items())),
        "top_priority_ids": [item["id"] for item in sorted(high_priority, key=lambda item: (-item["priority_score"], item["id"]))[:20]],
    }


def write_worksheet(report: dict[str, Any]) -> None:
    lines = [
        "# V6 Boundary Debate Candidate Queue Review v1",
        "",
        "Non-sealed review of the 48-item candidate queue. This is not a gate and not training data.",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        if isinstance(value, dict) or isinstance(value, list):
            continue
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Priority Review Items",
        "",
        "| id | score | action | topic | target | type | fields | expected | actual | prompt |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    priority_items = [item for item in report["items"] if item["id"] in set(report["summary"]["top_priority_ids"])]
    priority_items.sort(key=lambda item: (-item["priority_score"], item["id"]))
    for item in priority_items:
        fields = ",".join(item["fields"])
        expected = f"{item['expected']['primary_intent']}:{item['expected']['risk']['level']}"
        actual = f"{item['actual']['primary_intent']}:{item['actual']['risk']['level']}"
        prompt = item["prompt"].replace("|", "&#124;")
        lines.append(
            "| "
            f"{item['id']} | {item['priority_score']} | {item['action']} | {item['source_topic_id']} | "
            f"{item['target_set']} | {item['candidate_type']} | {fields} | {expected} | {actual} | {prompt} |"
        )
    lines.extend([
        "",
        "## Contract",
        "",
        "- training_allowed: false",
        "- gate_use_allowed: false",
        "- human_review_required: true",
        "- same_cycle_gate_use_allowed: false",
    ])
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    queue = load_json(QUEUE_PATH)
    items = [review_candidate(candidate) for candidate in queue["candidates"]]
    report = {
        "schema_version": "v6-boundary-debate-candidate-queue-review.v1",
        "generated_at": generated_at,
        "status": "review_ready_for_human_decision",
        "source_queue": rel(QUEUE_PATH),
        "worksheet": rel(WORKSHEET_PATH),
        "policy": POLICY,
        "summary": summarize(items, queue),
        "items": items,
        "next_step": {
            "name": "human_review_then_optional_nonsealed_replay_adoption",
            "recommended_input": rel(WORKSHEET_PATH),
            "note": "Do not train or gate on this report until the user approves selected candidates.",
        },
    }
    write_json(REPORT_PATH, report)
    write_worksheet(report)
    print(json.dumps({
        "status": report["status"],
        "report": rel(REPORT_PATH),
        "worksheet": rel(WORKSHEET_PATH),
        "summary": report["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()