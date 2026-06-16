"""Phase-2 go/no-go probe for the v0.3 learned intent layer.

Trains an averaged-perceptron intent classifier (reusing the Pattern Router
machinery, 7-intent space) on the approved intent corpus, and measures its
intent accuracy on the DISJOINT 50-case campaign and on a within-corpus
held-out split. This answers: does a learned intent layer generalize to the
campaign's conversational distribution better than the v0.2 marker intent
(0.80)? PROBE ONLY — not wired into the adapter, not deployed.
"""

import io
import json
import sys
from collections import Counter, defaultdict
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
DIM = 2048


def predict(text, labels, weights, bias):
    feats = text_features(text, DIM)
    scores = {
        lab: bias.get(lab, 0.0)
        + sum(weights[lab].get(i, 0.0) * v for i, v in feats.items())
        for lab in labels
    }
    return max(labels, key=lambda lab: (scores[lab], lab))


def train(examples):
    labels = sorted({e["intent"] for e in examples})
    rows = [
        {"input_text": e["input"], "route": e["intent"], "quality_score": 5}
        for e in examples
    ]
    weights, bias = _train_averaged_weights(
        rows, labels, DIM, epochs=24, learning_rate=0.35, seed=17
    )
    return labels, weights, bias


def main() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    examples = [
        e for e in corpus["examples"] if e["review_status"] == "approved"
    ]
    print(f"approved training examples: {len(examples)}")

    # within-corpus held-out (1 per intent by stable hash order) — sanity
    import hashlib
    by_intent = defaultdict(list)
    for e in examples:
        by_intent[e["intent"]].append(e)
    holdout, train_set = [], []
    for intent, items in by_intent.items():
        ordered = sorted(items, key=lambda x: hashlib.sha256(
            x["input"].encode()).hexdigest())
        if len(ordered) >= 6:
            holdout.extend(ordered[:2])
            train_set.extend(ordered[2:])
        else:
            train_set.extend(ordered)
    labels, w, b = train(train_set)
    hc = sum(predict(e["input"], labels, w, b) == e["intent"] for e in holdout)
    print(f"within-corpus held-out intent acc: {hc}/{len(holdout)} = "
          f"{hc/len(holdout):.2f}")

    # full model for the campaign measurement
    labels, w, b = train(examples)

    campaign = load_conversation_accumulation(CAMPAIGN)
    correct = 0
    by_cat = defaultdict(lambda: [0, 0])
    confusion = Counter()
    for case in campaign.cases:
        pred = predict(case.input_text, labels, w, b)
        ok = pred == case.expected.intent
        correct += ok
        c = by_cat[case.category]
        c[0] += ok
        c[1] += 1
        if not ok:
            confusion[(case.expected.intent, pred)] += 1
    n = len(campaign.cases)
    print(f"\nLEARNED intent on campaign (disjoint): {correct}/{n} = "
          f"{correct/n:.2f}   [v0.2 marker intent = 0.80]")
    print("by category:")
    for cat, (ok, tot) in sorted(by_cat.items()):
        print(f"  {cat:24s} {ok}/{tot}")
    print("top intent confusions (expected->pred):",
          confusion.most_common(6))


if __name__ == "__main__":
    main()
