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

from semantic_routing import baseline as _bl  # noqa: E402
from semantic_routing import intent_model as im  # noqa: E402
from semantic_routing.baseline import INTENT_MARKERS, _find_markers, _intent_scores  # noqa: E402
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

# v2: the markers' full graded per-intent score + auxiliary signal flags.
_SCORE_INDEX = {intent: DIM + 100 + i for i, intent in enumerate(_MARKER_INTENTS)}
_AUX_MARKERS = [
    ("terminal_build", "TERMINAL_BUILD_MARKER"),
    ("terminal_summary", "TERMINAL_SUMMARY_MARKER"),
    ("terminal_explain", "TERMINAL_EXPLAIN_MARKER"),
    ("multiple_intents", "MULTIPLE_INTENT_MARKER"),
    ("current", "CURRENT_MARKER"),
    ("current_blocker", "CURRENT_CONTEXT_BLOCKER"),
    ("unverified", "UNVERIFIED_MARKER"),
    ("short", "SHORT_MARKER"),
    ("long", "LONG_MARKER"),
]
_AUX_INDEX = {name: DIM + 200 + i for i, (name, _attr) in enumerate(_AUX_MARKERS)}


def _marker_votes(text: str) -> dict[int, float]:
    feats: dict[int, float] = {}
    for intent, markers in INTENT_MARKERS.items():
        if _find_markers(text, markers):
            feats[_MARKER_FEATURE_INDEX[intent]] = 1.0
    return feats


def _marker_rich(text: str) -> dict[int, float]:
    """v2: binary intent votes + graded intent scores + auxiliary marker flags."""
    feats = _marker_votes(text)
    candidates, _ = _intent_scores(text)
    for cand in candidates:
        if cand.intent in _SCORE_INDEX:
            feats[_SCORE_INDEX[cand.intent]] = float(cand.confidence)
    for name, attr in _AUX_MARKERS:
        marker = getattr(_bl, attr, None)
        if marker is not None and _find_markers(text, (marker,)):
            feats[_AUX_INDEX[name]] = 1.0
    return feats


def _features(text: str, *, mode: str) -> dict[int, float]:
    feats = dict(im.text_features(text, DIM))
    if mode == "markers":
        feats.update(_marker_votes(text))
    elif mode == "rich":
        feats.update(_marker_rich(text))
    return feats


def _train(pairs, labels, *, mode: str):
    feats_cache = {t: _features(t, mode=mode) for t, _ in pairs}
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


def _predict(text, weights, bias, labels, *, mode: str) -> str:
    feats = _features(text, mode=mode)
    scores = {l: bias.get(l, 0.0) + sum(weights.get(l, {}).get(i, 0.0) * v for i, v in feats.items()) for l in labels}
    return max(labels, key=lambda l: (scores[l], l))


def _acc(cases, weights, bias, labels, *, mode: str):
    ok = sum(1 for c in cases if _predict(c["input"], weights, bias, labels, mode=mode) == c["expected"]["primary_intent"])
    return round(ok / len(cases), 6) if cases else 0.0


