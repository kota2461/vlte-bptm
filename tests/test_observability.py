"""v0.3.1 observability: trace records WHY a route was decided, and NEVER
changes the decision (no-regression)."""

from pathlib import Path

from semantic_routing import route
from semantic_routing.adapter import ADAPTER_VERSION
from semantic_routing.baseline import extract_semantic_packet
from semantic_routing.intent_model import IntentPrediction
from semantic_routing.runtime import route_and_execute

AVAILABLE = ["google/gemma-4-e4b", "google/gemma-4-12b-qat"]


class _Fake:
    def __init__(self, intent, margin):
        self._i, self._m = intent, margin
        self.metadata = {}

    def predict(self, text):
        return IntentPrediction(self._i, self._m, {self._i: 1.0, "respond": 0.5})


def test_trace_marker_decision():
    r = route("セットアップ手順を作って")
    assert r.trace["decided_by"] == "markers"
    assert r.trace["markers_fired"] is True
    assert r.trace["adapter_version"] == ADAPTER_VERSION


def test_trace_learned_decision_with_injected_model():
    # markers silent + confident model -> decided_by learned
    r = route("やっと終わってほっとした", intent_model=_Fake("explore", 0.9))
    assert r.packet.primary_intent == "explore"
    assert r.trace["decided_by"] == "learned"
    assert r.trace["intent_margin"] == 0.9
    assert r.trace["intent_top_scores"][0][0] == "explore"


def test_trace_fallback_when_margin_below_gate():
    # markers silent + low-margin model -> fallback (decision unchanged)
    r = route("やっと終わってほっとした", intent_model=_Fake("explore", 0.01))
    assert r.packet.primary_intent == "respond"   # fallback, NOT explore
    assert r.trace["decided_by"] == "fallback"
    assert r.trace["markers_fired"] is False


def test_trace_does_not_change_decisions():
    # same packet/intent with and without a trace dict
    for text in ["手順を作って", "なぜ空は青いのか教えて", "こんにちは", "要約して"]:
        no_trace = extract_semantic_packet(text)
        with_trace = extract_semantic_packet(text, None, trace={})
        assert no_trace.primary_intent == with_trace.primary_intent
        assert no_trace.as_dict() == with_trace.as_dict()


def test_execution_result_carries_decided_by():
    def chat_fn(*, model, messages, max_tokens, temperature=0.3):
        return {"choices": [{"message": {"content": "x"}, "finish_reason": "stop"}]}

    # greeting -> direct
    g = route_and_execute("こんにちは", chat_fn=chat_fn, available_models=AVAILABLE)
    assert g.decided_by == "direct"
    # real question -> markers/fallback/learned (not direct)
    q = route_and_execute("セットアップ手順を作って", chat_fn=chat_fn,
                          available_models=AVAILABLE)
    assert q.decided_by in {"markers", "learned", "fallback"}
    assert "decided_by" in q.as_dict()
