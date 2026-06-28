"""Prioritize V8 recovery debate candidates for human review.

The extractor intentionally keeps every usable debate topic in a broad queue.
This script makes a smaller first-pass review batch while preserving the
training contract: raw LLM prose is evidence only and must be rewritten by a
human before fixture adoption.
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SELECTION_SOURCE = ROOT / "build" / "v8_recovery_debate_candidate_selection_v1.json"
DEFAULT_SOURCE_LOG = ROOT / "build" / "v8_recovery_debate_r4_100.json"
DEFAULT_OUTPUT = ROOT / "build" / "v8_recovery_debate_candidate_priority_selection_v1.json"
DEFAULT_WORKSHEET = ROOT / "build" / "v8_recovery_debate_candidate_priority_selection_v1.md"


POLICY = {
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "priority_selection_is_training_data": False,
    "human_rewrite_required_before_fixture_adoption": True,
    "human_review_required_before_gate": True,
    "same_cycle_gate_use_allowed": False,
    "length_finish_topics_default_bucket": "hold_for_rerun",
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


def _category(candidate: dict[str, Any]) -> str:
    axes = list(candidate.get("axis_ids", []))
    if len(axes) >= 3:
        return str(axes[2])
    return str(candidate.get("recovery_focus", "unknown")).split()[0] or "unknown"


def _length_finish_details(source_log: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    details: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for topic in source_log.get("topics", []):
        topic_id = str(topic.get("topic_id", ""))
        for index, turn in enumerate(topic.get("turns", []), start=1):
            if turn.get("finish_reason") == "length":
                details[topic_id].append(
                    {
                        "turn_index": index,
                        "role": turn.get("role", ""),
                        "model": turn.get("model", ""),
                    }
                )
    return dict(details)


def _candidate_key(candidate: dict[str, Any]) -> tuple[int, str]:
    return (-int(candidate.get("selection_score", 0)), str(candidate.get("source_topic_id", "")))


def _compact(candidate: dict[str, Any], *, bucket: str, rank: int | None, length_details: list[dict[str, Any]]) -> dict[str, Any]:
    output = {
        "id": candidate["id"],
        "review_bucket": bucket,
        "priority_rank": rank,
        "source_topic_id": candidate["source_topic_id"],
        "category": _category(candidate),
        "selection_score": candidate["selection_score"],
        "status": candidate["status"],
        "recovery_focus": candidate.get("recovery_focus", ""),
        "theme": candidate.get("theme", ""),
        "axis_ids": candidate.get("axis_ids", []),
        "content_chars": candidate.get("content_chars", 0),
        "completed_rounds": candidate.get("completed_rounds", 0),
        "cautions": candidate.get("cautions", []),
        "length_finish": bool(length_details),
        "length_finish_details": length_details,
        "router_packet_hint": candidate.get("router_packet_hint", {}),
        "desired_discussion": candidate.get("desired_discussion", []),
        "sample_rewrite_instruction": candidate.get(
            "sample_rewrite_instruction",
            "Human reviewer should rewrite this into a short self-contained non-sealed sample before fixture adoption.",
        ),
        "training_status": "not_training_data",
        "allowed_use": "human_review_and_rewrite_only",
    }
    return output


def build_priority_selection(
    selection_source: Path,
    source_log: Path,
    *,
    per_category: int,
) -> dict[str, Any]:
    selection = _load(selection_source)
    log = _load(source_log)
    length_by_topic = _length_finish_details(log)
    length_topic_ids = set(length_by_topic)

    candidates = list(selection.get("candidates", []))
    usable = [candidate for candidate in candidates if candidate.get("status") == "usable_review_candidate"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in usable:
        groups[_category(candidate)].append(candidate)

    priority: list[dict[str, Any]] = []
    priority_ids: set[str] = set()
    deficits: dict[str, int] = {}

    for category in sorted(groups):
        ordered = sorted(groups[category], key=_candidate_key)
        non_length = [candidate for candidate in ordered if candidate.get("source_topic_id") not in length_topic_ids]
        selected = non_length[:per_category]
        deficits[category] = max(0, per_category - len(selected))
        for candidate in selected:
            priority_ids.add(candidate["id"])
            priority.append(candidate)

    priority.sort(key=lambda candidate: (_category(candidate), _candidate_key(candidate)))

    hold = [
        candidate
        for candidate in sorted(candidates, key=lambda candidate: str(candidate.get("source_topic_id", "")))
        if candidate.get("source_topic_id") in length_topic_ids and candidate["id"] not in priority_ids
    ]
    hold_ids = {candidate["id"] for candidate in hold}
    reserve = [
        candidate
        for candidate in sorted(candidates, key=_candidate_key)
        if candidate["id"] not in priority_ids and candidate["id"] not in hold_ids
    ]

    priority_records = [
        _compact(candidate, bucket="priority_review", rank=index, length_details=length_by_topic.get(candidate["source_topic_id"], []))
        for index, candidate in enumerate(priority, start=1)
    ]
    hold_records = [
        _compact(candidate, bucket="hold_for_rerun_length_finish", rank=None, length_details=length_by_topic.get(candidate["source_topic_id"], []))
        for candidate in hold
    ]
    reserve_records = [
        _compact(candidate, bucket="reserve_review", rank=None, length_details=length_by_topic.get(candidate["source_topic_id"], []))
        for candidate in reserve
    ]

    priority_category_counts = Counter(record["category"] for record in priority_records)
    hold_category_counts = Counter(record["category"] for record in hold_records)
    reserve_category_counts = Counter(record["category"] for record in reserve_records)

    return {
        "schema_version": "v8-recovery-debate-candidate-priority-selection.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "priority_review_queue_prepared",
        "selection_source": _rel(selection_source),
        "source_log": _rel(source_log),
        "policy": POLICY,
        "selection_rules": {
            "per_category": per_category,
            "priority_review_strategy": "balanced_top_n_per_category",
            "exclude_length_finish_from_priority_review": True,
            "raw_llm_text_is_training_data": False,
            "human_rewrite_required": True,
        },
        "summary": {
            "source_candidate_count": len(candidates),
            "usable_source_candidate_count": len(usable),
            "priority_review_count": len(priority_records),
            "hold_for_rerun_count": len(hold_records),
            "reserve_review_count": len(reserve_records),
            "length_finish_topic_count": len(length_topic_ids),
            "length_finish_turn_count": sum(len(items) for items in length_by_topic.values()),
            "priority_category_counts": dict(sorted(priority_category_counts.items())),
            "hold_category_counts": dict(sorted(hold_category_counts.items())),
            "reserve_category_counts": dict(sorted(reserve_category_counts.items())),
            "category_deficits": {key: value for key, value in sorted(deficits.items()) if value},
        },
        "priority_review": priority_records,
        "hold_for_rerun": hold_records,
        "reserve_review": reserve_records,
    }


def write_worksheet(path: Path, priority_selection: dict[str, Any]) -> None:
    lines = [
        "# V8 Recovery Debate Candidate Priority Selection v1",
        "",
        "Raw Gemma/Qwen turns are evidence only. Rewrite any accepted row into a short self-contained non-sealed sample before fixture adoption.",
        "",
        "## Summary",
        "",
    ]
    for key, value in priority_selection["summary"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "## Priority Review",
            "",
            "| rank | id | category | score | topic | chars | theme |",
            "|---:|---|---|---:|---|---:|---|",
        ]
    )
    for record in priority_selection["priority_review"]:
        theme = str(record["theme"]).replace("|", "&#124;")
        lines.append(
            f"| {record['priority_rank']} | {record['id']} | {record['category']} | "
            f"{record['selection_score']} | {record['source_topic_id']} | {record['content_chars']} | {theme} |"
        )

    lines.extend(
        [
            "",
            "## Hold For Rerun",
            "",
            "These candidates reached usable score, but at least one turn ended by token length. Prefer rerun before adopting.",
            "",
            "| id | category | score | topic | length turns | theme |",
            "|---|---|---:|---|---|---|",
        ]
    )
    for record in priority_selection["hold_for_rerun"]:
        length_turns = ", ".join(f"{item['role']}@{item['turn_index']}" for item in record["length_finish_details"])
        theme = str(record["theme"]).replace("|", "&#124;")
        lines.append(
            f"| {record['id']} | {record['category']} | {record['selection_score']} | "
            f"{record['source_topic_id']} | {length_turns} | {theme} |"
        )

    lines.extend(
        [
            "",
            "## Reserve Review",
            "",
            "Reserve candidates remain usable, but should wait until the balanced priority batch is reviewed.",
            "",
            "| id | category | score | topic | theme |",
            "|---|---|---:|---|---|",
        ]
    )
    for record in priority_selection["reserve_review"]:
        theme = str(record["theme"]).replace("|", "&#124;")
        lines.append(f"| {record['id']} | {record['category']} | {record['selection_score']} | {record['source_topic_id']} | {theme} |")

    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- Keep priority review balanced: first pass is 3 candidates per V8 weakness category.",
            "- Do not copy model prose into fixtures; use it only to guide human-authored sample rewriting.",
            "- Length-finish candidates are not bad data, but they should be rerun or manually checked before adoption.",
            "- Maintain positive/negative contrast pairs where possible.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-source", type=Path, default=DEFAULT_SELECTION_SOURCE)
    parser.add_argument("--source-log", type=Path, default=DEFAULT_SOURCE_LOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET)
    parser.add_argument("--per-category", type=int, default=3)
    args = parser.parse_args()

    priority_selection = build_priority_selection(
        args.selection_source,
        args.source_log,
        per_category=args.per_category,
    )
    _write_json(args.output, priority_selection)
    write_worksheet(args.worksheet, priority_selection)
    print(
        json.dumps(
            {
                "status": priority_selection["status"],
                "output": _rel(args.output),
                "worksheet": _rel(args.worksheet),
                "summary": priority_selection["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
