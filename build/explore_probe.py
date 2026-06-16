"""Direct probe of the handover's documented explore borderline cases plus
the respond-bleed suspects, written to a UTF-8 file to dodge console mojibake.
"""

import io
import sys

from pattern_learning.trainer import RouterModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROBES = [
    # handover-documented explore borderline cases
    ("explore", "8になる別のたし算を考えてください"),
    ("explore", "答えが8になる別の足し算を挙げてください"),
    ("explore", "他のやり方も考えてみてください"),
    ("explore", "別のアプローチを探してください"),
    ("explore", "他の解き方はありますか"),
    ("explore", "もっと良い方法を探してください"),
    # respond-bleed suspects (must stay respond)
    ("respond", "sin30°+cos60° の値を計算してください"),
    ("respond", "7×6を計算してください"),
    ("respond", "二次関数 y=x^2-4x+3 の頂点と最小値を求めてください"),
    ("respond", "0という数の意味を説明してください"),
]


def main() -> None:
    model = RouterModel.load("build/pattern_router_model.json")
    ok = 0
    for expected, text in PROBES:
        pred = model.predict(text)
        hit = pred.route == expected
        ok += hit
        print(
            f"{'ok  ' if hit else 'MISS'} expect={expected:8} "
            f"got={pred.route:8} conf={pred.confidence:.3f}  {text}"
        )
    print(f"{ok}/{len(PROBES)} correct")


if __name__ == "__main__":
    main()
