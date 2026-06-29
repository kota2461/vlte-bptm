"""Extract reviewable weakpoint-explain-english candidates from a debate run.

This is not an adoption step. Raw Gemma/Qwen turns stay review evidence only.
The output is a human-review queue that helps decide which short samples should
be rewritten into a non-sealed fixture later.

Mirrors build/extract_v8_recovery_debate_candidates.py (same scoring philosophy,
same policy, same selection/worksheet shape), adapted to the
`weakpoint_explain_english_v1` topic set: the explain-boundary axes drive the
relevance bonus, and each candidate records the target intent vs the router's
pre-debate intent so a reviewer can see the miss at a glance.
"""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_LOG = ROOT / "build" / "weakpoint_explain_english_debate_v1.json"
DEFAULT_TOPICS_PATH = ROOT / "debate_lab" / "topics_weakpoint_explain_english_v1.json"
DEFAULT_SELECTION_PATH = ROOT / "build" / "weakpoint_explain_english_debate_candidate_selection_v1.json"
DEFAULT_WORKSHEET_PATH = ROOT / "build" / "weakpoint_explain_english_debate_candidate_review_worksheet_v1.md"

# The 7 router intents; the intent axis among a topic's axis_ids is its target.
ROUTER_INTENTS = {"respond", "explain", "build", "verify", "summarize", "explore", "clarify"}

# Axes that make a topic directly relevant to the explain-recall weak surface.
EXPLAIN_BOUNDARY_AXES = {
    "explain",
    "explain_vs_respond",
    "explain_vs_verify",
    "explain_vs_clarify",
    "english",
}

REQUIRED_SECTION_MARKERS = [
    "classification_rule",
    "should_fire_examples",
    "should_not_fire_examples",
    "boundary_cases",
    "candidate_sample_notes",
    "paraphrase_variants",
    "cheap_sufficient_route",
    "router_packet_hint",
    "terminal_action",
]

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "topic_metadata_synthesis_used": True,
    "human_review_required_before_training": True,
    "human_review_required_before_gate": True,
    "same_cycle_gate_use_allowed": False,
    "candidate_queue_is_training_data": False,
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _combined_text(result: dict[str, Any]) -> str:
    return "\n".join(str(turn.get("content", "")) for turn in result.get("turns", []))


def _target_intent(axis_ids: list[str]) -> str:
    for axis in axis_ids:
        if axis in ROUTER_INTENTS:
            return axis
    return ""


def _router_before_intent(result: dict[str, Any]) -> str:
    packet = result.get("router_before", {}).get("packet", {})
    if isinstance(packet, dict):
        return str(packet.get("primary_intent", "") or "")
    return ""


def _score_result(result: dict[str, Any], topic_meta: dict[str, Any], *, min_rounds: int) -> tuple[int, list[str], list[str]]:
    turns = list(result.get("turns", []))
    events = list(result.get("moderation_events", []))
    decision = dict(result.get("router_decision", {}))
    combined = _combined_text(result).lower()
    completed_rounds = len(turns) // 2
    reasoning_chars = sum(int(turn.get("reasoning_content_chars", 0) or 0) for turn in turns)
    content_chars = sum(len(str(turn.get("content", ""))) for turn in turns if turn.get("via") == "content")
    section_hits = [marker for marker in REQUIRED_SECTION_MARKERS if marker in combined]

    score = 0
    reasons: list[str] = []
    cautions: list[str] = []

    if completed_rounds >= min_rounds:
        score += 25
        reasons.append("rounds_complete")
    else:
        cautions.append("below_expected_rounds")

    if decision.get("closed") is True:
        score += 10
        reasons.append("router_closed_topic")
    else:
        cautions.append("router_did_not_close")

    if reasoning_chars == 0 and all(turn.get("via") == "content" for turn in turns):
        score += 10
        reasons.append("final_content_only")
    else:
        cautions.append("suppressed_or_noncontent_turn")

    if content_chars >= 2400:
        score += 10
        reasons.append("enough_discussion_volume")
    elif content_chars >= 1000:
        score += 5
        reasons.append("some_discussion_volume")
    else:
        cautions.append("short_discussion")

    if len(events) >= min_rounds:
        score += 10
        reasons.append("moderator_guided_each_round")
    else:
        cautions.append("few_moderator_events")

    if section_hits:
        score += min(18, len(section_hits) * 2)
        reasons.append("explicit_output_sections:" + ",".join(section_hits[:6]))
    else:
        cautions.append("no_explicit_section_markers")

    priority = topic_meta.get("priority") or result.get("priority")
    if priority == "high":
        score += 7
        reasons.append("high_priority_topic")

    axes = set(topic_meta.get("axis_ids", []) or result.get("axis_ids", []))
    if EXPLAIN_BOUNDARY_AXES & axes:
        score += 8
        reasons.append("explain_boundary_surface")

    if result.get("candidate_stub", {}).get("training_allowed") is False:
        score += 2
        reasons.append("candidate_stub_review_only")

    return score, reasons, cautions


