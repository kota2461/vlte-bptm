"""Build the intent-model CANDIDATE with an off-campaign k-fold dev metric.

Trains the averaged-perceptron IntentModel on the approved corpus (disjoint
from the measurement campaign), records a stratified k-fold accuracy in
metadata.metrics so the deployment gate's improvement check has a baseline,
and writes build/intent_model_v1_candidate.json. Does NOT deploy.
"""

import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.intent_model import IntentModel, load_intent_corpus
from semantic_routing.reproducibility import reproducible_now_iso
from semantic_routing.intent_deployment import evaluate_intent_kfold, DEFAULT_CANDIDATE

CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
OUT = ROOT / DEFAULT_CANDIDATE


def main() -> None:
    examples = load_intent_corpus(CORPUS)
    metrics = evaluate_intent_kfold(examples)
    model = IntentModel.train(examples)
    model.metadata["metrics"] = metrics
    model.metadata["trained_at"] = reproducible_now_iso()
    model.save(OUT)

    print(f"candidate -> {OUT.name}")
    print("examples:", len(examples),
          "| by_intent:", dict(sorted(Counter(e["intent"] for e in examples).items())))
    print("k-fold dev metric (off-campaign):",
          {k: (round(v, 4) if isinstance(v, float) else v) for k, v in metrics.items()})


if __name__ == "__main__":
    main()
