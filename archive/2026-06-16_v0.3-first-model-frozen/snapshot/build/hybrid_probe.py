"""Decisive test: does the HYBRID (markers when they fire, learned layer only
on no-match) beat markers-alone (0.80) on the campaign intent?

Measuring the learned layer alone (0.58) understates the hybrid: the hybrid
keeps the precise marker decision wherever a marker fires and only consults
the learned layer where markers are silent. This probe measures all three.
PROBE ONLY.
"""

import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import json

from pattern_learning.trainer import _train_averaged_weights, text_features
from semantic_routing.baseline import _intent_scores, extract_semantic_packet
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
DIM = 2048


def main() -> None:
    examples = [
        e for e in json.loads(CORPUS.read_text(encoding="utf-8"))["examples"]
        if e["review_status"] == "approved"
    ]
    labels = sorted({e["intent"] for e in examples})
    rows = [
        {"input_text": e["input"], "route": e["intent"], "quality_score": 5}
        for e in examples
    ]
    weights, bias = _train_averaged_weights(
        rows, labels, DIM, epochs=24, learning_rate=0.35, seed=17
    )

    def learned_intent(text):
        feats = text_features(text, DIM)
        scores = {
            lab: bias.get(lab, 0.0)
            + sum(weights[lab].get(i, 0.0) * v for i, v in feats.items())
            for lab in labels
        }
        return max(labels, key=lambda lab: (scores[lab], lab))

    campaign = load_conversation_accumulation(CAMPAIGN)
    marker_ok = learned_ok = hybrid_ok = 0
    rescued = broke = 0
    for case in campaign.cases:
        exp = case.expected.intent
        marker_i = extract_semantic_packet(case.input_text).primary_intent
        _cands, evidence = _intent_scores(case.input_text)
        markers_fired = len(evidence) > 0
        learned_i = learned_intent(case.input_text)
        hybrid_i = marker_i if markers_fired else learned_i

        marker_ok += marker_i == exp
        learned_ok += learned_i == exp
        hybrid_ok += hybrid_i == exp
        # where markers were silent: did learned help vs the marker fallback?
        if not markers_fired:
            if hybrid_i == exp and marker_i != exp:
                rescued += 1
            if hybrid_i != exp and marker_i == exp:
                broke += 1

    n = len(campaign.cases)
    print(f"marker-alone intent : {marker_ok}/{n} = {marker_ok/n:.2f}")
    print(f"learned-alone intent: {learned_ok}/{n} = {learned_ok/n:.2f}")
    print(f"HYBRID intent       : {hybrid_ok}/{n} = {hybrid_ok/n:.2f}")
    print(f"  on no-match cases: rescued {rescued}, broke {broke}")


if __name__ == "__main__":
    main()
