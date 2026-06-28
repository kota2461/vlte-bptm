"""Select useful V6 boundary-calibration debate logs.

The source run is raw review evidence only. This script classifies topic logs
into review tiers without turning model turns into training data.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_routing.reproducibility import reproducible_now_iso
SOURCE_LOG_PATH = ROOT / "build" / "router_debate_live_31stock_r3.json"
TOPICS_PATH = ROOT / "debate_lab" / "topics_seed.json"
SELECTION_PATH = ROOT / "build" / "v6_boundary_debate_log_selection_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_debate_log_selection_v1.md"

PRIMARY_TARGET_SETS = {"false_positive_set", "paraphrase_set", "no_risk_contrast"}
SECONDARY_TARGET_SETS = {"mixed_ja_en", "current_search_split"}
HOLD_TARGET_SETS = {"severity_ladder"}

IMMEDIATE_FOCUS_AXES = {
    "ai_light_use",
    "ai_task_support",
    "ai_word_only",
    "dependency_suppression",
    "license_general",
    "license_word_only",
    "legal_suppression",
    "current_suppression",
    "medical_ui_design",
    "medical_word_only",
    "diagnosis_suppression",
}

REQUIRED_SECTION_MARKERS = {
    "classification_rule": ["classification_rule", "classification rule"],
    "should_fire_examples": ["should_fire_examples", "should fire", "should-fire"],
    "should_not_fire_examples": ["should_not_fire_examples", "should not fire", "should-not-fire"],
    "boundary_cases": ["boundary_cases", "boundary cases"],
    "candidate_sample_notes": ["candidate_sample_notes", "candidate sample"],
}

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "topic_metadata_selection_allowed": True,
    "human_review_required_before_training": True,
    "human_review_required_before_gate": True,
    "same_cycle_gate_use_allowed": False,
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def clean_excerpt(text: str, limit: int = 260) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def debate_health(topic: dict[str, Any]) -> dict[str, Any]:
    turns = topic.get("turns", [])
    return {
        "turn_count": len(turns),
        "moderation_event_count": len(topic.get("moderation_events", [])),
        "final_decision": topic.get("router_decision", {}).get("decision"),
        "closed": bool(topic.get("router_decision", {}).get("closed")),
        "all_turns_content": all(turn.get("via") == "content" for turn in turns),
        "reasoning_content_chars": sum(turn.get("reasoning_content_chars", 0) for turn in turns),
        "min_turn_chars": min((len(turn.get("content", "")) for turn in turns), default=0),
        "total_content_chars": sum(len(turn.get("content", "")) for turn in turns),
    }


def section_hits(topic: dict[str, Any]) -> dict[str, bool]:
    combined = "\n".join(turn.get("content", "") for turn in topic.get("turns", [])).lower()
    return {
        name: any(marker in combined for marker in markers)
        for name, markers in REQUIRED_SECTION_MARKERS.items()
    }


def classify_topic(topic: dict[str, Any], metadata: dict[str, Any]) -> tuple[str, str]:
    health = debate_health(topic)
    target_set = metadata["target_set"]
    if not health["closed"] or not health["all_turns_content"] or health["reasoning_content_chars"] != 0:
        return "hold_quality_issue", "Log is incomplete, hidden-reasoning-only, or not cleanly closed."
    if target_set in PRIMARY_TARGET_SETS:
        return "select_primary_review", "High-priority false-positive/paraphrase/no-risk calibration topic."
    if target_set in SECONDARY_TARGET_SETS:
        return "select_secondary_review", "Useful medium-priority mixed-language or current/search split topic."
    if target_set in HOLD_TARGET_SETS:
        return "hold_ladder_review", "Severity ladder is useful but should be reviewed after low-risk contrast labels are stable."
    return "hold_unclassified", "Topic target_set is not in the current V6 boundary selection plan."


def score_topic(decision: str, topic: dict[str, Any], metadata: dict[str, Any]) -> tuple[int, list[str]]:
    health = debate_health(topic)
    hits = section_hits(topic)
    axes = set(metadata.get("axis_ids", []))
    score = 0
    reasons: list[str] = []
    if health["turn_count"] == 6 and health["closed"]:
        score += 3
        reasons.append("clean_three_round_closed_log")
    if health["all_turns_content"] and health["reasoning_content_chars"] == 0:
        score += 2
        reasons.append("final_content_available_no_hidden_reasoning")
    if decision == "select_primary_review":
        score += 3
        reasons.append("primary_priority_set")
    elif decision == "select_secondary_review":
        score += 2
        reasons.append("secondary_priority_set")
    if axes & IMMEDIATE_FOCUS_AXES:
        score += 2
        reasons.append("matches_immediate_focus_boundary")
    section_count = sum(hits.values())
    if section_count >= 3:
        score += 1
        reasons.append("contains_multiple_output_contract_sections")
    return score, reasons


def build_item(topic: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    decision, reason = classify_topic(topic, metadata)
    score, reasons = score_topic(decision, topic, metadata)
    turns = topic.get("turns", [])
    return {
        "topic_id": topic["topic_id"],
        "target_set": metadata["target_set"],
        "priority": metadata["priority"],
        "decision": decision,
        "selection_reason": reason,
        "selection_score": score,
        "score_reasons": reasons,
        "immediate_focus_match": bool(set(metadata.get("axis_ids", [])) & IMMEDIATE_FOCUS_AXES),
        "axis_ids": metadata.get("axis_ids", []),
        "theme": topic["theme"],
        "health": debate_health(topic),
        "section_hits": section_hits(topic),
        "evidence_excerpt": {
            "first_expander": clean_excerpt(turns[0].get("content", "")) if turns else "",
            "last_critic": clean_excerpt(turns[-1].get("content", "")) if turns else "",
        },
        "allowed_use": "review_only_log_selection",
        "training_allowed": False,
        "gate_use_allowed": False,
    }


def summarize(items: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any]:
    by_decision = Counter(item["decision"] for item in items)
    by_target_set = Counter(item["target_set"] for item in items)
    immediate = sum(1 for item in items if item["immediate_focus_match"])
    section_coverage: Counter[str] = Counter()
    for item in items:
        for section, present in item["section_hits"].items():
            if present:
                section_coverage[section] += 1
    return {
        "source_topic_count": source["summary"]["topic_count"],
        "source_turn_count": source["summary"]["turn_count"],
        "selected_primary_count": by_decision.get("select_primary_review", 0),
        "selected_secondary_count": by_decision.get("select_secondary_review", 0),
        "held_ladder_count": by_decision.get("hold_ladder_review", 0),
        "quality_issue_count": by_decision.get("hold_quality_issue", 0),
        "immediate_focus_match_count": immediate,
        "by_decision": dict(sorted(by_decision.items())),
        "by_target_set": dict(sorted(by_target_set.items())),
        "section_coverage": dict(sorted(section_coverage.items())),
    }


def write_worksheet(payload: dict[str, Any]) -> None:
    lines = [
        "# V6 Boundary Debate Log Selection v1",
        "",
        "Raw LLM debate turns are review evidence only. This worksheet selects logs for later human rewriting/review; it does not make any item training-ready.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        if isinstance(value, dict):
            continue
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Decisions",
        "",
        "| topic | target_set | decision | score | immediate | reason |",
        "| --- | --- | --- | ---: | --- | --- |",
    ])
    for item in payload["items"]:
        lines.append(
            "| "
            f"{item['topic_id']} | {item['target_set']} | {item['decision']} | "
            f"{item['selection_score']} | {str(item['immediate_focus_match']).lower()} | "
            f"{item['selection_reason']} |"
        )
    lines.extend([
        "",
        "## Immediate Focus Matches",
        "",
        "| topic | target_set | axes | theme |",
        "| --- | --- | --- | --- |",
    ])
    for item in payload["items"]:
        if not item["immediate_focus_match"]:
            continue
        theme = item["theme"].replace("|", "&#124;").replace("\n", "<br>")
        lines.append(
            "| "
            f"{item['topic_id']} | {item['target_set']} | {', '.join(item['axis_ids'])} | {theme} |"
        )
    lines.extend([
        "",
        "## Contract",
        "",
        "- training_allowed: false",
        "- gate_use_allowed: false",
        "- raw_debate_logs_direct_training_allowed: false",
        "- next step: human review, then synthesize short self-contained candidate samples if accepted",
    ])
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = reproducible_now_iso()
    source = load_json(SOURCE_LOG_PATH)
    topics_payload = load_json(TOPICS_PATH)
    metadata_by_id = {topic["id"]: topic for topic in topics_payload["topics"]}
    items = [build_item(topic, metadata_by_id[topic["topic_id"]]) for topic in source["topics"]]
    payload = {
        "schema_version": "v6-boundary-debate-log-selection.v1",
        "generated_at": generated_at,
        "status": "selection_ready_for_human_review",
        "source_log": rel(SOURCE_LOG_PATH),
        "source_topics": rel(TOPICS_PATH),
        "policy": POLICY,
        "summary": summarize(items, source),
        "items": items,
        "next_step": {
            "name": "human_review_then_synthesize_candidate_samples",
            "input": rel(WORKSHEET_PATH),
            "raw_log": rel(SOURCE_LOG_PATH),
            "allowed_use": "review_only",
        },
    }
    write_json(SELECTION_PATH, payload)
    write_worksheet(payload)
    print(json.dumps({
        "status": payload["status"],
        "selection": rel(SELECTION_PATH),
        "worksheet": rel(WORKSHEET_PATH),
        "summary": payload["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()