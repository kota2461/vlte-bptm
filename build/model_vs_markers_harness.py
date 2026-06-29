"""Honest decomposition: can the learned model carry intent on its own?

The router currently lets markers decide and consults the IntentModel only on
marker-miss (margin >= INTENT_GATE_MARGIN). To decide whether to lean on the
model, measure each component's intent accuracy on the held-out validation
split (never tuned on), snapshot gated OFF:

  markers_only   - _intent_scores top intent (no model)
  model_only     - IntentModel.predict top intent (always, no markers)
  model_gated    - model if margin >= gate else 'respond' fallback
  hybrid_current - route() gate-off (markers-first, model fallback)

train shown only as a reference ceiling. Read-only; writes one report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_benchmark, route  # noqa: E402
from semantic_routing.adapter import DEFAULT_INTENT_MODEL_PATH, _load_intent_model  # noqa: E402
from semantic_routing.baseline import INTENT_GATE_MARGIN, _intent_scores  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso  # noqa: E402

BENCH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
OUT = ROOT / "build" / "model_vs_markers_harness_v1.json"


def _acc(cases, predict) -> float:
    if not cases:
        return 0.0
    ok = sum(1 for c in cases if predict(c) == c.expected.primary_intent)
    return round(ok / len(cases), 6)


def main() -> None:
    model = _load_intent_model(str(DEFAULT_INTENT_MODEL_PATH))
    bench = parse_plm_benchmark(json.loads(BENCH.read_text(encoding="utf-8")))
    by_split: dict[str, list] = {}
    for c in bench.cases:
        by_split.setdefault(getattr(c, "split", "unknown"), []).append(c)

    def markers_only(c):
        return _intent_scores(c.input_text)[0][0].intent

    def model_only(c):
        return model.predict(c.input_text).intent

    def model_gated(c):
        p = model.predict(c.input_text)
        return p.intent if p.margin >= INTENT_GATE_MARGIN else "respond"

    def hybrid(c):
        return route(c.input_text, use_legacy_snapshot=False).packet.primary_intent

    regimes = {
        "markers_only": markers_only,
        "model_only": model_only,
        "model_gated": model_gated,
        "hybrid_current": hybrid,
    }

    result = {}
    for split in ("validation", "train"):
        cases = by_split.get(split, [])
        result[split] = {name: _acc(cases, fn) for name, fn in regimes.items()}

    # how often the model is confident enough to lead (margin >= gate) on validation
    val = by_split.get("validation", [])
    confident = sum(1 for c in val if model.predict(c.input_text).margin >= INTENT_GATE_MARGIN)
    # of confident predictions, how many correct (model precision when it leads)
    conf_cases = [c for c in val if model.predict(c.input_text).margin >= INTENT_GATE_MARGIN]
    conf_correct = sum(1 for c in conf_cases if model.predict(c.input_text).intent == c.expected.primary_intent)

    report = {
        "schema_version": "model-vs-markers-harness.v1",
        "generated_at": reproducible_now_iso(),
        "gate_margin": INTENT_GATE_MARGIN,
        "intent_accuracy": result,
        "model_confidence_on_validation": {
            "confident_count": confident,
            "validation_total": len(val),
            "confident_rate": round(confident / len(val), 6) if val else 0.0,
            "precision_when_confident": round(conf_correct / len(conf_cases), 6) if conf_cases else None,
        },
        "note": "validation is held-out (never tuned on); train is a reference ceiling only.",
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"intent_accuracy": result, "model_confidence_on_validation": report["model_confidence_on_validation"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
