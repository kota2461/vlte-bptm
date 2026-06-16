import json
import shutil
from pathlib import Path

import pytest

from semantic_routing.intent_model import IntentModel, IntentPrediction
from semantic_routing.intent_deployment import (
    evaluate_intent_gate,
    evaluate_intent_kfold,
    promote_intent_model,
    rollback_intent_model,
    run_intent_deployment_gate,
)
from pattern_learning.deployment import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEPLOYED = ROOT / "build" / "intent_model_v1.json"


def _model() -> IntentModel:
    return IntentModel.load(DEPLOYED)


class _Fake:
    """Always predicts a fixed intent with a gate-clearing margin."""

    def __init__(self, intent: str):
        self._intent = intent
        self.metadata: dict = {}

    def predict(self, text: str) -> IntentPrediction:
        return IntentPrediction(self._intent, 0.9, {self._intent: 1.0})


def test_kfold_returns_bounded_accuracy():
    examples = [
        {"input": f"手順を作って その{i}", "intent": "build"} for i in range(6)
    ] + [
        {"input": f"こんにちは {i}", "intent": "respond"} for i in range(6)
    ]
    metrics = evaluate_intent_kfold(examples, folds=3)
    assert 0.0 <= metrics["kfold_accuracy"] <= 1.0
    assert metrics["folds"] >= 1


def test_gate_passes_on_marker_anchors():
    foundation = [
        {"input": "こんにちは、調子はどう？", "intent": "respond"},
        {"input": "セットアップ手順を作って", "intent": "build"},
        {"input": "この計算が合っているか確認して", "intent": "verify"},
        {"input": "この記事を要約して", "intent": "summarize"},
    ]
    hybrid = [{"input": "計算を検算してから手順書を作って", "intent": "build"}]
    report = evaluate_intent_gate(_model(), foundation, hybrid)
    assert report["checks"]["foundation_anchors"]["passed"] is True
    assert report["checks"]["hybrid_regression"]["passed"] is True
    assert report["contract_passed"] is True


def test_gate_fails_when_learned_layer_mispredicts_nomatch():
    # markers stay silent -> the (fake, wrong) learned layer decides -> miss
    foundation = [{"input": "やっと終わってほっとした", "intent": "respond"}]
    report = evaluate_intent_gate(_Fake("build"), foundation, [])
    assert report["checks"]["foundation_anchors"]["passed"] is False
    assert report["contract_passed"] is False


def test_improvement_check_blocks_degradation():
    model = _model()
    model.metadata["metrics"] = {"kfold_accuracy": 0.50}
    report = evaluate_intent_gate(
        model, [], [], current_metrics={"kfold_accuracy": 0.90}
    )
    improvement = report["checks"]["improvement_vs_deployed"]
    assert improvement["passed"] is False
    assert report["improvement_accepted"] is False


def test_full_gate_passes_on_frozen_fixtures():
    report = run_intent_deployment_gate(
        candidate_path=ROOT / "build" / "intent_model_v1_candidate.json",
        foundation_fixture=ROOT / "tests" / "fixtures" / "intent_foundation_anchors_v1.json",
        hybrid_fixture=ROOT / "tests" / "fixtures" / "intent_hybrid_regression_v1.json",
        registry_path=ROOT / "tests" / "fixtures" / "intent_gate_fixture_registry.json",
        deployed_path=DEPLOYED,
    )
    assert report["decision"] == "pass"
    assert report["checks"]["fixture_integrity"]["passed"] is True
    assert report["checks"]["minimum_counts"]["passed"] is True


def test_promote_then_rollback(tmp_path: Path):
    deployed = tmp_path / "deployed.json"
    candidate = tmp_path / "candidate.json"
    history = tmp_path / "history"
    shutil.copy2(DEPLOYED, deployed)
    # candidate differs from deployed so rollback is observable
    m = _model()
    m.metadata["metrics"] = {"kfold_accuracy": 0.99}
    m.save(candidate)
    original_sha = file_sha256(deployed)

    report = {
        "contract_passed": True,
        "improvement_accepted": True,
        "hashes": {"candidate_sha256": file_sha256(candidate)},
    }
    promote_intent_model(candidate, deployed, report, history_dir=history)
    assert file_sha256(deployed) == file_sha256(candidate)
    assert report["promotion"]["archived_previous"] is not None

    roll = rollback_intent_model(deployed, history_dir=history, reason="test rollback")
    assert file_sha256(deployed) == original_sha
    assert roll["reason"] == "test rollback"


def test_promote_blocked_without_contract_pass(tmp_path: Path):
    deployed = tmp_path / "deployed.json"
    candidate = tmp_path / "candidate.json"
    shutil.copy2(DEPLOYED, deployed)
    shutil.copy2(DEPLOYED, candidate)
    with pytest.raises(ValueError):
        promote_intent_model(
            candidate, deployed,
            {"contract_passed": False, "improvement_accepted": True},
        )
