"""Honest v0.3 measurement: end-to-end through the REAL hybrid path.

Runs extract_semantic_packet(text, intent_model) -> build_processing_plan on
the campaign with the deployed intent model and the locked conservative gate
(margin 0.15, baked into baseline.INTENT_GATE_MARGIN). Compares to
markers-only (no model). Single measurement with the pre-committed threshold
— the honest v0.3 number. MEASUREMENT ONLY.
"""

import io
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import build_processing_plan, extract_semantic_packet
from semantic_routing.intent_model import IntentModel
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

MODEL = ROOT / "build" / "intent_model_v1.json"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"


def measure(campaign, model):
    e2e = intent_ok = crit = 0
    by_cat = defaultdict(lambda: [0, 0])
    for case in campaign.cases:
        packet = extract_semantic_packet(case.input_text, model)
        plan = build_processing_plan(packet)
        sem = packet.primary_intent == case.expected.intent
        ok = (
            sem
            and plan.processing_class == case.expected.processing_class
            and plan.core_mode == case.expected.core_mode
        )
        intent_ok += sem
        e2e += ok
        if case.critical_underprocessing and not ok:
            crit += 1
        b = by_cat[case.category]
        b[0] += ok
        b[1] += 1
    n = len(campaign.cases)
    return intent_ok, e2e, crit, n, by_cat


def main() -> None:
    campaign = load_conversation_accumulation(CAMPAIGN)
    model = IntentModel.load(MODEL)

    mi, me, mc, n, _ = measure(campaign, None)
    hi, he, hc, _, by_cat = measure(campaign, model)

    print("                 | intent | end_to_end | critical")
    print(f"markers-only     |  {mi/n:.2f}  |   {me/n:.2f}     |   {mc}")
    print(f"v0.3 hybrid      |  {hi/n:.2f}  |   {he/n:.2f}     |   {hc}")
    print("\nv0.3 hybrid by category (end_to_end):")
    for cat, (ok, tot) in sorted(by_cat.items()):
        print(f"  {cat:24s} {ok}/{tot}")


if __name__ == "__main__":
    main()
