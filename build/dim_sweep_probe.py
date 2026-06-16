"""Conversion-efficiency probe: does feature dimension (hash collisions)
bottleneck the learned intent layer? Sweep the hash dimension and measure
learned-alone accuracy on the campaign + within-corpus held-out. PROBE ONLY.
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
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"


def predict(text, dim, labels, weights, bias):
    feats = text_features(text, dim)
    return max(
        labels,
        key=lambda lab: (
            bias.get(lab, 0.0)
            + sum(weights[lab].get(i, 0.0) * v for i, v in feats.items()),
            lab,
        ),
    )


def main() -> None:
    examples = [
        e for e in json.loads(CORPUS.read_text(encoding="utf-8"))["examples"]
        if e["review_status"] == "approved"
    ]
    labels = sorted({e["intent"] for e in examples})
    campaign = load_conversation_accumulation(CAMPAIGN)

    # within-corpus held-out (stable, 2/intent for intents with >=6)
    by_intent = defaultdict(list)
    for e in examples:
        by_intent[e["intent"]].append(e)
    holdout, train_set = [], []
    for items in by_intent.values():
        ordered = sorted(items, key=lambda x: hashlib.sha256(
            x["input"].encode()).hexdigest())
        if len(ordered) >= 6:
            holdout.extend(ordered[:2]); train_set.extend(ordered[2:])
        else:
            train_set.extend(ordered)

    print("dim    | learned-alone campaign | within-corpus held-out")
    for dim in (512, 1024, 2048, 4096, 8192, 16384):
        rows = [
            {"input_text": e["input"], "route": e["intent"], "quality_score": 5}
            for e in train_set
        ]
        w, b = _train_averaged_weights(
            rows, labels, dim, epochs=24, learning_rate=0.35, seed=17
        )
        hc = sum(predict(e["input"], dim, labels, w, b) == e["intent"]
                 for e in holdout)
        # full-corpus model for campaign
        rows_full = [
            {"input_text": e["input"], "route": e["intent"], "quality_score": 5}
            for e in examples
        ]
        wf, bf = _train_averaged_weights(
            rows_full, labels, dim, epochs=24, learning_rate=0.35, seed=17
        )
        cc = sum(
            predict(c.input_text, dim, labels, wf, bf) == c.expected.intent
            for c in campaign.cases
        )
        n = len(campaign.cases)
        print(f"{dim:6d} |   {cc}/{n} = {cc/n:.2f}        | "
              f"{hc}/{len(holdout)} = {hc/len(holdout):.2f}")


if __name__ == "__main__":
    main()
