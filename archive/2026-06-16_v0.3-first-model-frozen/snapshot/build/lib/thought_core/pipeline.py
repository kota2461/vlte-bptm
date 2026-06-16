import logging
from typing import Mapping, Optional

from .action_vector import build_action_vector
from .encoder import encode
from .integrator import DEFAULT_INHIBITION_MATRIX, integrate
from .order_builder import build_llm_order
from .selector import select_units
from .state import PipelineMetrics, PipelineState, TraceStage
from .units import DEFAULT_UNITS


PIPELINE_VERSION = "1.0a"
OUTPUT_SCHEMA_VERSION = "vlte-bptm.pipeline.v1"
LOGGER = logging.getLogger("thought_core")


def process(
    user_input: str,
    inhibition_matrix: Mapping[str, Mapping[str, float]] = (
        DEFAULT_INHIBITION_MATRIX
    ),
    threshold_profile: Optional[str] = None,
) -> PipelineState:
    encoded = encode(user_input, threshold_profile=threshold_profile)
    selected = select_units(encoded, DEFAULT_UNITS)
    integrated = integrate(selected, inhibition_matrix)
    action_vector = build_action_vector(integrated, DEFAULT_UNITS)
    metrics = PipelineMetrics(
        active_bit_count=encoded.thought_code.active_bit_count,
        active_bit_density=encoded.thought_code.active_bit_density,
        selected_unit_count=len(integrated),
        threshold_profile=encoded.threshold_profile.name,
    )
    llm_order = build_llm_order(
        user_input=user_input,
        thought_code=encoded.thought_code,
        action_vector=action_vector,
        metadata={
            "selected_unit_ids": [unit.unit_id for unit in integrated],
            "pipeline_version": PIPELINE_VERSION,
            "threshold_profile": encoded.threshold_profile.name,
        },
    )
    trace = [
        TraceStage(
            stage="input",
            data={
                "character_count": len(user_input),
                "utf8_byte_count": len(user_input.encode("utf-8")),
            },
        ),
        TraceStage(
            stage="active_bits",
            data={
                "thought_code": encoded.thought_code.hex(),
                "active_bits": list(encoded.thought_code.active_bits),
                "threshold_profile": encoded.threshold_profile.name,
            },
        ),
        TraceStage(
            stage="selected_units",
            data={
                "unit_ids": [unit.unit_id for unit in selected],
                "raw_scores": {
                    unit.unit_id: round(unit.raw_score, 6)
                    for unit in selected
                },
            },
        ),
        TraceStage(
            stage="inhibition_integration",
            data={
                "unit_ids": [unit.unit_id for unit in integrated],
                "integrated_scores": {
                    unit.unit_id: round(unit.integrated_score, 6)
                    for unit in integrated
                },
            },
        ),
        TraceStage(stage="action_vector", data=action_vector.as_dict()),
        TraceStage(
            stage="llm_order",
            data={"mode": llm_order["mode"]},
        ),
    ]

    LOGGER.info(
        "pipeline_metrics active_bit_count=%d "
        "active_bit_density=%.6f selected_unit_count=%d "
        "threshold_profile=%s",
        metrics.active_bit_count,
        metrics.active_bit_density,
        metrics.selected_unit_count,
        metrics.threshold_profile,
    )

    return PipelineState(
        schema_version=OUTPUT_SCHEMA_VERSION,
        pipeline_version=PIPELINE_VERSION,
        user_input=user_input,
        thought_code=encoded.thought_code,
        active_bits=encoded.thought_code.active_bits,
        selected_units=integrated,
        action_vector=action_vector.as_dict(),
        llm_order=llm_order,
        metrics=metrics,
        trace=trace,
        diagnostics={
            "processing_mode": "horizontal",
            "routing": {
                "threshold_profile": encoded.threshold_profile.name,
                "intensity_threshold": (
                    encoded.threshold_profile.intensity_threshold
                ),
                "density_guard": {
                    "min_active_bits": (
                        encoded.threshold_profile.min_active_bits
                    ),
                    "max_active_bits": (
                        encoded.threshold_profile.max_active_bits
                    ),
                },
                "active_bit_intensities": {
                    str(index): round(encoded.bit_intensities[index], 6)
                    for index in encoded.thought_code.active_bits
                },
            },
            "feature_buffer": encoded.feature_buffer.summary(),
            "inhibition_matrix": {
                source: dict(targets)
                for source, targets in inhibition_matrix.items()
            },
        },
    )
