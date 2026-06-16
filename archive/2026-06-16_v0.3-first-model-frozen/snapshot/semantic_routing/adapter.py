"""v0.3 deployment entry — the canonical "run the adapter on text" call.

Ties the hybrid together: deterministic markers first (always win when they
fire) + the deployed learned intent layer on marker no-match, gated by
confidence (baseline.INTENT_GATE_MARGIN), then the deterministic processing
plan. The deployed intent model is loaded by default; if it is absent the
adapter degrades gracefully to markers-only (v0.2 behaviour).
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .baseline import extract_semantic_packet
from .intent_model import IntentModel
from .processing_plan import ProcessingPlan, build_processing_plan
from .semantic_packet import SemanticPacket


DEFAULT_INTENT_MODEL_PATH = (
    Path(__file__).resolve().parents[1] / "build" / "intent_model_v1.json"
)


@dataclass(frozen=True)
class RouteResult:
    packet: SemanticPacket
    plan: ProcessingPlan


@lru_cache(maxsize=4)
def _load_intent_model(path_str: str) -> Optional[IntentModel]:
    path = Path(path_str)
    return IntentModel.load(path) if path.exists() else None


def route(
    text: str,
    *,
    intent_model: Optional[IntentModel] = None,
    model_path: Path = DEFAULT_INTENT_MODEL_PATH,
) -> RouteResult:
    """Run the v0.3 hybrid adapter on `text` and return packet + plan.

    Pass `intent_model` to inject one explicitly (tests / pinned models).
    Otherwise the deployed model at `model_path` is used if present; if it is
    missing, the adapter runs markers-only.
    """
    model = (
        intent_model
        if intent_model is not None
        else _load_intent_model(str(model_path))
    )
    packet = extract_semantic_packet(text, model)
    plan = build_processing_plan(packet)
    return RouteResult(packet=packet, plan=plan)
