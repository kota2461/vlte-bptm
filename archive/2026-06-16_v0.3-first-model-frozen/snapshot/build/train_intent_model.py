"""Train + save the v0.3 learned intent model from the approved corpus.

Reads data/intent_training_corpus_v1.json (approved examples only), trains
the averaged-perceptron IntentModel, saves to build/intent_model_v1.json, and
prints a summary + the learned-alone campaign accuracy (informational).
"""

import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.intent_model import IntentModel, load_intent_corpus
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
OUT = ROOT / "build" / "intent_model_v1.json"


def main() -> None:
    examples = load_intent_corpus(CORPUS)
    model = IntentModel.train(examples)
    model.save(OUT)
    print(f"trained intent model -> {OUT.name}")
    print("examples:", len(examples),
          "| by_intent:", dict(sorted(Counter(e["intent"] for e in examples).items())))

    reloaded = IntentModel.load(OUT)
    campaign = load_conversation_accumulation(CAMPAIGN)
    correct = sum(
        reloaded.predict(c.input_text).intent == c.expected.intent
        for c in campaign.cases
    )
    n = len(campaign.cases)
    print(f"learned-alone campaign intent (informational): {correct}/{n} = "
          f"{correct/n:.2f}")


if __name__ == "__main__":
    main()
