from semantic_routing import route
from semantic_routing.direct import direct_response
from semantic_routing.runtime import DIRECT_MODEL, route_and_execute

AVAILABLE = ["google/gemma-4-e4b", "google/gemma-4-12b-qat"]


def _exploding_chat_fn(*, model, messages, max_tokens, temperature=0.3):
    raise AssertionError("LLM must NOT be called on the direct path")


# ---- direct_response unit -------------------------------------------------
def test_direct_matches_smalltalk_categories():
    assert direct_response("こんにちは").category == "greeting"
    assert direct_response("ありがとう！").category == "thanks"
    assert direct_response("またね").category == "farewell"
    assert direct_response("了解").category == "acknowledgement"
    assert direct_response("調子はどう？").category == "wellbeing"


def test_direct_language_switch():
    assert direct_response("hello", language="en").text == "Hello! How can I help?"
    assert direct_response("こんにちは", language="ja").text.startswith("こんにちは")


def test_direct_returns_none_for_real_questions_and_long_text():
    assert direct_response("Pythonのデコレータを教えて") is None
    assert direct_response("x" * 80) is None
    assert direct_response("") is None


# ---- short-circuit through route_and_execute ------------------------------
def test_greeting_short_circuits_without_llm():
    result = route_and_execute(
        "こんにちは", chat_fn=_exploding_chat_fn, available_models=AVAILABLE,
    )
    assert result.via == "direct"
    assert result.model == DIRECT_MODEL
    assert result.finish_reason == "direct"
    assert result.request_max_tokens == 0
    assert result.text


def test_direct_works_with_no_backend_at_all():
    # no chat_fn, no models -> still answers trivial smalltalk
    result = route_and_execute("ありがとう")
    assert result.via == "direct"
    assert result.intent == "respond"


def test_real_question_does_not_short_circuit():
    # routes respond/economy but is NOT smalltalk -> direct returns None ->
    # the LLM is still consulted (no canned reply for a real question)
    seen = {}

    def chat_fn(*, model, messages, max_tokens, temperature=0.3):
        seen["called"] = True
        return {"choices": [{"message": {"content": "デコレータは…"}, "finish_reason": "stop"}]}

    result = route_and_execute(
        "Pythonのデコレータを教えて", chat_fn=chat_fn, available_models=AVAILABLE,
    )
    assert seen.get("called") is True
    assert result.via == "content"


def test_allow_direct_false_forces_llm():
    def chat_fn(*, model, messages, max_tokens, temperature=0.3):
        return {"choices": [{"message": {"content": "やあ"}, "finish_reason": "stop"}]}

    result = route_and_execute(
        "こんにちは", chat_fn=chat_fn, available_models=AVAILABLE, allow_direct=False,
    )
    assert result.via == "content"
    assert result.model != DIRECT_MODEL


def test_route_classifies_greeting_as_respond_economy():
    # the gate the short-circuit relies on
    plan = route("こんにちは").plan
    assert plan.primary_route == "respond"
    assert plan.processing_class == "economy"