def _heldout_inputs(bench) -> set[str]:
    """Inputs that must never be trained on: benchmark validation+sealed and all
    sealed_vN fixtures."""
    out = {c["input"] for c in bench["cases"] if c["split"] in ("validation", "sealed")}
    for p in sorted((ROOT / "tests" / "fixtures").glob("pattern_language_sealed_v*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d.get("cases", []):
            if "input" in c:
                out.add(c["input"])
    return out


def _extra_pairs(have: set[str], heldout: set[str], bench) -> list[tuple[str, str]]:
    """Correct (input, intent) pairs from human-reviewed v6-9 benchmark fixtures
    + the benchmark train split, excluding anything held-out or already in corpus."""
    cand: list[tuple[str, str]] = []
    for f in sorted((ROOT / "tests" / "fixtures").glob("v[6789]_*benchmark*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for c in d.get("cases", []):
            inp = c.get("input")
            exp = (c.get("expected") or {}).get("primary_intent")
            if inp and exp:
                cand.append((inp, exp))
    cand += [(c["input"], c["expected"]["primary_intent"]) for c in bench["cases"] if c["split"] == "train"]
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for i, lab in cand:
        if i in heldout or i in have or i in seen or lab not in INTENTS:
            continue
        seen.add(i)
        out.append((i, lab))
    return out


def _kfold(pairs, labels, *, mode: str, k: int = 5) -> dict:
    rng = random.Random(SEED)
    items = list(pairs)
    rng.shuffle(items)
    folds = [items[i::k] for i in range(k)]
    accs = []
    for i in range(k):
        test = folds[i]
        tr = [p for j in range(k) if j != i for p in folds[j]]
        flabels = sorted({l for _, l in tr})
        w, b = _train(tr, flabels, mode=mode)
        ok = sum(1 for t, gold in test if _predict(t, w, b, flabels, mode=mode) == gold)
        accs.append(ok / len(test) if test else 0.0)
    return {"mean": round(sum(accs) / len(accs), 6), "folds": [round(a, 6) for a in accs]}


def main() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    ex = corpus.get("examples", corpus)
    base_pairs = [(e["input"], e["intent"]) for e in ex if e.get("review_status") == "approved" and e["intent"] in INTENTS]

    bench = json.loads(BENCH.read_text(encoding="utf-8"))
    val = [c for c in bench["cases"] if c["split"] == "validation"]
    train = [c for c in bench["cases"] if c["split"] == "train"]

    heldout = _heldout_inputs(bench)
    have = {i for i, _ in base_pairs}
    extra = _extra_pairs(have, heldout, bench)
    # leakage assertion: no training input may be in the held-out set
    assert not ({i for i, _ in base_pairs + extra} & heldout), "LEAKAGE: training overlaps held-out"
    pairs_plus = base_pairs + extra
    labels = sorted({i for _, i in pairs_plus})

    out = {
        "schema_version": "exp-unified-model.v1",
        "generated_at": reproducible_now_iso(),
        "base_corpus_size": len(base_pairs),
        "extra_pairs_added": len(extra),
        "extra_by_intent": {k: sum(1 for _, l in extra if l == k) for k in sorted({l for _, l in extra})},
        "labels": labels,
        "results": {},
    }
    datasets = {"corpus_only": base_pairs, "corpus_plus_assets": pairs_plus}
    for dtag, dpairs in datasets.items():
        for ftag, mode in (("baseline_features", "plain"), ("unified_features", "markers"), ("unified_rich", "rich")):
            w, b = _train(dpairs, labels, mode=mode)
            out["results"][f"{dtag}__{ftag}"] = {
                "validation_intent_accuracy": _acc(val, w, b, labels, mode=mode),
                "train_split_intent_accuracy": _acc(train, w, b, labels, mode=mode),
            }
    # k-fold CV on the combined pool: a more robust (still in-distribution)
    # generalization estimate than a single 28-case validation. Guards against
    # reading too much into a small-set 1.000.
    out["kfold5_combined_pool"] = {
        "unified_features": _kfold(pairs_plus, labels, mode="markers", k=5),
        "baseline_features": _kfold(pairs_plus, labels, mode="plain", k=5),
    }
    out["reference"] = {"markers_only_validation": 0.964286, "deployed_model_only_validation": 0.678571}
    out["honesty_note"] = (
        "validation is 28 cases from the same benchmark family as the added "
        "assets; a 1.000 there is distribution-overfit, not proven real-world "
        "generalization. True confirmation needs a fresh sealed set the model "
        "has seen nothing similar to. kfold5 is a more robust in-distribution "
        "estimate."
    )
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"base_corpus_size": out["base_corpus_size"], "extra_pairs_added": out["extra_pairs_added"], "extra_by_intent": out["extra_by_intent"], "results": out["results"], "reference": out["reference"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
