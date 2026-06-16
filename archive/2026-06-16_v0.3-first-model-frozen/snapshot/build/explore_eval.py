"""Behavioral evaluation for the explore-route reinforcement (weakness #1).

Three honest views, none of which trains on what it measures:
  [holdout]  rebuild the *measurement* model (train split only) and score the
             validation holdout — the real generalization estimate.
  [battery]  unseen sentences, disjoint from the curriculum, covering explore
             generalization plus regression guards for the other routes.

Run after an explicit train. Console may mojibake CJK; routes stay readable.
"""

import io
import sys

from pattern_learning.database import PatternDatabase
from pattern_learning.trainer import (
    RouterModel,
    _operator_priors,
    _split_examples,
    _train_averaged_weights,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MODEL = "build/pattern_router_model.json"
DB = "data/pattern_lab.db"

# Unseen by construction (not present in either curriculum).
BATTERY = [
    ("explore", "別の角度から解いてみてください"),
    ("explore", "他の表現も提案してください"),
    ("explore", "もっと別のやり方はないか探してみて"),
    ("explore", "答えが10になる別のかけ算を考えて"),
    ("explore", "他のアプローチをいくつか挙げて"),
    ("explore", "違う解法も検討してみてください"),
    ("respond", "3+5を計算してください"),
    ("respond", "二次関数の頂点を求めてください"),
    ("respond", "こんにちは"),
    ("respond", "ありがとうございます"),
    ("clarify", "条件が足りないので質問してください"),
    ("clarify", "何を求める問題か確認してください"),
    ("verify", "この計算が正しいか検算してください"),
    ("summarize", "この証明を短く要約してください"),
    ("build", "解答の手順を組み立ててください"),
]


def main() -> None:
    db = PatternDatabase(DB)
    examples = db.training_examples()
    labels = sorted({e["route"] for e in examples})
    train, validation = _split_examples(examples)

    # Honest holdout: a measurement model that never saw the validation set.
    weights, bias = _train_averaged_weights(train, labels, 2048, 40, 0.35, 17)
    measurement = RouterModel(labels, 2048, weights, bias,
                              _operator_priors(examples), {})
    by_route: dict[str, list[int]] = {}
    vwrong = []
    for e in validation:
        got = measurement.predict(e["input_text"]).route
        by_route.setdefault(e["route"], [0, 0])
        by_route[e["route"]][1] += 1
        if got == e["route"]:
            by_route[e["route"]][0] += 1
        else:
            vwrong.append((e["route"], got, e["input_text"]))
    vok = sum(c for c, _ in by_route.values())
    print(f"[holdout] {vok}/{len(validation)} correct (measurement model)")
    for route in sorted(by_route):
        c, n = by_route[route]
        print(f"    {route:9} {c}/{n}")
    for exp, got, text in vwrong:
        print(f"    MISS expect={exp:9} got={got:9} {text}")

    # Unseen battery against the deployed (all-data) model.
    deployed = RouterModel.load(MODEL)
    correct = 0
    print("[battery] unseen generalization + regression (deployed model)")
    for expected, text in BATTERY:
        pred = deployed.predict(text)
        ok = pred.route == expected
        correct += ok
        print(
            f"    {'ok  ' if ok else 'MISS'} expect={expected:9} "
            f"got={pred.route:9} conf={pred.confidence:.3f}  {text}"
        )
    print(f"[battery] {correct}/{len(BATTERY)} correct")


if __name__ == "__main__":
    main()
