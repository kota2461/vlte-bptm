"""Executor-boundary budget resolution (pure policy, no network).

The processing plan's `max_output_tokens` is the budget for the ANSWER
(content tokens) and is part of the v1 contract — it is NOT changed here.

Reasoning-type models spend additional tokens *thinking* before they emit
content, and OpenAI-compatible `max_tokens` caps reasoning + content
together. So if the executor sends only the contract content budget to a
reasoning model, the reasoning pass eats the whole budget and the answer is
truncated to empty (`finish_reason="length"`, `content=""`).

Direction (1): keep the contract content budget intact and provision a
SEPARATE reasoning allowance ON TOP of it, only when the target model
reasons. The request's `max_tokens` therefore = content budget + reasoning
allowance. The contract still means "produce up to N content tokens"; the
allowance is operational headroom the executor owns.

(Direction (2) — suppress reasoning for light classes / route heavy
reasoning to `deep` — would be implemented by overriding `reasoning=` per
class at the call sites below; this module localises that single switch.)

This module lives OUTSIDE thought_core.
"""

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from .processing_plan import ProcessingPlan

# Default operational headroom for a reasoning model's thinking pass. Sized
# from observation (a hard counting problem used ~1.0-1.2k reasoning tokens).
DEFAULT_REASONING_ALLOWANCE = 1536

# Mirror the processing-plan budget ceiling so a request never exceeds it.
MAX_REQUEST_TOKENS = 32768

# Heuristic model classification. The authoritative signal is runtime
# (`message.reasoning_content` present) — these markers are only the a-priori
# guess used to size the FIRST request. Observed: the gemma-4 family emits
# reasoning_content; gemma-3 / qwen2.5-vl do not.
_NON_REASONING_MARKERS = ("gemma-3", "qwen", "embed")
_REASONING_MARKERS = ("gemma-4",)


# model_class -> ordered preference of concrete backend model ids.
# Assignment from the 2026-06-15 speed bench (build/lmstudio_speed_bench.py):
#   small    = smallest/cheapest model (e4b)
#   standard = fastest correct workhorse (gemma-4-12b-qat, 49 tok/s + correct)
#   large    = full-precision 12B for verified/deep/critical depth (slower by
#              design -- "large" spends more, matching the tier's intent)
# The leftover gemma-3-12b (fast but non-reasoning, weaker on hard problems)
# is kept only as a late fallback. Availability is resolved at call time.
DEFAULT_MODEL_TIERS = {
    "small": ("google/gemma-4-e4b", "google/gemma-3-12b", "google/gemma-4-12b-qat"),
    "standard": ("google/gemma-4-12b-qat", "google/gemma-4-12b", "google/gemma-3-12b"),
    "large": ("google/gemma-4-12b", "google/gemma-4-12b-qat", "google/gemma-4-e4b"),
}
# if a tier has nothing available, walk tiers in this order before giving up
_TIER_FALLBACK_ORDER = ("standard", "large", "small")


def select_model(
    model_class: str,
    available_models: Sequence[str],
    *,
    tiers: Mapping[str, Sequence[str]] = DEFAULT_MODEL_TIERS,
) -> Optional[str]:
    """Pick a concrete backend model id for a plan's model_class.

    Prefers the tier's ranked list (first available wins), then falls back
    across tiers, then to any available model. Returns None only when no
    models are available at all.
    """
    available = list(available_models or [])
    available_set = set(available)
    for mid in tiers.get(model_class, ()):
        if mid in available_set:
            return mid
    for cls in _TIER_FALLBACK_ORDER:
        for mid in tiers.get(cls, ()):
            if mid in available_set:
                return mid
    return available[0] if available else None


@dataclass(frozen=True)
class RequestBudget:
    """How the contract budget maps to an actual request `max_tokens`."""

    content_tokens: int       # contract answer budget (unchanged)
    reasoning_allowance: int  # extra room for the thinking pass (0 if none)
    request_max_tokens: int   # value to send as max_tokens

    def as_dict(self) -> dict:
        return {
            "content_tokens": self.content_tokens,
            "reasoning_allowance": self.reasoning_allowance,
            "request_max_tokens": self.request_max_tokens,
        }


def looks_like_reasoning_model(model_id: str) -> bool:
    """A-priori guess: does this model reason before answering?

    Unknown models default to True — over-provisioning costs a non-reasoning
    model nothing (it stops early at finish=stop), whereas under-provisioning
    a reasoning model returns an empty answer.
    """
    mid = (model_id or "").lower()
    if any(m in mid for m in _NON_REASONING_MARKERS):
        return False
    if any(m in mid for m in _REASONING_MARKERS):
        return True
    return True


def resolve_request_budget(
    plan: ProcessingPlan,
    *,
    reasoning: bool,
    reasoning_allowance: int = DEFAULT_REASONING_ALLOWANCE,
) -> RequestBudget:
    """Translate a plan's content budget into a request `max_tokens`.

    `reasoning=True` adds `reasoning_allowance` on top of the contract
    content budget; `reasoning=False` sends exactly the content budget so the
    contract answer length is honoured precisely.
    """
    if not isinstance(plan, ProcessingPlan):
        raise TypeError("resolve_request_budget requires a ProcessingPlan")
    if reasoning_allowance < 0:
        raise ValueError("reasoning_allowance must be non-negative")

    content = plan.budgets.max_output_tokens
    allowance = reasoning_allowance if reasoning else 0
    total = min(content + allowance, MAX_REQUEST_TOKENS)
    return RequestBudget(
        content_tokens=content,
        reasoning_allowance=allowance,
        request_max_tokens=total,
    )
