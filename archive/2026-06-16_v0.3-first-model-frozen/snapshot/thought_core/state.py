from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .bits import ThoughtCode


@dataclass(frozen=True)
class TraceStage:
    stage: str
    data: dict

    def as_dict(self) -> dict:
        return {"stage": self.stage, "data": self.data}


@dataclass(frozen=True)
class UnitActivation:
    unit_id: str
    label: str
    raw_score: float
    integrated_score: float
    pattern_shape: Tuple[int, int, int]
    unit_type: str = ""
    channel_schema: str = ""
    channel_schema_version: str = ""
    channel_semantics: str = ""
    prototype_channels: Tuple[int, ...] = ()
    catalog_schema_version: str = ""
    process_mode: str = "horizontal"
    inhibited_by: Dict[str, float] = field(default_factory=dict)
    score_components: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "unit_id": self.unit_id,
            "label": self.label,
            "raw_score": round(self.raw_score, 6),
            "integrated_score": round(self.integrated_score, 6),
            "pattern_shape": list(self.pattern_shape),
            "unit_type": self.unit_type,
            "channel_schema": self.channel_schema,
            "channel_schema_version": self.channel_schema_version,
            "channel_semantics": self.channel_semantics,
            "prototype_channels": list(self.prototype_channels),
            "catalog_schema_version": self.catalog_schema_version,
            "process_mode": self.process_mode,
            "inhibited_by": {
                source: round(amount, 6)
                for source, amount in sorted(self.inhibited_by.items())
            },
            "score_components": {
                name: round(value, 6)
                for name, value in sorted(self.score_components.items())
            },
        }


@dataclass(frozen=True)
class PipelineMetrics:
    active_bit_count: int
    active_bit_density: float
    selected_unit_count: int
    threshold_profile: str

    def as_dict(self) -> dict:
        return {
            "active_bit_count": self.active_bit_count,
            "active_bit_density": round(self.active_bit_density, 6),
            "selected_unit_count": self.selected_unit_count,
            "threshold_profile": self.threshold_profile,
        }


@dataclass
class PipelineState:
    schema_version: str
    pipeline_version: str
    user_input: str
    thought_code: ThoughtCode
    active_bits: Tuple[int, ...]
    selected_units: List[UnitActivation]
    horizontal_mesh: dict
    vertical_stack: Optional[dict]
    hybrid_stack_mesh: Optional[dict]
    action_vector: Dict[str, float]
    action_vector_schema_version: str
    llm_order: dict
    metrics: PipelineMetrics
    trace: List[TraceStage] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "pipeline_version": self.pipeline_version,
            "input": self.user_input,
            "thought_code": self.thought_code.as_dict(),
            "active_bits": list(self.active_bits),
            "selected_units": [
                activation.as_dict() for activation in self.selected_units
            ],
            "horizontal_mesh": self.horizontal_mesh,
            **(
                {"vertical_stack": self.vertical_stack}
                if self.vertical_stack is not None
                else {}
            ),
            **(
                {"hybrid_stack_mesh": self.hybrid_stack_mesh}
                if self.hybrid_stack_mesh is not None
                else {}
            ),
            "action_vector": {
                name: round(value, 6)
                for name, value in self.action_vector.items()
            },
            "action_vector_schema_version": (
                self.action_vector_schema_version
            ),
            "llm_order": self.llm_order,
            "metrics": self.metrics.as_dict(),
            "trace": [stage.as_dict() for stage in self.trace],
            "diagnostics": self.diagnostics,
        }