def _candidate_status(score: int, cautions: list[str], min_score: int) -> str:
    if score >= min_score and "below_expected_rounds" not in cautions and "suppressed_or_noncontent_turn" not in cautions:
        return "usable_review_candidate"
    if score >= max(20, min_score - 15):
        return "hold_for_manual_review"
    return "not_enough_signal"


def build_selection(source_log: Path, topics_path: Path, *, min_score: int, min_rounds: int, top: int | None) -> dict[str, Any]:
    run = _load(source_log)
    topics_payload = _load(topics_path)
    topic_meta_by_id = {topic["id"]: topic for topic in topics_payload.get("topics", [])}
    candidates: list[dict[str, Any]] = []

    for index, result in enumerate(run.get("topics", []), start=1):
        topic_id = result["topic_id"]
        meta = topic_meta_by_id.get(topic_id, {})
        score, reasons, cautions = _score_result(result, meta, min_rounds=min_rounds)
        status = _candidate_status(score, cautions, min_score)
        turns = list(result.get("turns", []))
        events = list(result.get("moderation_events", []))
        axis_ids = result.get("axis_ids", meta.get("axis_ids", []))
        target_intent = _target_intent(axis_ids)
        router_before_intent = _router_before_intent(result)
        candidates.append(
            {
                "id": f"weakpoint-explain-english-candidate-{index:03d}",
                "status": status,
                "selection_score": score,
                "source_topic_id": topic_id,
                "target_set": meta.get("target_set", ""),
                "priority": meta.get("priority", ""),
                "recovery_focus": meta.get("recovery_focus", ""),
                "theme": result.get("theme", meta.get("theme", "")),
                "axis_ids": axis_ids,
                "target_intent": target_intent,
                "router_before_intent": router_before_intent,
                "router_before_matches_target": bool(target_intent) and router_before_intent == target_intent,
                "turn_count": len(turns),
                "completed_rounds": len(turns) // 2,
                "moderator_event_count": len(events),
                "content_chars": sum(len(str(turn.get("content", ""))) for turn in turns if turn.get("via") == "content"),
                "reasoning_content_chars": sum(int(turn.get("reasoning_content_chars", 0) or 0) for turn in turns),
                "router_closed": bool(result.get("router_decision", {}).get("closed")),
                "selection_reasons": reasons,
                "cautions": cautions,
                "router_packet_hint": result.get("candidate_stub", {}).get("router_packet_hint", {}),
                "sample_rewrite_instruction": "Human reviewer should rewrite this into a short self-contained non-sealed sample before fixture adoption.",
                "desired_discussion": meta.get("desired_discussion", []),
                "training_status": "not_training_data",
            }
        )

    candidates.sort(key=lambda item: (-item["selection_score"], item["source_topic_id"]))
    if top is not None:
        candidates = candidates[:top]

    status_counts = Counter(candidate["status"] for candidate in candidates)
    focus_counts = Counter(candidate["recovery_focus"] for candidate in candidates)
    axis_counts = Counter(axis for candidate in candidates for axis in candidate.get("axis_ids", []))
    intent_counts = Counter(candidate["target_intent"] for candidate in candidates if candidate["target_intent"])
    miss_count = sum(
        1
        for candidate in candidates
        if candidate["target_intent"] and not candidate["router_before_matches_target"]
    )
    usable = [candidate for candidate in candidates if candidate["status"] == "usable_review_candidate"]

    return {
        "schema_version": "weakpoint-explain-english-debate-candidate-selection.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "candidate_queue_prepared_from_debate_log",
        "source_log": _rel(source_log),
        "topics_source": _rel(topics_path),
        "policy": POLICY,
        "selection_rules": {
            "min_rounds": min_rounds,
            "min_score": min_score,
            "top": top,
            "raw_llm_text_is_training_data": False,
            "candidate_queue_requires_human_rewrite": True,
        },
        "summary": {
            "source_topic_count": len(run.get("topics", [])),
            "candidate_count": len(candidates),
            "usable_review_candidate_count": len(usable),
            "hold_for_manual_review_count": status_counts.get("hold_for_manual_review", 0),
            "not_enough_signal_count": status_counts.get("not_enough_signal", 0),
            "router_before_miss_count": miss_count,
            "turn_count": sum(candidate["turn_count"] for candidate in candidates),
            "expected_rounds": min_rounds,
            "status_counts": dict(sorted(status_counts.items())),
            "focus_counts": dict(sorted(focus_counts.items())),
            "target_intent_counts": dict(sorted(intent_counts.items())),
            "top_axis_counts": dict(axis_counts.most_common(20)),
        },
        "candidates": candidates,
    }


