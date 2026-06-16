"""Generate a human-review worksheet for the frozen 50-case campaign.

For each case: draft expected label, the adapter's actual prediction, the
source, and whether it needs a genuine human DECISION (policy-laden) versus
a quick CONFIRM. Helps the reviewer spend judgment where it matters without
rubber-stamping. Writes build/review_worksheet_50.md and prints the
decision subset. Reads labels/notes from build/batch02_staging.json for
batch-02; batch-01 (original seed) cases are listed for confirmation.
"""

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import build_processing_plan, extract_semantic_packet
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
STAGING = ROOT / "build" / "batch02_staging.json"
OUT = ROOT / "build" / "review_worksheet_50.md"


def main() -> None:
    campaign = load_conversation_accumulation(CAMPAIGN)
    staging = {
        c["id"]: c
        for c in json.loads(STAGING.read_text(encoding="utf-8"))["cases"]
    }

    rows = []
    for case in campaign.cases:
        packet = extract_semantic_packet(case.input_text)
        plan = build_processing_plan(packet)
        actual = f"{packet.primary_intent}/{plan.processing_class}/{plan.core_mode}"
        exp = case.expected
        draft = f"{exp.intent}/{exp.processing_class}/{exp.core_mode}"
        match = actual == draft
        staged = staging.get(case.case_id, {})
        note = staged.get("_label_note", "")
        source = staged.get("_source", "original_batch01")
        decision = note.startswith("POLICY")
        rows.append({
            "id": case.case_id,
            "source": source,
            "category": case.category,
            "input": case.input_text,
            "draft": draft,
            "actual": actual,
            "match": match,
            "decision": decision,
            "note": note,
        })

    decisions = [r for r in rows if r["decision"]]
    confirms = [r for r in rows if not r["decision"]]

    lines = ["# Review Worksheet — 50-case campaign (draft labels)", ""]
    lines.append(
        f"DECISION (policy-laden, needs your ruling): {len(decisions)} | "
        f"CONFIRM (apply agreed policy): {len(confirms)}"
    )
    lines.append("")
    lines.append("## DECISION — rule on these")
    lines.append("")
    lines.append("| id | category | input | draft expected | adapter | note |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in decisions:
        lines.append(
            f"| {r['id']} | {r['category']} | {r['input']} | "
            f"`{r['draft']}` | `{r['actual']}` | {r['note'].replace('POLICY', '').strip()} |"
        )
    lines.append("")
    lines.append("## CONFIRM — agreed policy applies (skim)")
    lines.append("")
    lines.append("| id | source | category | input | draft expected | adapter | match |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for r in confirms:
        lines.append(
            f"| {r['id']} | {r['source']} | {r['category']} | {r['input']} | "
            f"`{r['draft']}` | `{r['actual']}` | {'=' if r['match'] else '≠'} |"
        )
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"DECISION cases: {len(decisions)} | CONFIRM cases: {len(confirms)}")
    print(f"worksheet: {OUT}\n")
    print("== cases that need your ruling ==")
    for r in decisions:
        print(f"[{r['id']}] {r['category']}")
        print(f"   {r['input']}")
        print(f"   draft={r['draft']}  adapter={r['actual']}")
        print(f"   {r['note']}")


if __name__ == "__main__":
    main()
