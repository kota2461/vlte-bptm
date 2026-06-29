"""Format weak-point debate candidates into draft corpus rows (NOT auto-adopted).

Reads the human-review selection
(build/weakpoint_explain_english_debate_candidate_selection_v1.json), extracts a
clean user-utterance from each candidate's theme, attaches the DESIGNED
target_intent (not the router's circular guess), and writes draft corpus-format
rows with review_status="candidate" (load_intent_corpus only reads "approved",
so these are inert until a human flips them).

Filters: exclude held-out (validation/sealed/all sealed_vN), the accumulation
campaign, and existing-corpus duplicates. URL strip + length guard follow the
prior harvest cleaning. Output is a DRAFT file, never the live corpus.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / "build" / "weakpoint_explain_english_debate_candidate_selection_v1.json"
CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
BENCH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
OUT = ROOT / "build" / "weakpoint_explain_english_corpus_candidates_v1.json"

_QUOTE = re.compile(r"'([^']{8,})'")


def _utterance(theme: str) -> str | None:
    """First quoted, utterance-like span; else None (needs manual authoring)."""
    for m in _QUOTE.finditer(theme):
        cand = m.group(1).strip()
        # skip tiny paraphrase tokens like 'why' / 'how come'
        if len(cand.split()) >= 2 or any(ord(c) > 0x3000 for c in cand):
            return cand
    return None


def _held_out() -> set[str]:
    out: set[str] = set()
    b = json.loads(BENCH.read_text(encoding="utf-8"))
    out |= {c["input"] for c in b["cases"] if c["split"] in ("validation", "sealed")}
    for p in sorted((ROOT / "tests" / "fixtures").glob("pattern_language_sealed_v*.json")):
        for c in json.loads(p.read_text(encoding="utf-8")).get("cases", []):
            if "input" in c:
                out.add(c["input"])
    if CAMPAIGN.exists():
        camp = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
        for c in camp.get("cases", camp if isinstance(camp, list) else []):
            if isinstance(c, dict) and "input" in c:
                out.add(c["input"])
    return out


def main() -> None:
    sel = json.loads(SEL.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    have = {e["input"] for e in corpus.get("examples", [])}
    heldout = _held_out()

    rows = []
    need_manual = []
    seen: set[str] = set()
    for c in sel["candidates"]:
        utt = _utterance(c["theme"])
        if not utt:
            need_manual.append(c["id"])
            continue
        if "http" in utt.lower():  # URL strip rule (none expected)
            continue
        if utt in heldout or utt in have or utt in seen:
            continue
        seen.add(utt)
        lang = "ja" if any(0x3000 < ord(ch) for ch in utt) else "en"
        rows.append({
            "input": utt,
            "intent": c["target_intent"],
            "language": lang,
            "source": "weakpoint_explain_english_debate_v1",
            "review_status": "candidate",          # NOT approved -- human must confirm
            "router_before_intent": c["router_before_intent"],
            "router_before_miss": not c["router_before_matches_target"],
            "source_topic_id": c["source_topic_id"],
        })

    from collections import Counter
    doc = {
        "schema_version": "weakpoint-corpus-candidates.v1",
        "status": "draft_human_review_required",
        "policy": {"training_allowed": False, "auto_adopt": False,
                   "note": "review_status=candidate; flip to approved only after human verifies the rewrite + label."},
        "source_selection": SEL.relative_to(ROOT).as_posix(),
        "integration_target": "data/intent_training_corpus_v1.json",
        "row_count": len(rows),
        "by_intent": dict(Counter(r["intent"] for r in rows)),
        "by_language": dict(Counter(r["language"] for r in rows)),
        "miss_rows": sum(1 for r in rows if r["router_before_miss"]),
        "needs_manual_authoring": need_manual,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("row_count", "by_intent", "by_language", "miss_rows", "needs_manual_authoring")}, ensure_ascii=False, indent=1))
    print("draft ->", OUT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
