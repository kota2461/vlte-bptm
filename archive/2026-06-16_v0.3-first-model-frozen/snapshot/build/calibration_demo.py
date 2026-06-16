"""Show the abstention policy in action: raw route vs effective route.

High-confidence inputs pass through; sub-threshold inputs (where repeated
k-fold accuracy is < 0.5) fall back to clarify as an abstention policy.
This demo does not count fallback as a corrected label. None of these
sentences are in the curriculum.
"""

import io
import sys

from pattern_learning.trainer import RouterModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

INPUTS = [
    # confident, should pass through unchanged
    "3+5を計算してください",
    "二次関数 y=x^2-4x+3 の頂点を求めてください",
    "こんにちは",
    "この証明を短く要約してください",
    # low-confidence borderlines that previously misrouted
    "別の角度から解いてみてください",
    "他の表現も提案してください",
    "違う解法も検討してみてください",
    "何を求める問題か確認してください",
    "もっと良い方法を探してください",
]


def main() -> None:
    model = RouterModel.load("build/pattern_router_model.json")
    calib = model.metadata.get("calibration", {})
    print(
        f"threshold={calib.get('decision_threshold')} "
        f"fallback={calib.get('fallback_route')} "
        f"kfold_acc={calib.get('kfold_accuracy')}\n"
    )
    abstained = 0
    for text in INPUTS:
        p = model.predict(text)
        abstained += p.low_confidence
        tag = "  -> CLARIFY" if p.low_confidence else ""
        print(
            f"raw={p.route:9} eff={p.effective_route:9} "
            f"conf={p.confidence:.3f} cal={p.calibrated_confidence:.3f}"
            f"{tag}  {text}"
        )
    print(f"\nabstained {abstained}/{len(INPUTS)} to clarify")


if __name__ == "__main__":
    main()
