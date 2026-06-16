"""Compare the CANDIDATE vs the DEPLOYED intent model on the campaign.

Same honest path as measure_v03_hybrid (raw case.expected, locked gate
margin), but runs both models so we can see whether the new real-data batch
moved the needle before deciding to promote. MEASUREMENT ONLY.
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
from semantic_routing.conversation_accumulation import load_conversation_accumulation

DEPLOYED = ROOT / "build" / "intent_model_v1.json"
CANDIDATE = ROOT / "build" / "intent_model_v1_candidate.json"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"


def measure(campaign, model):
    e2e = intent_ok = crit = 0
    by_cat = defaultdict(lambda: [0, 0])
    for case in campaign.cases:
        packet = extract_semantic_packet(case.input_text, model)
        plan = build_processing_plan(packet)
        sem = packet.primary_intent == case.expected.intent
        ok = (sem and plan.processing_class == case.expected.processing_class
              and plan.core_mode == case.expected.core_mode)
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
    deployed = IntentModel.load(DEPLOYED)
    candidate = IntentModel.load(CANDIDATE)

    di, de, dc, n, _ = measure(campaign, deployed)
    ci, ce, cc, _, by_cat = measure(campaign, candidate)

    print("                    | intent | end_to_end | critical")
    print(f"deployed (current)  |  {di/n:.2f}  |   {de/n:.2f}     |   {dc}")
    print(f"candidate (+real)   |  {ci/n:.2f}  |   {ce/n:.2f}     |   {cc}")
    print("\ncandidate by category (end_to_end):")
    for cat, (ok, tot) in sorted(by_cat.items()):
        print(f"  {cat:24s} {ok}/{tot}")


if __name__ == "__main__":
    main()
