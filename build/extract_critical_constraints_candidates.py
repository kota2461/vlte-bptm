"""Extract non-sealed critical-signal/constraint review candidates.

The output is diagnostic and review-oriented only. It reads open/user-log
sources, runs the current canonical route() adapter to create draft labels,
and writes:

- build/critical_constraints_candidates_v1.json
- build/critical_constraints_review_worksheet_v1.md

It deliberately does not read any sealed fixture.
"""

import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso


SOURCES = (
    {
        "name": "harvested_claudelog",
        "path": ROOT / "data" / "harvested_claudelog_v1.json",
        "list_key": "examples",
        "text_key": "input",
    },
    {
        "name": "intent_training_corpus",
        "path": ROOT / "data" / "intent_training_corpus_v1.json",
        "list_key": "examples",
        "text_key": "input",
    },
    {
        "name": "conversation_accumulation",
        "path": ROOT / "data" / "conversation_accumulation_v1.json",
        "list_key": "cases",
        "text_key": "input",
    },
    {
        "name": "batch02_staging",
        "path": ROOT / "build" / "batch02_staging.json",
        "list_key": "cases",
        "text_key": "input",
    },
)

OUT_JSON = ROOT / "build" / "critical_constraints_candidates_v1.json"
OUT_MD = ROOT / "build" / "critical_constraints_review_worksheet_v1.md"
C_PROBE_WORKSHEET_LIMIT = 50

HIGH_VALUE_SOURCE_INTENTS = {
    "verify",
    "clarify",
    "explore",
    "summarize",
    "build",
}
CONTROL_OPERATIONS = {"verify", "search", "calculate", "compare"}
CRITICAL_FIELDS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)


