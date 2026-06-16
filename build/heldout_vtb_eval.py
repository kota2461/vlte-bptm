"""Held-out generalization check for the verify_then_build fix.

These prompts are authored fresh (NOT copied from the 50-case campaign) to
test whether the marker/sequencing fix generalizes rather than fits the
campaign. Includes guard cases (pure build / verify / explain / respond /
summarize / explore) to catch over-triggering. Also re-measures the 50-case
campaign for the headline numbers. MEASUREMENT ONLY.
"""

import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import build_processing_plan, extract_semantic_packet
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"

# (input, intent, processing_class, core_mode, is_vtb_critical_target)
HELDOUT = [
    # verify-then-build (build deliverable + verify prereq) -> verified/vertical
    ("数値が仕様と合っているか調べてから、移行スクリプトを書いてください",
     "build", "verified", "vertical", True),
    ("前提が正しいかチェックしたうえで、実装の段取りを組んでください",
     "build", "verified", "vertical", True),
    ("Make sure the schema is valid, then produce the migration steps.",
     "build", "verified", "vertical", True),
    ("計算が合っているか確かめて、合っていれば請求書を作成してください",
     "build", "verified", "vertical", True),
    ("仕様に違反していないか確認したうえで、対応案を用意してください",
     "build", "verified", "vertical", True),
    # pure build (no verify) -> standard/horizontal  [guard: not verified]
    ("新しい画面の実装タスクを洗い出して並べてください",
     "build", "standard", "horizontal", False),
    ("デプロイの作業手順を作ってください",
     "build", "standard", "horizontal", False),
    # pure verify -> verified/vertical  [guard: stays verify, not build]
    ("この集計が正しいか検算してください",
     "verify", "verified", "vertical", False),
    ("提出されたコードが要件を満たすか確認してください",
     "verify", "verified", "vertical", False),
    # review-as-verify (idiomatic "review" requests)
    ("この企画書をレビューしてほしいです",
     "verify", "verified", "vertical", False),
    ("Please review this design and point out the risks.",
     "verify", "verified", "vertical", False),
    # guards against over-triggering build/verify
    ("この設計の狙いを説明してください",
     "explain", "economy", "horizontal", False),
    ("HTTPって何の略ですか",
     "respond", "economy", "horizontal", False),
    ("この議事録を3行でまとめてください",
     "summarize", "economy", "horizontal", False),
    ("保存方式の候補をいくつか比較してください",
     "explore", "deep", "hybrid", False),
]


def measure(cases):
    correct = 0
    crit_hit = 0
    crit_total = 0
    misses = []
    for input_text, intent, pclass, mode, is_crit in cases:
        packet = extract_semantic_packet(input_text)
        plan = build_processing_plan(packet)
        ok = (
            packet.primary_intent == intent
            and plan.processing_class == pclass
            and plan.core_mode == mode
        )
        correct += ok
        if is_crit:
            crit_total += 1
            crit_hit += ok
        if not ok:
            misses.append((input_text, f"{intent}/{pclass}/{mode}",
                           f"{packet.primary_intent}/{plan.processing_class}/{plan.core_mode}"))
    return correct, len(cases), crit_hit, crit_total, misses


def measure_campaign():
    campaign = load_conversation_accumulation(CAMPAIGN)
    e2e = 0
    crit = 0
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
    return e2e, len(campaign.cases), crit


def main() -> None:
    c, n, ch, ct, misses = measure(HELDOUT)
    print(f"held-out: {c}/{n}  (vtb-target {ch}/{ct})")
    for inp, exp, act in misses:
        print(f"  MISS exp={exp} act={act} :: {inp}")
    e2e, total, crit = measure_campaign()
    print(f"campaign 50: end_to_end {e2e}/{total} = {e2e/total:.2f}  "
          f"critical_underprocessing {crit}")


if __name__ == "__main__":
    main()
