"""Confidence-gated hybrid probe.

The plain hybrid (marker when fired, else learned) was a wash on no-match
cases: rescued 4 / broke 3. Here, on no-match cases we defer to the learned
layer ONLY when its top1-top2 margin >= threshold, else keep the marker
fallback. Sweep thresholds to see if gating turns the wash into a net win
WITHOUT new data. PROBE ONLY.
"""

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

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

    def learned(text):
        feats = text_features(text, DIM)
        scores = sorted(
            (
                bias.get(lab, 0.0)
                + sum(weights[lab].get(i, 0.0) * v for i, v in feats.items()),
                lab,
            )
            for lab in labels
        )
        top_score, top_lab = scores[-1]
        margin = top_score - scores[-2][0] if len(scores) > 1 else top_score
        return top_lab, margin

    campaign = load_conversation_accumulation(CAMPAIGN)
    cases = []
    for case in campaign.cases:
        marker_i = extract_semantic_packet(case.input_text).primary_intent
        _c, evidence = _intent_scores(case.input_text)
        learned_i, margin = learned(case.input_text)
        cases.append((case.expected.intent, marker_i, bool(evidence),
                      learned_i, margin))

    n = len(cases)
    marker_acc = sum(m == e for e, m, _f, _l, _g in cases) / n
    print(f"marker-alone: {marker_acc:.2f}  (n={n})")
    print("threshold | hybrid acc | no-match rescued/broke")
    for thr in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30):
        ok = rescued = broke = 0
        for exp, marker_i, fired, learned_i, margin in cases:
            if fired:
                hyb = marker_i
            else:
                hyb = learned_i if margin >= thr else marker_i
            ok += hyb == exp
            if not fired:
                if hyb == exp and marker_i != exp:
                    rescued += 1
                if hyb != exp and marker_i == exp:
                    broke += 1
        print(f"  {thr:.2f}    |   {ok/n:.2f}    | {rescued}/{broke}")


if __name__ == "__main__":
    main()
