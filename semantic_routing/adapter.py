"""v0.3 deployment entry — the canonical "run the adapter on text" call.

Ties the hybrid together: deterministic markers first (always win when they
fire) + the deployed learned intent layer on marker no-match, gated by
confidence (baseline.INTENT_GATE_MARGIN), then the deterministic processing
plan. The deployed intent model is loaded by default; if it is absent the
adapter degrades gracefully to markers-only (v0.2 behaviour).

v0.3.2 adds the SIG-64 route CAM (route-cam.v1) as an escalation-only pass
AFTER the decision table: the baseline plan is a floor and an approved CAM
entry can only raise the processing class (max-join). With the shipped
empty store the adapter is byte-identical to v0.3.1.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from .baseline import extract_semantic_packet
from .intent_model import IntentModel
from .processing_plan import ProcessingPlan, build_processing_plan
from .route_cam import (
    DEFAULT_ROUTE_CAM_PATH,
    RouteCamStore,
    apply_route_cam,
    load_route_cam,
)
from .semantic_packet import SemanticPacket
from .signature import build_signature, signature_hex


ADAPTER_VERSION = "0.3.2"

DEFAULT_INTENT_MODEL_PATH = (
    Path(__file__).resolve().parents[1] / "build" / "intent_model_v1.json"
)


@dataclass(frozen=True)
class RouteResult:
    packet: SemanticPacket
    plan: ProcessingPlan
    # observability only (v0.3.1) — how/why the intent was decided;
    # never affects routing decisions
    trace: Dict[str, Any] = field(default_factory=dict)


@lru_cache(maxsize=4)
def _load_intent_model(path_str: str) -> Optional[IntentModel]:
    path = Path(path_str)
    return IntentModel.load(path) if path.exists() else None


@lru_cache(maxsize=4)
def _load_route_cam(path_str: str) -> Optional[RouteCamStore]:
    path = Path(path_str)
    return load_route_cam(path) if path.exists() else None


def route(
    text: str,
    *,
    intent_model: Optional[IntentModel] = None,
    model_path: Path = DEFAULT_INTENT_MODEL_PATH,
    route_cam: Optional[RouteCamStore] = None,
    route_cam_path: Path = DEFAULT_ROUTE_CAM_PATH,
) -> RouteResult:
    """Run the v0.3 hybrid adapter on `text` and return packet + plan.

    Pass `intent_model` to inject one explicitly (tests / pinned models).
    Otherwise the deployed model at `model_path` is used if present; if it is
    missing, the adapter runs markers-only.

    Pass `route_cam` to inject a RouteCamStore (tests / pinned stores).
    Otherwise the store at `route_cam_path` is used if present. An empty (or
    missing) store leaves the plan and trace byte-identical to v0.3.1.
    """
    model = (
        intent_model
        if intent_model is not None
        else _load_intent_model(str(model_path))
    )
    trace: Dict[str, Any] = {"adapter_version": ADAPTER_VERSION}
    packet = extract_semantic_packet(text, model, trace=trace)
    plan = build_processing_plan(packet)
    cam = (
        route_cam
        if route_cam is not None
        else _load_route_cam(str(route_cam_path))
    )
    if cam is not None and len(cam):
        signature = build_signature(packet, text)
        plan, hit, applied = apply_route_cam(packet, plan, cam, signature)
        trace["route_cam"] = {
            "signature": signature_hex(signature),
            "entry_count": len(cam),
            "hit": hit.entry.entry_id if hit is not None else None,
            "distance": hit.distance if hit is not None else None,
            "applied": applied,
        }
    return RouteResult(packet=packet, plan=plan, trace=trace)
