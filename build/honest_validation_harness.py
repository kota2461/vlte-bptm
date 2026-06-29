"""Step 2: an honest scoreboard for any router re-tuning.

Measures the router on the held-out *validation* split (never the sealed split,
never the train split it was tuned on) with the memorization snapshot both ON
and OFF. The gate-OFF column is the router's true generalization; the ON-vs-OFF
gap is how much the snapshot is doing. Any re-tuning is judged by whether the
gate-OFF validation numbers go UP -- not by a fixture hitting 1.000.

Read-only: writes one report JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_benchmark, route  # noqa: E402
from semantic_routing.evaluation import evaluate_plm_extractor  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso  # noqa: E402

BENCH = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
OUT = ROOT / "build" / "honest_validation_harness_v1.json"

METRIC_KEYS = (
    "intent_accuracy",
    "critical_signal_recall",
    "operation_exact_match",
    "constraint_exact_match",
    "risk_exact_match",
)


def _metrics(cases, *, use_legacy_snapshot: bool) -> dict:
    report = evaluate_plm_extractor(
        cases, lambda t: route(t, use_legacy_snapshot=use_legacy_snapshot).packet
    )
    return {k: report.get(k) for k in METRIC_KEYS}


def _per_case_failures(cases, *, use_legacy_snapshot: bool) -> list[dict]:
    """Cases the router gets wrong (gate-off honest view), for step-3 targeting."""
    out = []
    for case in cases:
        packet = route(case.input_text, use_legacy_snapshot=use_legacy_snapshot).packet
        exp = case.expected
        if packet.primary_intent != exp.primary_intent:
            out.append(
                {
                    "id": case.case_id,
                    "input": case.input_text[:80],
                    "expected_intent": exp.primary_intent,
                    "predicted_intent": packet.primary_intent,
                }
            )
    return out


def main() -> None:
    bench = parse_plm_benchmark(json.loads(BENCH.read_text(encoding="utf-8")))
    by_split: dict[str, list] = {}
    for case in bench.cases:
        by_split.setdefault(getattr(case, "split", "unknown"), []).append(case)

    validation = by_split.get("validation", [])
    train = by_split.get("train", [])

    report = {
        "schema_version": "honest-validation-harness.v1",
        "generated_at": reproducible_now_iso(),
        "fixture": BENCH.name,
        "split_sizes": {k: len(v) for k, v in sorted(by_split.items())},
        "policy": {
            "measured_split": "validation",
            "never_tuned_on": "validation/sealed",
            "judge_rule": "gate_off validation metrics must rise; fixture 1.000 is not the goal",
        },
        "validation_gate_on": _metrics(validation, use_legacy_snapshot=True) if validation else {},
        "validation_gate_off": _metrics(validation, use_legacy_snapshot=False) if validation else {},
        # train shown only as a reference ceiling (it was tuned on; do not optimise it)
        "train_gate_off_reference": _metrics(train, use_legacy_snapshot=False) if train else {},
        "validation_intent_failures_gate_off": _per_case_failures(validation, use_legacy_snapshot=False),
    }
    on = report["validation_gate_on"]
    off = report["validation_gate_off"]
    report["snapshot_gap_on_minus_off"] = {
        k: round((on.get(k) or 0) - (off.get(k) or 0), 6) for k in METRIC_KEYS
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "split_sizes": report["split_sizes"],
        "validation_gate_on": on,
        "validation_gate_off": off,
        "snapshot_gap": report["snapshot_gap_on_minus_off"],
        "validation_intent_errors_gate_off": len(report["validation_intent_failures_gate_off"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
