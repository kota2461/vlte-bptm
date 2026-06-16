"""5-fold honest reliability analysis for the router (weakness #2).

Each approved pattern is predicted by a model that did NOT train on it, so
the (signal, correct) pairs are an honest estimate of how trustworthy a
prediction is. We compare two abstention signals — softmax confidence and
the top1-top2 raw-score margin — and print reliability tables plus the
abstain/keep trade-off at candidate thresholds. Output informs the decision
threshold; it does not itself change any model.
"""

import hashlib
import io
import sys
from collections import defaultdict

from pattern_learning.database import PatternDatabase
from pattern_learning.trainer import (
    RouterModel,
    _operator_priors,
    _train_averaged_weights,
    text_features,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIM, EPOCHS, LR, SEED, FOLDS = 2048, 40, 0.35, 17, 5


def _fold(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest, 16) % FOLDS


def _scored(model: RouterModel, text: str):
    pred = model.predict(text)
    ordered = sorted(pred.scores.values(), reverse=True)
    margin = ordered[0] - ordered[1] if len(ordered) > 1 else ordered[0]
    return pred.route, pred.confidence, margin


def main() -> None:
    examples = PatternDatabase("data/pattern_lab.db").training_examples()
    labels = sorted({e["route"] for e in examples})

    # Stratified folds: round-robin within each route by hash order.
    folds: dict[int, list] = defaultdict(list)
    by_route: dict[str, list] = defaultdict(list)
    for e in examples:
        by_route[e["route"]].append(e)
    for route_examples in by_route.values():
        for i, e in enumerate(
            sorted(route_examples, key=lambda x: _fold(x["input_text"]))
        ):
            folds[i % FOLDS].append(e)

    points = []  # (route_correct, confidence, margin, expected, predicted)
    for f in range(FOLDS):
        held = folds[f]
        train = [e for g in range(FOLDS) if g != f for e in folds[g]]
        weights, bias = _train_averaged_weights(
            train, labels, DIM, EPOCHS, LR, SEED
        )
        model = RouterModel(labels, DIM, weights, bias, {}, {})
        for e in held:
            got, conf, margin = _scored(model, e["input_text"])
            points.append((got == e["route"], conf, margin, e["route"], got))

    n = len(points)
    overall = sum(p[0] for p in points) / n
    print(f"k-fold honest accuracy: {overall:.3f}  (n={n})")

    for name, idx in (("confidence", 1), ("margin", 2)):
        print(f"\n[{name}] reliability (sorted, 6 bins)")
        ordered = sorted(points, key=lambda p: p[idx])
        size = max(1, n // 6)
        for b in range(0, n, size):
            chunk = ordered[b:b + size]
            if not chunk:
                continue
            acc = sum(c[0] for c in chunk) / len(chunk)
            lo, hi = chunk[0][idx], chunk[-1][idx]
            print(
                f"    {name}[{lo:.3f}..{hi:.3f}] n={len(chunk):2d} "
                f"acc={acc:.3f}"
            )

    print("\n[trade-off] abstain (->clarify) when signal < threshold")
    for name, idx in (("confidence", 1), ("margin", 2)):
        vals = sorted(p[idx] for p in points)
        print(f"  by {name}:")
        for q in (0.1, 0.2, 0.3, 0.4, 0.5):
            thr = vals[int(q * n)]
            below = [p for p in points if p[idx] < thr]
            above = [p for p in points if p[idx] >= thr]
            # A correct abstention = below-threshold AND would-have-been-wrong.
            saved = sum(1 for p in below if not p[0])
            lost = sum(1 for p in below if p[0])  # correct, wrongly abstained
            kept_acc = (sum(p[0] for p in above) / len(above)) if above else 0
            print(
                f"    thr={thr:.3f} (q{int(q*100)}) abstain={len(below):3d} "
                f"saved_wrong={saved:3d} lost_correct={lost:3d} "
                f"kept_acc={kept_acc:.3f}"
            )


if __name__ == "__main__":
    main()
