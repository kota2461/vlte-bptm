import logging
from typing import Any, Mapping, Optional

from .action_vector import (
    ACTION_VECTOR_SCHEMA_VERSION,
    ActionVector,
)
from .encoder import encode
from .integrator import DEFAULT_INHIBITION_MATRIX, integrate
from .hybrid import build_hybrid_stack_mesh
from .mesh import build_horizontal_mesh
from .order_builder import build_llm_order
from .selector import DEFAULT_UNIT_SELECTION_POLICY, select_units
from .state import PipelineMetrics, PipelineState, TraceStage
from .units import DEFAULT_UNITS
from .vertical_stack import (
    build_vertical_stack,
    evaluate_vertical_outputs,
)


PIPELINE_VERSION = "1.6"
OUTPUT_SCHEMA_VERSION = "vlte-bptm.pipeline.v1"
LOGGER = logging.getLogger("thought_core")


def process(
    user_input: str,
    inhibition_matrix: Mapping[str, Mapping[str, float]] = (
        DEFAULT_INHIBITION_MATRIX
    ),
    threshold_profile: Optional[str] = None,
    processing_mode: str = "horizontal",
    vertical_root_mode: Optional[str] = None,
    vertical_outputs: Optional[Mapping[str, Mapping[str, Any]]] = None,
    hybrid_outputs: Optional[
        Mapping[str, Mapping[str, Mapping[str, Any]]]
    ] = None,
) -> PipelineState:
    if processing_mode not in {"horizontal", "vertical", "hybrid"}:
        raise ValueError(
            "processing_mode must be horizontal, vertical, or hybrid"
        )
    if processing_mode != "vertical" and vertical_outputs is not None:
        raise ValueError(
            "vertical_outputs require processing_mode='vertical'"
        )
    if processing_mode != "vertical" and vertical_root_mode is not None:
        raise ValueError(
            "vertical_root_mode requires processing_mode='vertical'"
        )
    if processing_mode != "hybrid" and hybrid_outputs is not None:
        raise ValueError(
            "hybrid_outputs require processing_mode='hybrid'"
        )
    encoded = encode(user_input, threshold_profile=threshold_profile)
    selected = select_units(encoded, DEFAULT_UNITS)
    integrated = integrate(selected, inhibition_matrix)
    horizontal_mesh = build_horizontal_mesh(integrated, DEFAULT_UNITS)
    action_vector = ActionVector(horizontal_mesh.votes)
    vertical_stack = None
    vertical_progress = None
    hybrid_decision = None
    selected_mode = horizontal_mesh.winning_mode
    instruction_override = None
    if processing_mode == "vertical":
        root_mode = vertical_root_mode or horizontal_mesh.winning_mode
        vertical_stack = build_vertical_stack(
            root_mode,
            integrated,
        )
        vertical_progress = evaluate_vertical_outputs(
            vertical_stack,
            vertical_outputs or {},
        )
        if vertical_progress.status == "waiting":
            selected_mode = vertical_progress.next_unit_id
            order = " -> ".join(vertical_stack.execution_order)
            next_unit = vertical_progress.next_unit_id
            instruction_override = (
                f"Execute the vertical unit stack in order: {order}. "
                f"Execute only the next unit, {next_unit}, and return output "
                "matching its contract. Do not execute later units before "
                "this output is validated."
            )
        elif vertical_progress.status == "completed":
            selected_mode = vertical_stack.final_mode
            instruction_override = (
                "All vertical unit outputs passed their contracts. No "
                "further unit dispatch is required; use the validated "
                f"{vertical_stack.root_unit_id} output held by the external "
                "executor without introducing new assumptions."
            )
        else:
            selected_mode = (
                "clarify"
                if vertical_progress.stop_reason
                == "unresolved_clarification"
                else "verify"
            )
            instruction_override = (
                "Stop vertical execution because "
                f"{vertical_progress.stop_reason}. Do not execute later "
                "units; report the failed contract or request the missing "
                "clarification."
            )
    elif processing_mode == "hybrid":
        hybrid_decision = build_hybrid_stack_mesh(
            integrated,
            horizontal_mesh,
            outputs=hybrid_outputs,
        )
        selected_mode = hybrid_decision.final_mode
        if hybrid_decision.status == "waiting":
            dispatch = hybrid_decision.next_dispatch
            instruction_override = (
                "Execute only the next Hybrid Stack-Mesh unit: "
                f"stack {dispatch['stack_id']}, unit "
                f"{dispatch['unit_id']}. Return its output under that "
                "stack namespace and do not execute another unit in the "
                "same call."
            )
        elif hybrid_decision.status == "completed":
            instruction_override = (
                "Hybrid Stack-Mesh integration completed. No further unit "
                "dispatch is required; use the validated output from stack "
                f"{hybrid_decision.winning_stack_id} held by the external "
                "executor without introducing new assumptions."
            )
        else:
            instruction_override = (
                "Hybrid Stack-Mesh stopped with fallback reason "
                f"{hybrid_decision.stop_reason}. Do not execute additional "
                "stacks; use the declared fallback mode."
            )
    metrics = PipelineMetrics(
        active_bit_count=encoded.thought_code.active_bit_count,
        active_bit_density=encoded.thought_code.active_bit_density,
        selected_unit_count=len(integrated),
        threshold_profile=encoded.threshold_profile.name,
    )
    metadata = {
        "selected_unit_ids": [unit.unit_id for unit in integrated],
        "pipeline_version": PIPELINE_VERSION,
        "processing_mode": processing_mode,
        "threshold_profile": encoded.threshold_profile.name,
        "horizontal_mesh_schema_version": (
            horizontal_mesh.as_dict()["schema_version"]
        ),
        "horizontal_mesh_winning_axis": horizontal_mesh.winning_axis,
    }
    if vertical_stack is not None:
        metadata.update(
            {
                "vertical_stack_schema_version": (
                    vertical_stack.as_dict()["schema_version"]
                ),
                "vertical_stack_status": vertical_stack.status,
                "vertical_stack_root_mode": vertical_stack.root_mode,
                "vertical_stack_root_origin": (
                    "processing_plan"
                    if vertical_root_mode is not None
                    else "horizontal_mesh"
                ),
                "vertical_stack_root_unit_id": (
                    vertical_stack.root_unit_id
                ),
                "vertical_stack_progress_status": (
                    vertical_progress.status
                ),
                "vertical_stack_execution_order": list(
                    vertical_stack.execution_order
                ),
                "vertical_stack_next_unit_id": (
                    vertical_progress.next_unit_id
                ),
                "vertical_stack_stop_reason": (
                    vertical_progress.stop_reason
                ),
            }
        )
    if hybrid_decision is not None:
        metadata.update(
            {
                "hybrid_stack_mesh_schema_version": (
                    hybrid_decision.as_dict()["schema_version"]
                ),
                "hybrid_status": hybrid_decision.status,
                "hybrid_used_stacks": hybrid_decision.used_stacks,
                "hybrid_used_steps": hybrid_decision.used_steps,
                "hybrid_next_dispatch": hybrid_decision.next_dispatch,
                "hybrid_winning_stack_id": (
                    hybrid_decision.winning_stack_id
                ),
                "hybrid_stop_reason": hybrid_decision.stop_reason,
            }
        )
    llm_order = build_llm_order(
        user_input=user_input,
        thought_code=encoded.thought_code,
        action_vector=action_vector,
        metadata=metadata,
        selected_mode=selected_mode,
        instruction_override=instruction_override,
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
                "score_components": {
                    unit.unit_id: {
                        name: round(value, 6)
                        for name, value in unit.score_components.items()
                    }
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
        TraceStage(
            stage="horizontal_mesh",
            data={
                "winning_axis": horizontal_mesh.winning_axis,
                "winning_mode": horizontal_mesh.winning_mode,
                "votes": {
                    axis: round(value, 6)
                    for axis, value in horizontal_mesh.votes.items()
                },
            },
        ),
    ]
    if vertical_stack is not None:
        trace.append(
            TraceStage(
                stage="vertical_stack",
                data={
                    "status": vertical_stack.status,
                    "progress_status": vertical_progress.status,
                    "root_unit_id": vertical_stack.root_unit_id,
                    "execution_order": list(
                        vertical_stack.execution_order
                    ),
                    "next_unit_id": vertical_progress.next_unit_id,
                    "stop_reason": vertical_progress.stop_reason,
                },
            )
        )
    if hybrid_decision is not None:
        trace.append(
            TraceStage(
                stage="hybrid_stack_mesh",
                data={
                    "status": hybrid_decision.status,
                    "used_stacks": hybrid_decision.used_stacks,
                    "used_steps": hybrid_decision.used_steps,
                    "next_dispatch": hybrid_decision.next_dispatch,
                    "winning_stack_id": (
                        hybrid_decision.winning_stack_id
                    ),
                    "stop_reason": hybrid_decision.stop_reason,
                },
            )
        )
    trace.extend(
        [
            TraceStage(stage="action_vector", data=action_vector.as_dict()),
            TraceStage(
                stage="llm_order",
                data={"mode": llm_order["mode"]},
            ),
        ]
    )

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
        vertical_stack=(
            {
                **vertical_stack.as_dict(),
                "progress": vertical_progress.as_dict(),
            }
            if vertical_stack is not None
            else None
        ),
        hybrid_stack_mesh=(
            hybrid_decision.as_dict()
            if hybrid_decision is not None
            else None
        ),
        action_vector=action_vector.as_dict(),
        action_vector_schema_version=ACTION_VECTOR_SCHEMA_VERSION,
        horizontal_mesh=horizontal_mesh.as_dict(),
        llm_order=llm_order,
        metrics=metrics,
        trace=trace,
        diagnostics={
            "processing_mode": processing_mode,
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
                "unit_selection_policy": (
                    DEFAULT_UNIT_SELECTION_POLICY.as_dict()
                ),
            },
            "feature_buffer": encoded.feature_buffer.summary(),
            "inhibition_matrix": {
                source: dict(targets)
                for source, targets in inhibition_matrix.items()
            },
        },
    )
