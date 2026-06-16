"""Unseen-English generalization battery after Round 2 (10 approved).

None of these prompts exist in the Pattern DB; this measures whether the
English non-respond reinforcement generalizes beyond its own phrasings.
"""

import io
import sys

from pattern_learning.trainer import RouterModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BATTERY = (
    ("Please check if this answer is right.", "verify"),
    ("Verify that the totals in this table add up correctly.", "verify"),
    ("Make a step-by-step plan for the database migration.", "build"),
    ("Put together an ordered task list for this project.", "build"),
    ("Some information is missing, so ask me about it.", "clarify"),
    ("Ask me which file you should look at first.", "clarify"),
    ("Sum up this report in one sentence.", "summarize"),
    ("Give me a short summary of the discussion.", "summarize"),
    ("Suggest several alternative designs for this screen.", "explore"),
    ("What are some other ways to solve this problem?", "explore"),
    ("What is 12 plus 7?", "respond"),
    ("Explain what an API is.", "respond"),
)


def main() -> None:
    model = RouterModel.load("build/pattern_router_model.json")
    correct = 0
    for text, expected in BATTERY:
        prediction = model.predict(text)
        ok = prediction.route == expected
        correct += ok
        mark = "OK " if ok else "MISS"
        print(f"{mark} [{expected:9s}->{prediction.route:9s}] {text}")
    print(f"unseen English battery: {correct}/{len(BATTERY)}")


if __name__ == "__main__":
    main()
