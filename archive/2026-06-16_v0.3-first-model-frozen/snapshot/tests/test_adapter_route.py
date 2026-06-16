from pathlib import Path

from semantic_routing import route
from semantic_routing.adapter import DEFAULT_INTENT_MODEL_PATH
from semantic_routing.processing_plan import ProcessingPlan
from semantic_routing.semantic_packet import SemanticPacket


def test_route_returns_packet_and_plan() -> None:
    result = route("手順を作ってください")
    assert isinstance(result.packet, SemanticPacket)
    assert isinstance(result.plan, ProcessingPlan)
    assert result.plan.primary_route == result.packet.primary_intent


def test_route_degrades_gracefully_without_model(tmp_path: Path) -> None:
    # missing model path -> markers-only, still produces a valid result
    missing = tmp_path / "no_model.json"
    result = route("手順を作ってください", model_path=missing)
    assert result.packet.primary_intent == "build"


def test_route_uses_injected_model_on_no_match() -> None:
    from semantic_routing.intent_model import IntentPrediction

    class _Fake:
        def predict(self, text):
            return IntentPrediction("explain", 0.5, {"explain": 1.0})

    nomatch = "やっと終わってほっとした"
    assert route(nomatch, model_path=Path("does_not_exist.json")).packet.primary_intent == "respond"
    assert route(nomatch, intent_model=_Fake()).packet.primary_intent == "explain"


def test_default_intent_model_path_points_into_build() -> None:
    assert DEFAULT_INTENT_MODEL_PATH.name == "intent_model_v1.json"
    assert DEFAULT_INTENT_MODEL_PATH.parent.name == "build"
