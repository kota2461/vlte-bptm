"""Distribution-balancing (thinning) probe.

Hypothesis: the learned layer is biased by the dominant class (respond 95,
all curriculum-style Pattern-DB remap). Flattening the per-intent counts —
and, when thinning, preferring to drop curriculum-style examples over the
campaign-matched conversational ones — may improve campaign accuracy.

Selection is CAMPAIGN-BLIND (stable hash order / source label), never by
campaign performance. Re-measures learned-alone + a conservatively gated
hybrid (margin 0.15) per variant. PROBE ONLY.
"""

import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pattern_learning.trainer import _train_averaged_weights, text_features
from semantic_routing.baseline import _intent_scores, extract_semantic_packet
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
DIM = 2048
GATE_MARGIN = 0.15
CONVERSATIONAL = {
    "intent-conversational-v1", "intent-conversational-v2", "intent-explain-v1",
}


def _hash(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def cap(examples, c, source_pref=False):
    by_intent = defaultdict(list)
    for e in examples:
        by_intent[e["intent"]].append(e)
    out = []
    for items in by_intent.values():
        if source_pref:
            # keep conversational first (0), curriculum remap later (1)
            items = sorted(
                items,
                key=lambda e: (
                    0 if e["source"] in CONVERSATIONAL else 1,
                    _hash(e["input"]),
                ),
            )
        else:
            items = sorted(items, key=lambda e: _hash(e["input"]))
        out.extend(items[:c])
    return out


def train(examples):
    labels = sorted({e["intent"] for e in examples})
    rows = [
        {"input_text": e["input"], "route": e["intent"], "quality_score": 5}
        for e in examples
    ]
    w, b = _train_averaged_weights(rows, labels, DIM, 24, 0.35, 17)
    return labels, w, b


def main() -> None:
    full = [
        e for e in json.loads(CORPUS.read_text(encoding="utf-8"))["examples"]
        if e["review_status"] == "approved"
    ]
    campaign = load_conversation_accumulation(CAMPAIGN)

    # marker pass (variant-independent)
    marker = []
    for case in campaign.cases:
        mi = extract_semantic_packet(case.input_text).primary_intent
        _c, ev = _intent_scores(case.input_text)
        marker.append((case.expected.intent, mi, bool(ev)))

    def evaluate(examples):
        labels, w, b = train(examples)

        def learned(text):
            feats = text_features(text, DIM)
            scored = sorted(
                (b.get(l, 0.0)
                 + sum(w[l].get(i, 0.0) * v for i, v in feats.items()), l)
                for l in labels
            )
            top_s, top_l = scored[-1]
            margin = top_s - scored[-2][0] if len(scored) > 1 else top_s
            return top_l, margin

        la = gh = 0
        for (exp, mi, fired), case in zip(marker, campaign.cases):
            li, mg = learned(case.input_text)
            la += li == exp
            hyb = mi if fired else (li if mg >= GATE_MARGIN else mi)
            gh += hyb == exp
        n = len(campaign.cases)
        return len(examples), la / n, gh / n

    variants = {
        "baseline (408)": full,
        "flat-to-min 32 (hash)": cap(full, 32),
        "cap 40 (hash)": cap(full, 40),
        "cap 40 (source-pref)": cap(full, 40, source_pref=True),
        "cap 50 (source-pref)": cap(full, 50, source_pref=True),
    }
    print(f"marker-alone intent: "
          f"{sum(e==m for e,m,_ in marker)/len(marker):.2f}  "
          f"(gated hybrid margin={GATE_MARGIN})")
    print("variant                  | n_train | learned-alone | gated-hybrid")
    for name, ex in variants.items():
        n, la, gh = evaluate(ex)
        print(f"  {name:24s}|  {n:4d}   |    {la:.2f}      |    {gh:.2f}")


if __name__ == "__main__":
    main()
