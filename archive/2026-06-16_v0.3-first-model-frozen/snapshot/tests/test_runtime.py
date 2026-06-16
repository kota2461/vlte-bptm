import pytest

from semantic_routing import route
from semantic_routing.executor import DEFAULT_MODEL_TIERS, select_model
from semantic_routing.runtime import route_and_execute

AVAILABLE = [
    "google/gemma-4-e4b",
    "google/gemma-4-12b-qat",
    "google/gemma-4-12b",
    "google/gemma-3-12b",
]


# ---- tier selection ------------------------------------------------------
def test_select_model_per_tier():
    assert select_model("small", AVAILABLE) == "google/gemma-4-e4b"
    assert select_model("standard", AVAILABLE) == "google/gemma-4-12b-qat"
    assert select_model("large", AVAILABLE) == "google/gemma-4-12b"


def test_select_model_falls_back_when_tier_absent():
    only_qat = ["google/gemma-4-12b-qat"]
    # large's preferred (gemma-4-12b) absent -> qat is in large's preference list
    assert select_model("large", only_qat) == "google/gemma-4-12b-qat"
    # unknown class -> cross-tier fallback still yields an available model
    assert select_model("nonexistent", only_qat) == "google/gemma-4-12b-qat"


def test_select_model_none_when_nothing_available():
    assert select_model("standard", []) is None


# ---- route_and_execute (pure orchestration via injected chat_fn) ---------
def _fake_chat_fn(reply="こんにちは！元気です。", reasoning="", finish="stop"):
    captured = {}

    def chat_fn(*, model, messages, max_tokens, temperature=0.3):
        captured["model"] = model
        captured["max_tokens"] = max_tokens
        captured["messages"] = messages
        return {
            "choices": [{
                "message": {"content": reply, "reasoning_content": reasoning},
                "finish_reason": finish,
            }],
        }

    return chat_fn, captured


def test_route_and_execute_routes_and_selects_tier_model():
    chat_fn, captured = _fake_chat_fn()
    # allow_direct=False to exercise the LLM tier path (greetings would
    # otherwise short-circuit to the direct responder)
    result = route_and_execute(
        "こんにちは、調子はどう？", chat_fn=chat_fn, available_models=AVAILABLE,
        allow_direct=False,
    )
    assert result.intent == "respond"
    assert result.plan.processing_class == "economy"
    assert result.plan.model_class == "small"
    # economy -> small tier -> e4b
    assert result.model == "google/gemma-4-e4b"
    assert captured["model"] == "google/gemma-4-e4b"
    # reasoning model -> content budget + allowance
    assert captured["max_tokens"] == result.request_max_tokens > result.plan.budgets.max_output_tokens
    assert result.via == "content"
    assert result.text


def test_route_and_execute_uses_reasoning_fallback_when_content_empty():
    chat_fn, _ = _fake_chat_fn(reply="", reasoning="考え中…", finish="length")
    result = route_and_execute(
        "なぜ空は青いのか教えて", chat_fn=chat_fn, available_models=AVAILABLE,
    )
    assert result.intent == "explain"
    assert result.via == "reasoning_content"
    assert result.text == "考え中…"


def test_route_and_execute_system_prompt_carries_routing():
    chat_fn, captured = _fake_chat_fn()
    route_and_execute(
        "セットアップ手順を作って", chat_fn=chat_fn, available_models=AVAILABLE,
    )
    system = captured["messages"][0]["content"]
    assert "intent=build" in system
    assert "model_class=" in system


def test_route_and_execute_requires_available_models():
    chat_fn, _ = _fake_chat_fn()
    # a route that needs the LLM (not smalltalk) with no backend -> error
    with pytest.raises(ValueError):
        route_and_execute(
            "なぜ空は青いのか教えて", chat_fn=chat_fn, available_models=[],
        )


def test_build_class_routes_to_standard_or_higher():
    # a build request is not economy-eligible -> standard tier model
    plan = route("セットアップ手順を作って").plan
    assert plan.model_class in {"standard", "large"}
    assert select_model(plan.model_class, AVAILABLE) in {
        "google/gemma-4-12b-qat", "google/gemma-4-12b",
    }
