"""Calibrate the learned-intent margin gate using harvested drops as negatives.

The hybrid router consults the learned IntentModel only when the deterministic
markers miss, and accepts its label only when the prediction margin (top1-top2)
clears ``baseline.INTENT_GATE_MARGIN`` (default 0.15). This script measures how
that threshold trades off:

  * positive coverage  -- out-of-sample harvested utterances that clear the
    gate AND are predicted correctly (held-out split, not used for training),
  * junk-abstain rate  -- harvested DROP utterances (pasted logs, acks, file
    paths; the URL drop is excluded per reviewer) that the gate suppresses
    (margin < threshold), i.e. correctly refuses to route.

Drops are negatives by construction: a healthy gate should abstain on them.
The sealed accumulation campaign is NEVER read here, so the seal holds.

Writes build/intent_gate_calibration_v1.json and prints a sweep table.
"""

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.baseline import INTENT_GATE_MARGIN
from semantic_routing.intent_model import IntentModel, load_intent_corpus

CORPUS = ROOT / "data" / "intent_training_corpus_v1.json"
HARVEST = ROOT / "data" / "harvested_claudelog_v1.json"
OUT = ROOT / "build" / "intent_gate_calibration_v1.json"

# Hold out every Nth approved harvest item (deterministic, no RNG) so the
# positive margins are measured out-of-sample.
HOLDOUT_EVERY = 6


def main() -> int:
    harvest = json.loads(HARVEST.read_text(encoding="utf-8"))
    approved = [
        e
        for e in harvest["examples"]
        if e["intent"] != "drop" and e.get("review_status") == "approved"
    ]
    approved.sort(key=lambda e: e["input"])
    holdout = approved[::HOLDOUT_EVERY]
    holdout_inputs = {e["input"] for e in holdout}

    # Negatives: drops, minus any flagged for calibration exclusion (URLs).
    negatives = [
        e
        for e in harvest["examples"]
        if e["intent"] == "drop" and not e.get("calibration_exclude")
    ]

    # Train a calibration model on the corpus MINUS the held-out positives, so
    # holdout margins are genuinely out-of-sample. The deployed model stays the
    # full-data build/intent_model_v1.json; this model is calibration-only.
    corpus = load_intent_corpus(CORPUS)
    train = [e for e in corpus if e["input"] not in holdout_inputs]
    model = IntentModel.train(train)

    pos = [
        (e["input"], e["intent"], model.predict(e["input"]))
        for e in holdout
    ]
    neg = [(e["input"], model.predict(e["input"])) for e in negatives]

    rows = []
    best = None
    t = 0.0
    while t <= 0.50001:
        thr = round(t, 2)
        # coverage: held-out positive cleared the gate AND correct label
        cov = sum(1 for _, intent, p in pos if p.margin >= thr and p.intent == intent)
        cov_rate = cov / len(pos) if pos else 0.0
        # junk-abstain: drop suppressed by the gate (margin below threshold)
        abst = sum(1 for _, p in neg if p.margin < thr)
        abst_rate = abst / len(neg) if neg else 0.0
        f = (
            2 * cov_rate * abst_rate / (cov_rate + abst_rate)
            if (cov_rate + abst_rate)
            else 0.0
        )
        row = {
            "threshold": thr,
            "pos_coverage": round(cov_rate, 3),
            "junk_abstain": round(abst_rate, 3),
            "balance_f1": round(f, 3),
        }
        rows.append(row)
        if best is None or f > best["balance_f1"]:
            best = row
        t += 0.05

    report = {
        "schema_version": "intent-gate-calibration.v1",
        "current_gate_margin": INTENT_GATE_MARGIN,
        "holdout_positives": len(pos),
        "negatives_drops": len(neg),
        "note": (
            "Positives are out-of-sample held-out harvested utterances; "
            "negatives are harvested drops (URL drop excluded). Sealed "
            "campaign not used. balance_f1 = harmonic mean of positive "
            "coverage and junk-abstain rate."
        ),
        "sweep": rows,
        "recommended": best,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"holdout positives: {len(pos)} | drop negatives: {len(neg)}")
    print(f"current gate margin: {INTENT_GATE_MARGIN}")
    print(f"{'thr':>5} {'pos_cov':>8} {'junk_abst':>10} {'bal_f1':>7}")
    for r in rows:
        mark = "  <- current" if abs(r["threshold"] - INTENT_GATE_MARGIN) < 1e-9 else ""
        star = " *best" if r is best else ""
        print(
            f"{r['threshold']:>5} {r['pos_coverage']:>8} "
            f"{r['junk_abstain']:>10} {r['balance_f1']:>7}{mark}{star}"
        )
    print(f"recommended threshold: {best['threshold']} "
          f"(cov {best['pos_coverage']}, abstain {best['junk_abstain']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
