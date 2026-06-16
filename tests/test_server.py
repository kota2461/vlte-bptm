from semantic_routing.server import handle

AVAILABLE = ["google/gemma-4-e4b", "google/gemma-4-12b-qat", "google/gemma-4-12b"]


def _chat_fn(reply="ok"):
    def chat_fn(*, model, messages, max_tokens, temperature=0.3):
        return {"choices": [{"message": {"content": reply}, "finish_reason": "stop"}]}
    return chat_fn


def test_health():
    status, body = handle("GET", "/health", None, available_models=AVAILABLE)
    assert status == 200
    assert body["status"] == "ok"
    assert body["models"] == AVAILABLE


def test_route_only_no_llm():
    status, body = handle("POST", "/route", {"text": "セットアップ手順を作って"})
    assert status == 200
    assert body["packet"]["intent_candidates"][0]["intent"] == "build"
    assert body["plan"]["primary_route"] == "build"
    assert body["plan"]["processing_class"] in {"standard", "deep", "verified"}
    assert "budgets" in body["plan"]


def test_route_bad_body():
    status, body = handle("POST", "/route", {"nope": 1})
    assert status == 400
    status, body = handle("POST", "/route", {"text": "   "})
    assert status == 400


def test_execute_runs_end_to_end():
    # a real question (not smalltalk) goes through the LLM path
    status, body = handle(
        "POST", "/execute", {"text": "なぜ空は青いのか教えて"},
        chat_fn=_chat_fn("レイリー散乱です"), available_models=AVAILABLE,
    )
    assert status == 200
    assert body["intent"] == "explain"
    assert body["model"] == "google/gemma-4-e4b"
    assert body["text"] == "レイリー散乱です"


def test_execute_smalltalk_short_circuits_without_backend():
    # greeting answered locally even with no LLM backend configured
    status, body = handle("POST", "/execute", {"text": "こんにちは"})
    assert status == 200
    assert body["via"] == "direct"
    assert body["model"] == "(direct)"


def test_execute_real_question_without_backend_is_503():
    status, body = handle("POST", "/execute", {"text": "なぜ空は青いのか教えて"})
    assert status == 503


def test_unknown_route_404():
    status, body = handle("GET", "/nope", None)
    assert status == 404


def test_execute_tool_grounding_reaches_llm():
    seen = {}

    def chat_fn(*, model, messages, max_tokens, temperature=0.3):
        seen["system"] = messages[0]["content"]
        return {"choices": [{"message": {"content": "確認しました"}, "finish_reason": "stop"}]}

    status, body = handle(
        "POST", "/execute",
        {"text": "この計算が合っているか確認して: 12 + 7 = 20"},
        chat_fn=chat_fn, available_models=AVAILABLE,
    )
    assert status == 200
    assert body["intent"] == "verify"
    # calculator result was injected as grounding for the LLM
    assert "12 + 7 = 19" in seen["system"]
    assert any(t["name"] == "calculator" and t["ok"] for t in body["tools"])
