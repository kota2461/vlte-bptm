import pytest

from semantic_routing.baseline import INTENT_GATE_MARGIN, extract_semantic_packet
from semantic_routing.intent_model import (
    INTENT_MODEL_SCHEMA_VERSION,
    IntentModel,
    IntentPrediction,
)


class _FakeIntentModel:
    """Deterministic stand-in to test the gated-merge wiring in isolation."""

    def __init__(self, intent: str, margin: float) -> None:
        self._prediction = IntentPrediction(
            intent=intent, margin=margin, scores={intent: 1.0}
        )

    def predict(self, text: str) -> IntentPrediction:
        return self._prediction


def _toy_examples():
    return [
        {"input": "この計算が正しいか確認して", "intent": "verify"},
        {"input": "手順を作ってください", "intent": "build"},
        {"input": "なぜそうなるのか説明して", "intent": "explain"},
        {"input": "候補を比較して", "intent": "explore"},
        {"input": "短くまとめて", "intent": "summarize"},
        {"input": "条件が足りないので質問して", "intent": "clarify"},
        {"input": "こんにちは", "intent": "respond"},
        {"input": "別の計算を検算してほしい", "intent": "verify"},
        {"input": "実装の段取りを組んで", "intent": "build"},
    ]


def test_train_predict_and_margin() -> None:
    model = IntentModel.train(_toy_examples(), dimension=512, epochs=20)
    pred = model.predict("この値が合っているか確認してほしい")
    assert pred.intent in model.labels
    assert pred.margin >= 0.0
    assert set(pred.scores) == set(model.labels)
    # deterministic: same input -> same prediction
    assert model.predict("手順を作って").intent == model.predict(
        "手順を作って"
    ).intent


def test_save_load_round_trip(tmp_path) -> None:
    model = IntentModel.train(_toy_examples(), dimension=512, epochs=20)
    path = tmp_path / "intent_model.json"
    model.save(path)
    reloaded = IntentModel.load(path)
    assert reloaded.labels == model.labels
    assert reloaded.dimension == model.dimension
    probe = "なぜこれが速いのか知りたい"
    assert reloaded.predict(probe).intent == model.predict(probe).intent
    assert reloaded.metadata["schema_version"] == INTENT_MODEL_SCHEMA_VERSION


def test_hybrid_overrides_no_match_only_when_confident() -> None:
    nomatch = "やっと終わってほっとした"
    # default (no model): markers-only -> respond fallback
    assert extract_semantic_packet(nomatch).primary_intent == "respond"
    # confident learned layer overrides on no-match
    confident = _FakeIntentModel("explain", INTENT_GATE_MARGIN + 0.1)
    assert extract_semantic_packet(nomatch, confident).primary_intent == "explain"
    # low-confidence learned layer does NOT override (gate protects fallback)
    timid = _FakeIntentModel("explain", INTENT_GATE_MARGIN - 0.05)
    assert extract_semantic_packet(nomatch, timid).primary_intent == "respond"


def test_hybrid_never_overrides_when_markers_fire() -> None:
    fired = "手順を作ってください"  # build markers fire
    baseline_intent = extract_semantic_packet(fired).primary_intent
    overriding = _FakeIntentModel("respond", 0.9)
    # markers always win; the learned layer is not consulted
    assert (
        extract_semantic_packet(fired, overriding).primary_intent
        == baseline_intent
    )


def test_train_rejects_unknown_intent_and_single_class() -> None:
    with pytest.raises(ValueError, match="unknown intent"):
        IntentModel.train([
            {"input": "x", "intent": "respond"},
            {"input": "y", "intent": "not_an_intent"},
        ])
    with pytest.raises(ValueError, match="at least two intents"):
        IntentModel.train([
            {"input": "x", "intent": "respond"},
            {"input": "y", "intent": "respond"},
        ])
