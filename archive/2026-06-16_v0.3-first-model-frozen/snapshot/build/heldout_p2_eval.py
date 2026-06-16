"""Held-out generalization check for the Priority-2 accuracy fix.

Fresh phrasings (NOT copied from the 50-case campaign) for indirect
explanation and plain conversational/response, plus guard cases (verify /
build / explore / explain-direct) to catch over-triggering or regressions
from the no-match-fallback change. MEASUREMENT ONLY; re-measures the 50-case
campaign for the headline.
"""

import io
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

# (input, intent, processing_class, core_mode)
HELDOUT = [
    # indirect explanation -> explain/economy/horizontal
    ("行列の掛け算、計算はできるけど何をやってるのか実感がわかない",
     "explain", "economy", "horizontal"),
    ("ポインタ、使えるんだけど結局なにものなのかがしっくりこない",
     "explain", "economy", "horizontal"),
    ("なんでこの式が成り立つのか、いまいちピンとこない",
     "explain", "economy", "horizontal"),
    ("I can follow the steps but I don't really get why it works.",
     "explain", "economy", "horizontal"),
    # plain conversational / response -> respond/economy/horizontal
    ("ちょっと愚痴を聞いてほしいんだけど",
     "respond", "economy", "horizontal"),
    ("やっと終わった、ほっとしたよ",
     "respond", "economy", "horizontal"),
    ("最近うまくいかなくて落ち込んでる",
     "respond", "economy", "horizontal"),
    # guards: must not regress
    ("この設計のリスクを確認してください",
     "verify", "verified", "vertical"),
    ("実装手順を作ってください",
     "build", "standard", "horizontal"),
    ("候補をいくつか比較してください",
     "explore", "deep", "hybrid"),
    ("この設計の狙いを説明してください",
     "explain", "economy", "horizontal"),
]


def measure_campaign():
    campaign = load_conversation_accumulation(CAMPAIGN)
    e2e = crit = 0
    by = {}
    for case in campaign.cases:
        packet = extract_semantic_packet(case.input_text)
        plan = build_processing_plan(packet)
        ok = (
            packet.primary_intent == case.expected.intent
            and plan.processing_class == case.expected.processing_class
            and plan.core_mode == case.expected.core_mode
        )
        e2e += ok
        if case.critical_underprocessing and not ok:
            crit += 1
        b = by.setdefault(case.category, [0, 0])
        b[0] += ok
        b[1] += 1
    return e2e, len(campaign.cases), crit, by


def main() -> None:
    correct = 0
    for input_text, intent, pclass, mode in HELDOUT:
        packet = extract_semantic_packet(input_text)
        plan = build_processing_plan(packet)
        ok = (
            packet.primary_intent == intent
            and plan.processing_class == pclass
            and plan.core_mode == mode
        )
        correct += ok
        if not ok:
            print(f"  MISS exp={intent}/{pclass}/{mode} "
                  f"act={packet.primary_intent}/{plan.processing_class}/{plan.core_mode}"
                  f" :: {input_text}")
    print(f"held-out P2: {correct}/{len(HELDOUT)}")
    e2e, n, crit, by = measure_campaign()
    print(f"campaign 50: end_to_end {e2e}/{n} = {e2e/n:.2f}  critical {crit}")
    for cat in ("indirect_explanation", "conversation_response", "compound_intent"):
        b = by.get(cat, [0, 0])
        print(f"  {cat}: {b[0]}/{b[1]}")


if __name__ == "__main__":
    main()
