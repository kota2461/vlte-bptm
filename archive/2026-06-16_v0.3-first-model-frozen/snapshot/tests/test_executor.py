import pytest

from semantic_routing import route
from semantic_routing.executor import (
    DEFAULT_REASONING_ALLOWANCE,
    MAX_REQUEST_TOKENS,
    looks_like_reasoning_model,
    resolve_request_budget,
)


def _economy_plan():
    # a plain explain request routes to economy (content budget 384)
    plan = route("なぜ空は青いのか教えて").plan
    assert plan.processing_class == "economy"
    assert plan.budgets.max_output_tokens == 384
    return plan


def test_non_reasoning_request_equals_contract_content_budget():
    plan = _economy_plan()
    budget = resolve_request_budget(plan, reasoning=False)
    # contract answer length honoured exactly — no headroom added
    assert budget.reasoning_allowance == 0
    assert budget.request_max_tokens == plan.budgets.max_output_tokens


def test_reasoning_request_adds_allowance_on_top():
    plan = _economy_plan()
    budget = resolve_request_budget(plan, reasoning=True)
    assert budget.content_tokens == plan.budgets.max_output_tokens
    assert budget.reasoning_allowance == DEFAULT_REASONING_ALLOWANCE
    assert budget.request_max_tokens == (
        plan.budgets.max_output_tokens + DEFAULT_REASONING_ALLOWANCE
    )


def test_request_is_clamped_to_ceiling():
    plan = _economy_plan()
    budget = resolve_request_budget(
        plan, reasoning=True, reasoning_allowance=MAX_REQUEST_TOKENS * 2
    )
    assert budget.request_max_tokens == MAX_REQUEST_TOKENS


def test_negative_allowance_rejected():
    plan = _economy_plan()
    with pytest.raises(ValueError):
        resolve_request_budget(plan, reasoning=True, reasoning_allowance=-1)


def test_requires_a_processing_plan():
    with pytest.raises(TypeError):
        resolve_request_budget(object(), reasoning=True)  # type: ignore[arg-type]


def test_reasoning_model_heuristic():
    assert looks_like_reasoning_model("google/gemma-4-12b-qat") is True
    assert looks_like_reasoning_model("google/gemma-4-12b") is True
    assert looks_like_reasoning_model("google/gemma-3-12b") is False
    assert looks_like_reasoning_model("qwen/qwen2.5-vl-7b") is False
    # unknown models default to provisioning reasoning room
    assert looks_like_reasoning_model("some/unknown-model") is True
