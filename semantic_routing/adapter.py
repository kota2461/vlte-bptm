"""v0.3 deployment entry — the canonical "run the adapter on text" call.

Ties the hybrid together: deterministic markers first (always win when they
fire) + the deployed learned intent layer on marker no-match, gated by
confidence (baseline.INTENT_GATE_MARGIN), then the deterministic processing
plan. The deployed intent model is loaded by default; if it is absent the
adapter degrades gracefully to markers-only (v0.2 behaviour).
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from .baseline import extract_semantic_packet
from .intent_model import IntentModel
from .guard_router import derive_failure_guard
from .knowledge_index import (
    DEFAULT_KNOWLEDGE_INDEX_PATH,
    RetrievalPacket,
    build_retrieval_packet,
)
from .processing_plan import ProcessingPlan, build_processing_plan
from .semantic_packet import SemanticPacket


ADAPTER_VERSION = "0.3.1"

DEFAULT_INTENT_MODEL_PATH = (
    Path(__file__).resolve().parents[1] / "build" / "intent_model_v1.json"
)


@dataclass(frozen=True)
class RouteResult:
    packet: SemanticPacket
    plan: ProcessingPlan
    retrieval: RetrievalPacket
    # observability only (v0.3.1) — how/why the intent was decided;
    # never affects routing decisions
    trace: Dict[str, Any] = field(default_factory=dict)


@lru_cache(maxsize=4)
def _load_intent_model(path_str: str) -> Optional[IntentModel]:
    path = Path(path_str)
    return IntentModel.load(path) if path.exists() else None


def route(
    text: str,
    *,
    intent_model: Optional[IntentModel] = None,
    model_path: Path = DEFAULT_INTENT_MODEL_PATH,
    knowledge_index_path: Path = DEFAULT_KNOWLEDGE_INDEX_PATH,
    use_legacy_snapshot: Optional[bool] = None,
) -> RouteResult:
    """Run the v0.3 hybrid adapter on `text` and return packet + plan.

    Pass `intent_model` to inject one explicitly (tests / pinned models).
    Otherwise the deployed model at `model_path` is used if present; if it is
    missing, the adapter runs markers-only.

    `use_legacy_snapshot` gates the exact-match memorization snapshot in
    extract_semantic_packet (None -> baseline.LEGACY_SNAPSHOT_DEFAULT).
    """
    model = (
        intent_model
        if intent_model is not None
        else _load_intent_model(str(model_path))
    )
    trace: Dict[str, Any] = {"adapter_version": ADAPTER_VERSION}
    packet = extract_semantic_packet(
        text, model, trace=trace, use_legacy_snapshot=use_legacy_snapshot
    )
    guard = derive_failure_guard(text, packet)
    retrieval = build_retrieval_packet(text, index_path=knowledge_index_path)
    trace["failure_guard"] = guard.as_dict()
    trace["retrieval"] = retrieval.as_dict()
    plan = build_processing_plan(packet)
    return RouteResult(packet=packet, plan=plan, retrieval=retrieval, trace=trace)
