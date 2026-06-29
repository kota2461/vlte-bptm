"""Honest estimate: do the 25 weak-point candidate rows move the model?

Compares base corpus vs base+weakpoint on the held-out validation split
(gate-off, plus explain-only and English-only breakdowns) and a k-fold5 CV.
Treats the candidate rows as if-approved FOR ESTIMATION ONLY -- they remain
review_status=candidate in the draft file. Honest read, not a 1.000 chase.
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
from semantic_routing.semantic_packet import INTENTS  # noqa: E402

DIM = im.DEFAULT_DIMENSION
EPOCHS = im.DEFAULT_EPOCHS
SEED = 13
_MK = {intent: DIM + i for i, intent in enumerate(sorted(INTENT_MARKERS))}


def _feats(text):
    f = dict(im.text_features(text, DIM))
    for intent, markers in INTENT_MARKERS.items():
        if _find_markers(text, markers):
            f[_MK[intent]] = 1.0
    return f


def _train(pairs, labels):
    cache = {t: _feats(t) for t, _ in pairs}
    w = {l: defaultdict(float) for l in labels}
    b = {l: 0.0 for l in labels}
    cw = {l: defaultdict(float) for l in labels}
    cb = {l: 0.0 for l in labels}
    step = 1
    rng = random.Random(SEED)
    for _ in range(EPOCHS):
        order = list(pairs)
        rng.shuffle(order)
        for t, gold in order:
            fe = cache[t]
            sc = {l: b[l] + sum(w[l].get(i, 0.0) * v for i, v in fe.items()) for l in labels}
            pred = max(labels, key=lambda l: (sc[l], l))
            if pred != gold:
                for i, v in fe.items():
                    w[gold][i] += v; w[pred][i] -= v
                    cw[gold][i] += step * v; cw[pred][i] -= step * v
                b[gold] += 1; b[pred] -= 1
                cb[gold] += step; cb[pred] -= step
            step += 1
    aw = {l: {i: x - cw[l][i] / step for i, x in wl.items() if x or cw[l][i]} for l, wl in w.items()}
    ab = {l: b[l] - cb[l] / step for l in labels}
    return aw, ab


def _pred(text, w, b, labels):
    fe = _feats(text)
    sc = {l: b.get(l, 0.0) + sum(w.get(l, {}).get(i, 0.0) * v for i, v in fe.items()) for l in labels}
    return max(labels, key=lambda l: (sc[l], l))


def _acc(cases, w, b, labels, *, only=None, lang=None):
    sel = [c for c in cases if (only is None or c["expected"]["primary_intent"] == only) and (lang is None or c.get("language") == lang)]
    if not sel:
        return None
    ok = sum(1 for c in sel if _pred(c["input"], w, b, labels) == c["expected"]["primary_intent"])
    return round(ok / len(sel), 4)


def _kfold(pairs, labels, k=5):
    rng = random.Random(SEED); items = list(pairs); rng.shuffle(items)
    folds = [items[i::k] for i in range(k)]; accs = []
    for i in range(k):
        test = folds[i]; tr = [p for j in range(k) if j != i for p in folds[j]]
        fl = sorted({l for _, l in tr}); w, b = _train(tr, fl)
        accs.append(sum(1 for t, g in test if _pred(t, w, b, fl) == g) / len(test))
    return round(sum(accs) / len(accs), 4)


def main():
    corpus = json.loads((ROOT / "data" / "intent_training_corpus_v1.json").read_text(encoding="utf-8"))
    base = [(e["input"], e["intent"]) for e in corpus["examples"] if e.get("review_status") == "approved" and e["intent"] in INTENTS]
    wp = json.loads((ROOT / "build" / "weakpoint_explain_english_corpus_candidates_v1.json").read_text(encoding="utf-8"))
    wp_pairs = [(r["input"], r["intent"]) for r in wp["rows"] if r["intent"] in INTENTS]
    plus = base + wp_pairs

    bench = json.loads((ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json").read_text(encoding="utf-8"))
    val = [c for c in bench["cases"] if c["split"] == "validation"]

    out = {"base_size": len(base), "weakpoint_added": len(wp_pairs)}
    for tag, pairs in (("base", base), ("base_plus_weakpoint", plus)):
        labels = sorted({l for _, l in pairs})
        w, b = _train(pairs, labels)
        out[tag] = {
            "validation_intent_acc": _acc(val, w, b, labels),
            "validation_explain_acc": _acc(val, w, b, labels, only="explain"),
            "validation_english_acc": _acc(val, w, b, labels, lang="en"),
            "kfold5": _kfold(pairs, labels),
        }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
