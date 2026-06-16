"""Validated shadow bridge from Processing Plan to VLTE-BPTM Core."""

from dataclasses import dataclass
from typing import Any, Dict

from thought_core.pipeline import process

from .processing_plan import ProcessingPlan
from .semantic_packet import SemanticPacket, request_digest


CORE_SHADOW_RESULT_SCHEMA_VERSION = "core-shadow-result.v1"


@dataclass(frozen=True)
class CoreShadowResult:
    request_digest: str
    processing_plan: ProcessingPlan
    pipeline_state: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": CORE_SHADOW_RESULT_SCHEMA_VERSION,
            "request_digest": self.request_digest,
            "processing_plan": self.processing_plan.as_dict(),
            "pipeline_state": dict(self.pipeline_state),
        }


def run_core_shadow(
    user_input: str,
    packet: SemanticPacket,
    plan: ProcessingPlan,
) -> CoreShadowResult:
    """Execute the Core mode selected by a validated Processing Plan."""

    if not isinstance(user_input, str):
        raise TypeError("user_input must be a string")
    if not isinstance(packet, SemanticPacket):
        raise TypeError("packet must be a validated SemanticPacket")
    if not isinstance(plan, ProcessingPlan):
        raise TypeError("plan must be a validated ProcessingPlan")
    digest = request_digest(user_input)
    if digest != packet.request_digest:
        raise ValueError("user_input digest does not match SemanticPacket")
    if plan.primary_route != packet.primary_intent:
        raise ValueError("ProcessingPlan route does not match SemanticPacket")

    pipeline = process(
        user_input,
        processing_mode=plan.core_mode,
        vertical_root_mode=(
            plan.primary_route if plan.core_mode == "vertical" else None
        ),
    )
    return CoreShadowResult(
        request_digest=digest,
        processing_plan=plan,
        pipeline_state=pipeline.as_dict(),
    )