def _load_rows(source: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    path = source["path"]
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload[source["list_key"]]
    result = []
    for index, row in enumerate(rows, start=1):
        text = str(row.get(source["text_key"], "")).strip()
        if not text:
            continue
        result.append(
            {
                "source": source["name"],
                "source_path": str(path.relative_to(ROOT)),
                "source_index": index,
                "input": text,
                "source_intent": _source_intent(row),
                "source_status": row.get("review_status"),
                "source_confidence": row.get("confidence"),
                "source_note": row.get("note") or row.get("_label_note"),
                "source_category": row.get("category"),
            }
        )
    return result


def _source_intent(row: Dict[str, Any]) -> str | None:
    if row.get("intent"):
        return str(row["intent"])
    expected = row.get("expected")
    if isinstance(expected, dict):
        if expected.get("intent"):
            return str(expected["intent"])
        if expected.get("primary_intent"):
            return str(expected["primary_intent"])
    return None


def _constraint_tags(constraints: Dict[str, Any]) -> List[str]:
    tags = []
    if constraints["response_length"] != "unspecified":
        tags.append(f"length:{constraints['response_length']}")
    tags.extend(f"format:{item}" for item in constraints["formats"])
    tags.extend(f"must:{item}" for item in constraints["must"])
    tags.extend(f"must_not:{item}" for item in constraints["must_not"])
    return tags


def _score_candidate(
    *,
    source_intents: set[str],
    info: Dict[str, bool],
    constraints: Dict[str, Any],
    operations: List[str],
    risk: Dict[str, Any],
) -> tuple[int, List[str], List[str]]:
    score = 0
    review_focus: List[str] = []
    reasons: List[str] = []

    for field in CRITICAL_FIELDS:
        if info[field]:
            score += 10
            review_focus.append(f"critical_signal:{field}")
            reasons.append(field)

    constraint_tags = _constraint_tags(constraints)
    if constraint_tags:
        score += 8 + len(constraint_tags)
        review_focus.append("constraints")
        reasons.extend(constraint_tags)

    control_ops = [op for op in operations if op in CONTROL_OPERATIONS]
    if control_ops:
        score += 6 + len(control_ops)
        review_focus.append("operations")
        reasons.append("ops:" + ",".join(control_ops))

    if risk["level"] != "low":
        score += 6
        review_focus.append("risk")
        reasons.append(f"risk:{risk['level']}")

    useful_source_intents = sorted(source_intents & HIGH_VALUE_SOURCE_INTENTS)
    if useful_source_intents:
        score += 2
        reasons.append("source_intent:" + ",".join(useful_source_intents))

    if not review_focus and useful_source_intents:
        review_focus.append("source_intent_probe")

    return score, sorted(set(review_focus)), reasons


def _candidate_priority(score: int, focus: List[str]) -> str:
    if score >= 28 or any(
        tag.startswith("critical_signal") for tag in focus
    ):
        return "A"
    if score >= 14 or "constraints" in focus or "operations" in focus:
        return "B"
    return "C"


def _draft_candidate(text: str, origins: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    routed = route(text)
    packet = routed.packet
    source_intents = {
        str(origin["source_intent"])
        for origin in origins
        if origin.get("source_intent")
    }
    info = packet.information_state.as_dict()
    constraints = packet.constraints.as_dict()
    risk = packet.risk.as_dict()
    operations = list(packet.operations)
    score, review_focus, reasons = _score_candidate(
        source_intents=source_intents,
        info=info,
        constraints=constraints,
        operations=operations,
        risk=risk,
    )
    if score <= 0:
        return None

    return {
        "id": "",
        "review_status": "pending",
        "priority": _candidate_priority(score, review_focus),
        "score": score,
        "review_focus": review_focus,
        "reason_tags": reasons,
        "input": text,
        "draft_expected": {
            "primary_intent": packet.primary_intent,
            "operations": operations,
            "information_state": info,
            "constraints": constraints,
            "risk": risk,
        },
        "adapter_trace": {
            "decided_by": routed.trace.get("decided_by"),
            "intent_margin": routed.trace.get("intent_margin"),
            "markers_fired": routed.trace.get("markers_fired"),
        },
        "source_intents": sorted(source_intents),
        "origins": origins,
    }


def _short_text(text: str, limit: int = 120) -> str:
    single = " ".join(text.split())
    return single if len(single) <= limit else single[: limit - 1] + "…"


def _markdown_table(candidates: List[Dict[str, Any]]) -> List[str]:
    lines = [
        "| id | focus | draft | source intent | score | input |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for candidate in candidates:
        draft = candidate["draft_expected"]
        draft_label = (
            f"{draft['primary_intent']} / "
            f"ops={','.join(draft['operations'])}"
        )
        source_intents = ", ".join(candidate["source_intents"]) or "-"
        lines.append(
            "| "
            f"{candidate['id']} | "
            f"{', '.join(candidate['review_focus'])} | "
            f"`{draft_label}` | "
            f"`{source_intents}` | "
            f"{candidate['score']} | "
            f"{_short_text(candidate['input']).replace('|', '&#124;')} |"
        )
    return lines


def _write_worksheet(report: Dict[str, Any]) -> None:
    candidates = report["candidates"]
    by_priority = defaultdict(list)
    for candidate in candidates:
        by_priority[candidate["priority"]].append(candidate)

    lines = [
        "# Critical / Constraints Candidate Review v1",
        "",
        "Diagnostic only. These are non-sealed candidates extracted from open "
        "logs/corpora. Draft labels come from the current adapter and must be "
        "human-reviewed before training or gate use.",
        "",
        "Sealed fixtures are not input sources for this worksheet.",
        "",
        "## Summary",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- unique inputs scanned: {report['summary']['unique_inputs_scanned']}",
        f"- candidates: {report['summary']['candidate_count']}",
        f"- review candidates (A+B): {report['summary']['review_candidate_count']}",
        f"- probe candidates (C): {report['summary']['probe_candidate_count']}",
        f"- priority counts: {report['summary']['by_priority']}",
        f"- focus counts: {report['summary']['by_focus']}",
        f"- route intent counts: {report['summary']['by_draft_intent']}",
        "",
        "## Review Rule",
        "",
        "For each row, approve only if the draft `critical_signal`, "
        "`constraints`, `risk`, and `operations` are correct. Otherwise mark "
        "corrected labels in the JSON/notes before promotion.",
        "",
    ]

    for priority, title in (
        ("A", "Priority A - Critical Signals"),
        ("B", "Priority B - Constraints / Operations"),
        ("C", "Priority C - Source-Intent Probes"),
    ):
        rows = by_priority.get(priority, [])
        lines.extend([f"## {title}", ""])
        if rows:
            displayed = (
                rows[:C_PROBE_WORKSHEET_LIMIT]
                if priority == "C"
                else rows
            )
            if priority == "C" and len(rows) > len(displayed):
                lines.append(
                    f"Showing first {len(displayed)} of {len(rows)} "
                    "source-intent probes. Full list is in the JSON."
                )
                lines.append("")
            lines.extend(_markdown_table(displayed))
        else:
            lines.append("- none")
        lines.append("")

    lines.extend(["## Source Coverage", ""])
    for source, count in report["summary"]["by_source"].items():
        lines.append(f"- {source}: {count}")
    lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows_by_text: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    source_row_counts = Counter()
    for source in SOURCES:
        for row in _load_rows(source):
            source_row_counts[row["source"]] += 1
            rows_by_text[row["input"]].append(
                {k: v for k, v in row.items() if k != "input"}
            )

    candidates = []
    for text, origins in rows_by_text.items():
        candidate = _draft_candidate(text, origins)
        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            item["priority"],
            -item["score"],
            item["draft_expected"]["primary_intent"],
            item["input"],
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = f"cc-open-v1-{index:03d}"

    by_priority = Counter(candidate["priority"] for candidate in candidates)
    by_focus = Counter(
        focus for candidate in candidates for focus in candidate["review_focus"]
    )
    by_source = Counter(
        origin["source"]
        for candidate in candidates
        for origin in candidate["origins"]
    )
    by_draft_intent = Counter(
        candidate["draft_expected"]["primary_intent"]
        for candidate in candidates
    )
    report = {
        "schema_version": "critical-constraints-candidates.v1",
        "generated_at": reproducible_now_iso(),
        "policy": {
            "sealed_fixtures_used": False,
            "candidate_status": (
                "draft; human review required before training or gate use"
            ),
        },
        "sources": [
            {
                "name": source["name"],
                "path": str(source["path"].relative_to(ROOT)),
                "row_count": source_row_counts[source["name"]],
            }
            for source in SOURCES
        ],
        "summary": {
            "unique_inputs_scanned": len(rows_by_text),
            "candidate_count": len(candidates),
            "review_candidate_count": sum(
                1
                for candidate in candidates
                if candidate["priority"] in {"A", "B"}
            ),
            "probe_candidate_count": sum(
                1
                for candidate in candidates
                if candidate["priority"] == "C"
            ),
            "by_priority": dict(sorted(by_priority.items())),
            "by_focus": dict(sorted(by_focus.items())),
            "by_source": dict(sorted(by_source.items())),
            "by_draft_intent": dict(sorted(by_draft_intent.items())),
        },
        "candidates": candidates,
    }

    OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_worksheet(report)

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
