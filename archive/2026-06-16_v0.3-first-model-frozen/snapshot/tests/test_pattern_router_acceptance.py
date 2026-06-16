import json
from pathlib import Path

import pytest

from pattern_learning.evaluation import evaluate_router
from pattern_learning.trainer import RouterModel


ROOT = Path(__file__).parents[1]
MODEL_PATH = ROOT / "build" / "pattern_router_model.json"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pattern_router_cases_v1.json"
CASES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
FOUNDATION_PATH = (
    Path(__file__).parent / "fixtures" / "foundation_anchor_suite_v1.json"
)


def test_deployed_router_matches_frozen_boundary_fixture() -> None:
    metrics = evaluate_router(RouterModel.load(MODEL_PATH), CASES)

    assert metrics["case_count"] == 25
    assert metrics["raw_accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["misses"] == []


def test_deployed_router_passes_foundation_anchor_suite() -> None:
    """tier 0自己一貫性契約: デプロイモデルは基礎入力で退行しない。"""

    payload = json.loads(FOUNDATION_PATH.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "foundation-anchor-suite.v1"
    assert len(payload["cases"]) >= 50

    model = RouterModel.load(MODEL_PATH)
    misses = [
        case
        for case in payload["cases"]
        if model.predict(case["input"]).route != case["route"]
    ]
    assert misses == []


def test_router_evaluation_keeps_abstention_separate_from_label_accuracy() -> None:
    model = RouterModel.load(MODEL_PATH)
    metrics = evaluate_router(model, CASES)

    assert metrics["coverage"] + metrics["abstention_rate"] == pytest.approx(1.0)
    assert 0.0 <= metrics["effective_label_accuracy"] <= 1.0
    assert 0.0 <= metrics["selective_accuracy"] <= 1.0
    assert "abstention_utility" not in model.metadata["calibration"]
    assert "abstention_diagnostics" in model.metadata["calibration"]
