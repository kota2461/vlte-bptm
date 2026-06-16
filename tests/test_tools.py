import pytest

from semantic_routing.tools import (
    DEFAULT_TOOL_REGISTRY,
    ToolResult,
    calculator,
    run_tools,
    safe_eval,
)


def test_safe_eval_basic_and_unicode_operators():
    assert safe_eval("12 + 7") == 19
    assert safe_eval("2*(3+4)") == 14
    assert safe_eval("12 × 7") == 84
    assert safe_eval("84 ÷ 2") == 42


def test_safe_eval_rejects_non_arithmetic():
    for bad in ("__import__('os')", "a + 1", "1; 2", "open('x')"):
        with pytest.raises((ValueError, SyntaxError)):
            safe_eval(bad)


def test_calculator_checks_equation_claim():
    res = calculator("この計算が合っているか確認して: 12 + 7 = 20")
    assert res.ok
    assert "12 + 7 = 19" in res.output
    assert "誤り" in res.output


def test_calculator_correct_equation():
    res = calculator("8 + 8 = 16 で合ってる？")
    assert res.ok
    assert "正しい" in res.output


def test_calculator_standalone_expression():
    res = calculator("2*(3+4) を計算して")
    assert res.ok
    assert "2*(3+4) = 14" in res.output


def test_calculator_no_arithmetic():
    res = calculator("こんにちは、元気ですか？")
    assert res.ok is False


def test_run_tools_marks_unavailable_web_search():
    results = run_tools(["calculator", "web_search"], "12 + 7 = 20")
    by_name = {r.name: r for r in results}
    assert by_name["calculator"].ok is True
    assert by_name["web_search"].ok is False
    assert by_name["web_search"].detail == "tool not available"


def test_run_tools_injected_tool():
    def fake_search(text: str) -> ToolResult:
        return ToolResult("web_search", ok=True, output="result for: " + text)

    registry = {**DEFAULT_TOOL_REGISTRY, "web_search": fake_search}
    results = run_tools(["web_search"], "天気", registry=registry)
    assert results[0].ok is True
    assert "天気" in results[0].output


def test_run_tools_tool_error_is_contained():
    def boom(text: str) -> ToolResult:
        raise RuntimeError("kaboom")

    results = run_tools(["x"], "t", registry={"x": boom})
    assert results[0].ok is False
    assert "kaboom" in results[0].detail
