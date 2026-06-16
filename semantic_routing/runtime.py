"""Runtime entry: route() -> tier model -> budget -> external LLM -> reply.

`route_and_execute` is the single "call the router on text and get an answer"
entry point. It ties the v0.3 pieces together:

    text
      -> route()                      intent + processing plan (hybrid)
      -> select_model(model_class)    concrete backend by tier
      -> resolve_request_budget()     content budget + reasoning allowance
      -> chat_fn(...)                 the external LLM (injected; outside core)
      -> parse content                with reasoning_content fallback

The LLM call is injected as `chat_fn` so the orchestration is pure and unit
-testable; a concrete LM Studio client (`lmstudio_chat_fn` /
`lmstudio_available_models`) is provided for real use. The external LLM lives
OUTSIDE thought_core and its output is returned to the caller, never
persisted as training data.
"""

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from .adapter import DEFAULT_INTENT_MODEL_PATH, route
from .direct import direct_response
from .executor import (
    looks_like_reasoning_model,
    resolve_request_budget,
    select_model,
)
from .intent_model import IntentModel
from .processing_plan import ProcessingPlan
from .semantic_packet import SemanticPacket
from .tools import DEFAULT_TOOL_REGISTRY, Tool, ToolResult, run_tools


# sentinel "model" value when a reply is produced locally without an LLM
DIRECT_MODEL = "(direct)"


# Per-intent instruction appended to the routing system prompt.
INSTRUCTION: Dict[str, str] = {
    "respond": "Answer directly and concisely.",
    "explain": "Explain the reason or mechanism clearly.",
    "build": "Produce concrete, ordered steps.",
    "verify": "Check correctness and state what you verified.",
    "summarize": "Summarize concisely.",
    "explore": "Offer a few distinct options with trade-offs.",
    "clarify": "Ask only for the missing information needed to proceed.",
}

# chat_fn(model=..., messages=[...], max_tokens=int, temperature=float) -> raw
# OpenAI-style response dict.
ChatFn = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class ExecutionResult:
    text: str
    intent: str
    plan: ProcessingPlan
    model: str
    request_max_tokens: int
    finish_reason: Optional[str]
    via: str            # "content" | "reasoning_content" | "empty"
    reply_chars: int
    tools: tuple = ()   # ToolResult per requested tool
    decided_by: str = ""        # markers | learned | fallback | direct
    margin: Optional[float] = None  # learned-layer margin when consulted

    def as_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "intent": self.intent,
            "processing_class": self.plan.processing_class,
            "core_mode": self.plan.core_mode,
            "model_class": self.plan.model_class,
            "model": self.model,
            "request_max_tokens": self.request_max_tokens,
            "finish_reason": self.finish_reason,
            "via": self.via,
            "reply_chars": self.reply_chars,
            "tools": [t.as_dict() for t in self.tools],
            "decided_by": self.decided_by,
            "margin": self.margin,
        }


def _tool_grounding_block(results: Sequence[ToolResult]) -> str:
    """Render successful tool outputs as a grounding section for the LLM."""
    lines = [f"- {t.name}: {t.output}" for t in results if t.ok and t.output]
    if not lines:
        return ""
    return (
        "\n\n[tool results — use these as ground truth]\n" + "\n".join(lines)
    )


def build_system_prompt(packet: SemanticPacket, plan: ProcessingPlan) -> str:
    intent = packet.primary_intent
    return (
        f"[routing] intent={intent}, processing={plan.processing_class}, "
        f"mode={plan.core_mode}, model_class={plan.model_class}. "
        f"{INSTRUCTION.get(intent, '')} Respond in the user's language."
    )


def _parse_reply(response: Dict[str, Any]) -> tuple[str, Optional[str], str]:
    choice = response["choices"][0]
    msg = choice.get("message", {})
    finish = choice.get("finish_reason")
    content = (msg.get("content") or "").strip()
    if content:
        return content, finish, "content"
    reasoning = (msg.get("reasoning_content") or "").strip()
    if reasoning:
        return reasoning, finish, "reasoning_content"
    return "", finish, "empty"


def route_and_execute(
    text: str,
    *,
    chat_fn: Optional[ChatFn] = None,
    available_models: Sequence[str] = (),
    intent_model: Optional[IntentModel] = None,
    model_path: Path = DEFAULT_INTENT_MODEL_PATH,
    temperature: float = 0.3,
    tool_registry: Mapping[str, Tool] = DEFAULT_TOOL_REGISTRY,
    allow_direct: bool = True,
) -> ExecutionResult:
    """Route `text`, run requested tools, pick a tier model, call the LLM.

    Trivial smalltalk (greetings/thanks/...) that the router classifies as
    respond/economy is answered locally without an LLM call (`via="direct"`,
    model="(direct)") — this needs no backend.
    """

    result = route(text, intent_model=intent_model, model_path=model_path)
    packet, plan = result.packet, result.plan

    # fast path: deterministic reply for trivial smalltalk, no LLM call
    if (
        allow_direct
        and packet.primary_intent == "respond"
        and plan.processing_class == "economy"
    ):
        answer = direct_response(text, language=packet.language)
        if answer is not None:
            return ExecutionResult(
                text=answer.text,
                intent=packet.primary_intent,
                plan=plan,
                model=DIRECT_MODEL,
                request_max_tokens=0,
                finish_reason="direct",
                via="direct",
                reply_chars=len(answer.text),
                tools=(),
                decided_by="direct",
                margin=None,
            )

    if chat_fn is None or not available_models:
        raise ValueError("no LLM backend available to execute this route")

    model = select_model(plan.model_class, available_models)
    if model is None:
        raise ValueError("model selection returned no backend model")

    # execute any tools the plan requested, feed results as grounding context
    tool_results = run_tools(plan.tools, text, registry=tool_registry)
    system = build_system_prompt(packet, plan) + _tool_grounding_block(tool_results)

    reasoning = looks_like_reasoning_model(model)
    budget = resolve_request_budget(plan, reasoning=reasoning)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]
    response = chat_fn(
        model=model,
        messages=messages,
        max_tokens=budget.request_max_tokens,
        temperature=temperature,
    )
    reply, finish, via = _parse_reply(response)
    return ExecutionResult(
        text=reply,
        intent=packet.primary_intent,
        plan=plan,
        model=model,
        request_max_tokens=budget.request_max_tokens,
        finish_reason=finish,
        via=via,
        reply_chars=len(reply),
        tools=tuple(tool_results),
        decided_by=result.trace.get("decided_by", ""),
        margin=result.trace.get("intent_margin"),
    )


# --------------------------------------------------------------------------
# concrete LM Studio client (OpenAI-compatible) -- the external executor
# --------------------------------------------------------------------------
def lmstudio_available_models(base_url: str, *, timeout: float = 8.0) -> List[str]:
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/models",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return [m["id"] for m in payload.get("data", [])]


def lmstudio_chat_fn(base_url: str, *, timeout: float = 180.0) -> ChatFn:
    """Return a chat_fn that posts to an LM Studio /v1/chat/completions."""

    endpoint = base_url.rstrip("/") + "/v1/chat/completions"

    def _call(*, model, messages, max_tokens, temperature=0.3) -> Dict[str, Any]:
        data = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    return _call
