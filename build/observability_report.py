"""Weak-category failure aggregation with decision traces (v0.3.1).

Runs the campaign through the real route() path (frozen deployed model),
captures the observability trace (decided_by / margin / top scores), and
aggregates misroutes by category — so the data-collection loop can SEE where
and WHY the router fails, not just the score. MEASUREMENT/observation only;
does not change any decision or model.
"""

import io
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import route
from semantic_routing.conversation_accumulation import load_conversation_accumulation

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"


def main() -> None:
    campaign = load_conversation_accumulation(CAMPAIGN)
    by_cat = defaultdict(lambda: {"total": 0, "intent_ok": 0, "e2e_ok": 0})
    by_decided = defaultdict(lambda: {"total": 0, "ok": 0})
    misses = []

    for case in campaign.cases:
        r = route(case.input_text)
        got = r.packet.primary_intent
        decided = r.trace.get("decided_by", "?")
        intent_ok = got == case.expected.intent
        e2e_ok = (intent_ok
                  and r.plan.processing_class == case.expected.processing_class
                  and r.plan.core_mode == case.expected.core_mode)
        c = by_cat[case.category]
        c["total"] += 1
        c["intent_ok"] += intent_ok
        c["e2e_ok"] += e2e_ok
        d = by_decided[decided]
        d["total"] += 1
        d["ok"] += e2e_ok
        if not e2e_ok:
            misses.append({
                "category": case.category, "decided_by": decided,
                "expected": case.expected.intent, "got": got,
                "margin": r.trace.get("intent_margin"),
                "top": r.trace.get("intent_top_scores"),
                "input": case.input_text[:60],
            })

    print("=== end_to_end by category (frozen v0.3) ===")
    for cat, s in sorted(by_cat.items()):
        print(f"  {cat:24s} e2e {s['e2e_ok']}/{s['total']}  "
              f"intent {s['intent_ok']}/{s['total']}")

    print("\n=== by decided_by (how the route was decided) ===")
    for d, s in sorted(by_decided.items()):
        print(f"  {d:9s} ok {s['ok']}/{s['total']}")

    print(f"\n=== misroutes ({len(misses)}) — where to target real data ===")
    for m in sorted(misses, key=lambda x: x["category"]):
        mg = f"{m['margin']:.3f}" if isinstance(m["margin"], float) else "—"
        print(f"  [{m['category']}] {m['expected']}→{m['got']} "
              f"(by {m['decided_by']}, margin {mg})  {m['input']}")
        if m["top"]:
            print(f"      top: {m['top']}")


if __name__ == "__main__":
    main()
