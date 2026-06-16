"""Evaluate the deployed router against the frozen regression fixture."""

import json
from pathlib import Path

from pattern_learning.evaluation import evaluate_router
from pattern_learning.trainer import RouterModel


MODEL_PATH = Path("build/pattern_router_model.json")
FIXTURE_PATH = Path("tests/fixtures/pattern_router_cases_v1.json")
MIN_RAW_ACCURACY = 1.0


def main() -> int:
    model = RouterModel.load(MODEL_PATH)
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    metrics = evaluate_router(model, cases)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0 if metrics["raw_accuracy"] >= MIN_RAW_ACCURACY else 1


if __name__ == "__main__":
    raise SystemExit(main())
