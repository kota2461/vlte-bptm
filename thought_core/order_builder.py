from typing import Mapping

from .action_vector import ACTION_VECTOR_SCHEMA_VERSION, ActionVector
from .bits import ThoughtCode


LLM_ORDER_SCHEMA_VERSION = "vlte-bptm.llm-order.v1"


AXIS_TO_MODE = {
    "ask": "clarify",
    "plan": "build",
    "verify": "verify",
    "summarize": "summarize",
    "creative": "explore",
    "caution": "verify",
    "explain": "explain",
    "reply": "respond",
}

CONTROL_AXES = (
    "ask",
    "verify",
    "plan",
    "summarize",
    "creative",
    "caution",
)

MODE_INSTRUCTIONS = {
    "clarify": "Ask only for information required to continue.",
    "build": "Produce an implementation-oriented answer with concrete steps.",
    "verify": "Check assumptions, risks, and evidence before concluding.",
    "summarize": "Compress the input without losing required decisions.",
    "explore": "Generate structured alternatives and mark uncertainty.",
    "explain": "Explain the result directly and concretely.",
    "respond": "Respond directly to the user input.",
}


def _select_mode(action_vector: ActionVector) -> str:
    values = action_vector.as_dict()
    control_axis = max(CONTROL_AXES, key=values.get)
    if values[control_axis] > 0.0:
        return AXIS_TO_MODE[control_axis]
    if values["explain"] > values["reply"]:
        return "explain"
    return "respond"


def build_llm_order(
    user_input: str,
    thought_code: ThoughtCode,
    action_vector: ActionVector,
    metadata: Mapping[str, object] | None = None,
    selected_mode: str | None = None,
    instruction_override: str | None = None,
) -> dict:
    mode = selected_mode or _select_mode(action_vector)
    if mode not in MODE_INSTRUCTIONS:
        raise ValueError(f"unknown LLM Order mode: {mode}")
    if (
        instruction_override is not None
        and (
            not isinstance(instruction_override, str)
            or not instruction_override.strip()
        )
    ):
        raise ValueError("instruction_override must be a non-empty string")
    return {
        "schema_version": LLM_ORDER_SCHEMA_VERSION,
        "mode": mode,
        "instruction": instruction_override or MODE_INSTRUCTIONS[mode],
        "user_input": user_input,
        "routing_key": thought_code.hex(),
        "action_vector_schema_version": ACTION_VECTOR_SCHEMA_VERSION,
        "action_vector": action_vector.as_dict(),
        "constraints": [
            "Do not persist cloud LLM output as training data.",
            "Do not perform automatic learning or automatic model updates.",
            "Do not train full-sentence regeneration.",
        ],
        "metadata": dict(metadata or {}),
    }
