"""Run the intent-model deployment gate; promote only with `promote` arg.

  python build/run_intent_gate.py            # evaluate + print, no deploy
  python build/run_intent_gate.py promote    # evaluate, then promote if pass
"""

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.intent_deployment import (
    DEFAULT_CANDIDATE, DEFAULT_DEPLOYED,
    run_intent_deployment_gate, promote_intent_model,
)


def _summary(checks, name):
    c = checks[name]
    return f"{name}: passed={c.get('passed')}" + (
        f" acc={c['accuracy']:.3f} misses={len(c['misses'])}"
        if "accuracy" in c else "")


def main() -> None:
    do_promote = len(sys.argv) > 1 and sys.argv[1] == "promote"
    report = run_intent_deployment_gate()
    checks = report["checks"]

    print("=== intent-model deployment gate ===")
    print(_summary(checks, "foundation_anchors"))
    print(_summary(checks, "hybrid_regression"))
    print("fixture_integrity: passed=", checks["fixture_integrity"]["passed"])
    print("minimum_counts: passed=", checks["minimum_counts"]["passed"])
    print("improvement_vs_deployed:", json.dumps(
        checks["improvement_vs_deployed"], ensure_ascii=False))
    print(f"contract_passed={report['contract_passed']} "
          f"improvement_accepted={report['improvement_accepted']} "
          f"-> decision={report['decision']}")
    for nm in ("foundation_anchors", "hybrid_regression"):
        for m in checks[nm]["misses"]:
            print(f"  MISS [{nm}] {m['expected']}->{m['predicted']} | {m['input']}")

    (ROOT / "build" / "intent_gate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("report -> build/intent_gate_report.json")

    if do_promote:
        if report["passed"]:
            deployed = promote_intent_model(
                ROOT / DEFAULT_CANDIDATE, ROOT / DEFAULT_DEPLOYED, report)
            print(f"\nPROMOTED -> {deployed}")
            print("archived previous:", report["promotion"]["archived_previous"])
        else:
            print("\nNOT promoted: gate did not pass.")


if __name__ == "__main__":
    main()
