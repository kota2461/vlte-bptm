from dataclasses import dataclass, field
from typing import Dict, List, Tuple

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
    process_mode: str = "horizontal"
    inhibited_by: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "unit_id": self.unit_id,
            "label": self.label,
            "raw_score": round(self.raw_score, 6),
            "integrated_score": round(self.integrated_score, 6),
            "pattern_shape": list(self.pattern_shape),
            "unit_type": self.unit_type,
            "channel_schema": self.channel_schema,
            "process_mode": self.process_mode,
            "inhibited_by": {
                source: round(amount, 6)
                for source, amount in sorted(self.inhibited_by.items())
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
    action_vector: Dict[str, float]
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
            "action_vector": {
                name: round(value, 6)
                for name, value in self.action_vector.items()
            },
            "llm_order": self.llm_order,
            "metrics": self.metrics.as_dict(),
            "trace": [stage.as_dict() for stage in self.trace],
            "diagnostics": self.diagnostics,
        }