def write_worksheet(path: Path, selection: dict[str, Any]) -> None:
    lines = [
        "# Weakpoint Explain (English) Debate Candidate Review Worksheet v1",
        "",
        "Raw debate turns are not training data. Rewrite selected candidates into short self-contained non-sealed samples before any fixture adoption.",
        "",
        "## Summary",
        "",
    ]
    for key, value in selection["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Candidates",
            "",
            "| id | status | score | topic | target | router_before | miss | rounds | chars | cautions | theme |",
            "|---|---|---:|---|---|---|:--:|---:|---:|---|---|",
        ]
    )
    for candidate in selection["candidates"]:
        cautions = ", ".join(candidate["cautions"]) or "-"
        theme = str(candidate["theme"]).replace("|", "&#124;")
        miss = "-" if not candidate["target_intent"] else ("no" if candidate["router_before_matches_target"] else "YES")
        lines.append(
            f"| {candidate['id']} | {candidate['status']} | {candidate['selection_score']} | "
            f"{candidate['source_topic_id']} | {candidate['target_intent'] or '-'} | {candidate['router_before_intent'] or '-'} | {miss} | "
            f"{candidate['completed_rounds']} | {candidate['content_chars']} | {cautions} | {theme} |"
        )
    lines.extend(
        [
            "",
            "## Review Checklist",
            "",
            "- Keep only candidates that can be rewritten without copying raw LLM prose.",
            "- Prefer minimal pairs that directly address the explain-vs-respond / explain-vs-verify boundary.",
            "- The `miss` column flags where the pre-debate router did not already route to the target intent; prioritise those.",
            "- Separate should_fire from should_not_fire; do not make broad suppression rules from vague cases.",
            "- Preserve constraints and terminal action in the rewritten sample.",
            "- Mark all accepted rows as human-reviewed before fixture use.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract weakpoint-explain-english debate candidates.")
    parser.add_argument("--source-log", default=str(DEFAULT_SOURCE_LOG))
    parser.add_argument("--topics", default=str(DEFAULT_TOPICS_PATH))
    parser.add_argument("--selection", default=str(DEFAULT_SELECTION_PATH))
    parser.add_argument("--worksheet", default=str(DEFAULT_WORKSHEET_PATH))
    parser.add_argument("--min-score", type=int, default=45)
    parser.add_argument("--min-rounds", type=int, default=4)
    parser.add_argument("--top", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_log = Path(args.source_log)
    topics_path = Path(args.topics)
    selection_path = Path(args.selection)
    worksheet_path = Path(args.worksheet)
    if not source_log.is_absolute():
        source_log = ROOT / source_log
    if not topics_path.is_absolute():
        topics_path = ROOT / topics_path
    if not selection_path.is_absolute():
        selection_path = ROOT / selection_path
    if not worksheet_path.is_absolute():
        worksheet_path = ROOT / worksheet_path

    selection = build_selection(
        source_log,
        topics_path,
        min_score=args.min_score,
        min_rounds=args.min_rounds,
        top=args.top,
    )
    _write_json(selection_path, selection)
    write_worksheet(worksheet_path, selection)
    print(
        json.dumps(
            {
                "status": selection["status"],
                "selection": _rel(selection_path),
                "worksheet": _rel(worksheet_path),
                "summary": selection["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
