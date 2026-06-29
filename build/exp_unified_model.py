"""Experiment: does feeding marker signals as features lift the learned model?

Isolated (touches no production code). Trains an averaged perceptron on the
existing approved 739-example corpus with two feature sets and compares intent
accuracy on the held-out validation split (0 overlap with corpus, verified):

  baseline_features  - text_features only (reproduces deployed model_only ~0.68)
  unified_features   - text_features + the markers' per-intent vote as clean,
                       collision-free features (indices >= DIM)

The goal is to see whether a single learned model can absorb the marker strength
(markers_only = 0.964 on validation) while still generalising via n-grams --
i.e. whether "leaning on the model" is viable with existing data.
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import intent_model as im  # noqa: E402
from semantic_routing.baseline import INTENT_MARKERS, _find_markers  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso  # noqa: E402
from semantic_routing.semantic_packet import INTENTS  # noqa: E402

DIM = im.DEFAULT_DIMENSION
EPOCHS = im.DEFAULT_EPOCHS
LR = 1.0
SEED = 13
CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
BENCH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
OUT = ROOT / "build" / "exp_unified_model_v1.json"

# Clean, collision-free feature indices for the markers' per-intent vote.
_MARKER_INTENTS = sorted(INTENT_MARKERS)
_MARKER_FEATURE_INDEX = {intent: DIM + i for i, intent in enumerate(_MARKER_INTENTS)}


def _marker_votes(text: str) -> dict[int, float]:
    feats: dict[int, float] = {}
    for intent, markers in INTENT_MARKERS.items():
        if _find_markers(text, markers):
            feats[_MARKER_FEATURE_INDEX[intent]] = 1.0
    return feats


def _features(text: str, *, with_markers: bool) -> dict[int, float]:
    feats = dict(im.text_features(text, DIM))
    if with_markers:
        feats.update(_marker_votes(text))
    return feats


def _train(pairs, labels, *, with_markers: bool):
    feats_cache = {t: _features(t, with_markers=with_markers) for t, _ in pairs}
    weights = {l: defaultdict(float) for l in labels}
    bias = {l: 0.0 for l in labels}
    cum_w = {l: defaultdict(float) for l in labels}
    cum_b = {l: 0.0 for l in labels}
    step = 1
    rng = random.Random(SEED)
    for _ in range(EPOCHS):
        order = list(pairs)
        rng.shuffle(order)
        for text, gold in order:
            feats = feats_cache[text]
            scores = {l: bias[l] + sum(weights[l].get(i, 0.0) * v for i, v in feats.items()) for l in labels}
            pred = max(labels, key=lambda l: (scores[l], l))
            if pred != gold:
                for i, v in feats.items():
                    weights[gold][i] += LR * v
                    weights[pred][i] -= LR * v
                    cum_w[gold][i] += step * LR * v
                    cum_w[pred][i] -= step * LR * v
                bias[gold] += LR
                bias[pred] -= LR
                cum_b[gold] += step * LR
                cum_b[pred] -= step * LR
            step += 1
    avg_w = {l: {i: w - cum_w[l][i] / step for i, w in wl.items() if w or cum_w[l][i]} for l, wl in weights.items()}
    avg_b = {l: bias[l] - cum_b[l] / step for l in labels}
    return avg_w, avg_b


def _predict(text, weights, bias, labels, *, with_markers: bool) -> str:
    feats = _features(text, with_markers=with_markers)
    scores = {l: bias.get(l, 0.0) + sum(weights.get(l, {}).get(i, 0.0) * v for i, v in feats.items()) for l in labels}
    return max(labels, key=lambda l: (scores[l], l))


def _acc(cases, weights, bias, labels, *, with_markers: bool):
    ok = sum(1 for c in cases if _predict(c["input"], weights, bias, labels, with_markers=with_markers) == c["expected"]["primary_intent"])
    return round(ok / len(cases), 6) if cases else 0.0


def main() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    ex = corpus.get("examples", corpus)
    pairs = [(e["input"], e["intent"]) for e in ex if e.get("review_status") == "approved" and e["intent"] in INTENTS]
    labels = sorted({i for _, i in pairs})

    bench = json.loads(BENCH.read_text(encoding="utf-8"))
    val = [c for c in bench["cases"] if c["split"] == "validation"]
    train = [c for c in bench["cases"] if c["split"] == "train"]

    out = {
        "schema_version": "exp-unified-model.v1",
        "generated_at": reproducible_now_iso(),
        "train_corpus_size": len(pairs),
        "labels": labels,
        "results": {},
    }
    for tag, wm in (("baseline_features", False), ("unified_features", True)):
        w, b = _train(pairs, labels, with_markers=wm)
        out["results"][tag] = {
            "validation_intent_accuracy": _acc(val, w, b, labels, with_markers=wm),
            "train_split_intent_accuracy": _acc(train, w, b, labels, with_markers=wm),
        }
    out["reference"] = {"markers_only_validation": 0.964286, "deployed_model_only_validation": 0.678571}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"train_corpus_size": out["train_corpus_size"], "results": out["results"], "reference": out["reference"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
