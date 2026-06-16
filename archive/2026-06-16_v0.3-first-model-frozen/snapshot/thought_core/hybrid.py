import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .mesh import HorizontalMeshDecision
from .order_builder import MODE_INSTRUCTIONS
from .state import UnitActivation
from .units import DEFAULT_UNITS
from .vertical_stack import (
    DEFAULT_VERTICAL_STACK_CONFIG,
    VerticalStackConfig,
    build_vertical_stack,
    evaluate_vertical_outputs,
)


HYBRID_STACK_MESH_SCHEMA_VERSION = "hybrid-stack-mesh.v1"
HYBRID_EVALUATION_SCHEMA_VERSION = "hybrid-stack-mesh-evaluation.v1"
DEFAULT_HYBRID_STACK_MESH_PATH = (
    Path(__file__).resolve().parent / "config" / "hybrid_stack_mesh.json"
)
_UNIT_TO_MODE = {
    "clarify": "clarify",
    "verify": "verify",
    "build": "build",
    "summarize": "summarize",
    "explore": "explore",
    "respond": "respond",
}


@dataclass(frozen=True)
class HybridBudget:
    max_stacks: int
    max_total_steps: int
    max_stack_depth: int
    max_dispatches_per_call: int


@dataclass(frozen=True)
class HybridConfig:
    candidate_score_method: str
    candidate_unit_priority: Tuple[str, ...]
    control_candidate_units: Tuple[str, ...]
    fallback_candidate_units: Tuple[str, ...]
    relative_score_threshold: float
    minimum_score: float
    exclude_dependency_roots: bool
    budget: HybridBudget
    scheduler: str
    integrator: str
    fallback_mode_by_reason: Mapping[str, str]


@dataclass(frozen=True)
class HybridDecision:
    status: str
    considered_candidates: Tuple[Mapping[str, Any], ...]
    stacks: Tuple[Mapping[str, Any], ...]
    next_dispatch: Optional[Mapping[str, str]]
    winning_stack_id: Optional[str]
    final_mode: str
    stop_reason: Optional[str]
    used_stacks: int
    used_steps: int
    config: HybridConfig

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": HYBRID_STACK_MESH_SCHEMA_VERSION,
            "status": self.status,
            "candidate_score_method": self.config.candidate_score_method,
            "scheduler": self.config.scheduler,
            "integrator": self.config.integrator,
            "relative_score_threshold": (
                self.config.relative_score_threshold
            ),
            "minimum_score": self.config.minimum_score,
            "budgets": {
                "max_stacks": self.config.budget.max_stacks,
                "max_total_steps": self.config.budget.max_total_steps,
                "max_stack_depth": self.config.budget.max_stack_depth,
                "max_dispatches_per_call": (
                    self.config.budget.max_dispatches_per_call
                ),
                "used_stacks": self.used_stacks,
                "used_steps": self.used_steps,
            },
            "considered_candidates": [
                dict(candidate) for candidate in self.considered_candidates
            ],
            "stacks": [dict(stack) for stack in self.stacks],
            "next_dispatch": (
                dict(self.next_dispatch)
                if self.next_dispatch is not None
                else None
            ),
            "winning_stack_id": self.winning_stack_id,
            "final_mode": self.final_mode,
            "stop_reason": self.stop_reason,
        }


def _string_list(value: Any, field: str) -> Tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{field} must contain unique non-empty strings")
    return tuple(value)


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _unit_depth(plan: Any) -> int:
    return max(
        (int(step["depth"]) for step in plan.steps),
        default=0,
    ) + 1


def load_hybrid_config(
    path: Optional[Path] = None,
    vertical_config: VerticalStackConfig = DEFAULT_VERTICAL_STACK_CONFIG,
) -> HybridConfig:
    config_path = path or DEFAULT_HYBRID_STACK_MESH_PATH
    payload: Any = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("hybrid config must be an object")
    if payload.get("schema_version") != HYBRID_STACK_MESH_SCHEMA_VERSION:
        raise ValueError("unsupported hybrid stack mesh schema")
    if (
        payload.get("candidate_score_method")
        != "integrated_score_plus_covered_dependency_scores"
    ):
        raise ValueError("unsupported hybrid candidate score method")

    known_units = {unit.unit_id for unit in DEFAULT_UNITS}
    priority = _string_list(
        payload.get("candidate_unit_priority"),
        "candidate_unit_priority",
    )
    control = _string_list(
        payload.get("control_candidate_units"),
        "control_candidate_units",
    )
    fallback = _string_list(
        payload.get("fallback_candidate_units"),
        "fallback_candidate_units",
    )
    if set(priority) != known_units:
        raise ValueError("candidate priority must cover every Pattern Unit")
    if set(control) | set(fallback) != known_units:
        raise ValueError("hybrid candidate groups must cover every Pattern Unit")
    if set(control) & set(fallback):
        raise ValueError("hybrid candidate groups must be disjoint")
    if set(known_units) != set(_UNIT_TO_MODE):
        raise ValueError("hybrid unit to mode mapping is incomplete")

    relative = payload.get("relative_score_threshold")
    minimum = payload.get("minimum_score")
    for value, field in (
        (relative, "relative_score_threshold"),
        (minimum, "minimum_score"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0.0 <= value <= 1.0
        ):
            raise ValueError(f"{field} must be in [0, 1]")
    if payload.get("exclude_dependency_roots") is not True:
        raise ValueError("exclude_dependency_roots must be true")

    budgets = payload.get("budgets")
    if not isinstance(budgets, dict):
        raise ValueError("hybrid budgets must be an object")
    budget = HybridBudget(
        max_stacks=_positive_int(budgets.get("max_stacks"), "max_stacks"),
        max_total_steps=_positive_int(
            budgets.get("max_total_steps"),
            "max_total_steps",
        ),
        max_stack_depth=_positive_int(
            budgets.get("max_stack_depth"),
            "max_stack_depth",
        ),
        max_dispatches_per_call=_positive_int(
            budgets.get("max_dispatches_per_call"),
            "max_dispatches_per_call",
        ),
    )
    if budget.max_dispatches_per_call != 1:
        raise ValueError("v1.4 allows exactly one dispatch per call")
    if budget.max_stack_depth > vertical_config.max_depth:
        raise ValueError("hybrid stack depth exceeds vertical max_depth")

    if payload.get("scheduler") != "candidate_score_then_priority":
        raise ValueError("unsupported hybrid scheduler")
    if payload.get("integrator") != "completed_highest_candidate_score":
        raise ValueError("unsupported hybrid integrator")
    fallback_modes = payload.get("fallback_mode_by_reason")
    if not isinstance(fallback_modes, dict) or not fallback_modes:
        raise ValueError("fallback_mode_by_reason must be an object")
    if any(
        not isinstance(reason, str)
        or not reason
        or mode not in MODE_INSTRUCTIONS
        for reason, mode in fallback_modes.items()
    ):
        raise ValueError("hybrid fallback modes must be valid")

    return HybridConfig(
        candidate_score_method=payload["candidate_score_method"],
        candidate_unit_priority=priority,
        control_candidate_units=control,
        fallback_candidate_units=fallback,
        relative_score_threshold=float(relative),
        minimum_score=float(minimum),
        exclude_dependency_roots=True,
        budget=budget,
        scheduler=payload["scheduler"],
        integrator=payload["integrator"],
        fallback_mode_by_reason=dict(fallback_modes),
    )


DEFAULT_HYBRID_CONFIG = load_hybrid_config()


def _candidate_pool(
    activations: Sequence[UnitActivation],
    config: HybridConfig,
) -> Tuple[UnitActivation, ...]:
    by_id = {activation.unit_id: activation for activation in activations}
    control = tuple(
        by_id[unit_id]
        for unit_id in config.control_candidate_units
        if unit_id in by_id
        and by_id[unit_id].integrated_score >= config.minimum_score
    )
    if control:
        return control
    return tuple(
        by_id[unit_id]
        for unit_id in config.fallback_candidate_units
        if unit_id in by_id
        and by_id[unit_id].integrated_score >= config.minimum_score
    )


def _priority_rank(config: HybridConfig) -> Dict[str, int]:
    return {
        unit_id: rank
        for rank, unit_id in enumerate(config.candidate_unit_priority)
    }


def _sorted_candidates(
    candidates: Sequence[UnitActivation],
    config: HybridConfig,
) -> Tuple[UnitActivation, ...]:
    ranks = _priority_rank(config)
    return tuple(
        sorted(
            candidates,
            key=lambda activation: (
                -activation.integrated_score,
                ranks[activation.unit_id],
            ),
        )
    )


def _candidate_descriptors(
    candidates: Sequence[UnitActivation],
    activations: Sequence[UnitActivation],
    config: HybridConfig,
    vertical_config: VerticalStackConfig,
) -> Tuple[Mapping[str, Any], ...]:
    by_id = {candidate.unit_id: candidate for candidate in candidates}
    ranks = _priority_rank(config)
    descriptors = []
    for candidate in candidates:
        plan = build_vertical_stack(
            _UNIT_TO_MODE[candidate.unit_id],
            activations,
            vertical_config,
        )
        covered_ids = tuple(
            unit_id
            for unit_id in plan.execution_order
            if unit_id in by_id
        )
        selection_score = sum(
            by_id[unit_id].integrated_score for unit_id in covered_ids
        )
        descriptors.append(
            {
                "activation": candidate,
                "plan": plan,
                "covered_unit_ids": covered_ids,
                "selection_score": selection_score,
            }
        )
    return tuple(
        sorted(
            descriptors,
            key=lambda descriptor: (
                -descriptor["selection_score"],
                -descriptor["activation"].integrated_score,
                ranks[descriptor["activation"].unit_id],
            ),
        )
    )


def build_hybrid_stack_mesh(
    activations: Sequence[UnitActivation],
    horizontal_mesh: HorizontalMeshDecision,
    outputs: Optional[
        Mapping[str, Mapping[str, Mapping[str, Any]]]
    ] = None,
    config: HybridConfig = DEFAULT_HYBRID_CONFIG,
    vertical_config: VerticalStackConfig = DEFAULT_VERTICAL_STACK_CONFIG,
) -> HybridDecision:
    if outputs is None:
        outputs = {}
    if not isinstance(outputs, Mapping):
        raise ValueError("hybrid outputs must be an object keyed by stack id")

    pool = _candidate_pool(activations, config)
    pool_ids = {activation.unit_id for activation in pool}
    has_control_pool = any(
        unit_id in pool_ids for unit_id in config.control_candidate_units
    )
    descriptors = _candidate_descriptors(
        pool,
        activations,
        config,
        vertical_config,
    )
    top_score = max(
        (
            descriptor["activation"].integrated_score
            for descriptor in descriptors
        ),
        default=0.0,
    )
    relative_floor = top_score * config.relative_score_threshold

    considered = []
    selected = []
    covered_by_selected = set()
    used_steps = 0
    for descriptor in descriptors:
        activation = descriptor["activation"]
        plan = descriptor["plan"]
        covered_unit_ids = descriptor["covered_unit_ids"]
        selection_score = descriptor["selection_score"]
        unit_id = activation.unit_id
        root_score = activation.integrated_score
        mode = _UNIT_TO_MODE[unit_id]
        cost = len(plan.execution_order)
        depth = _unit_depth(plan)
        reason = "selected"
        is_selected = True
        if unit_id in covered_by_selected:
            reason = "covered_by_selected_dependency"
            is_selected = False
        elif root_score < relative_floor:
            reason = "below_relative_threshold"
            is_selected = False
        elif len(selected) >= config.budget.max_stacks:
            reason = "stack_budget_exceeded"
            is_selected = False
        elif depth > config.budget.max_stack_depth:
            reason = "depth_budget_exceeded"
            is_selected = False
        elif used_steps + cost > config.budget.max_total_steps:
            reason = "step_budget_exceeded"
            is_selected = False
        if is_selected:
            selected.append((activation, plan, selection_score))
            covered_by_selected.update(covered_unit_ids)
            used_steps += cost
        considered.append(
            {
                "unit_id": unit_id,
                "mode": mode,
                "root_score": round(root_score, 6),
                "selection_score": round(selection_score, 6),
                "covered_unit_ids": list(covered_unit_ids),
                "planned_steps": cost,
                "planned_depth": depth,
                "selected": is_selected,
                "reason": reason,
            }
        )
    for activation in _sorted_candidates(
        [
            activation
            for activation in activations
            if activation.unit_id not in pool_ids
        ],
        config,
    ):
        if activation.integrated_score < config.minimum_score:
            reason = "below_minimum_score"
        elif (
            has_control_pool
            and activation.unit_id in config.fallback_candidate_units
        ):
            reason = "fallback_suppressed_by_control_candidates"
        else:
            reason = "not_eligible"
        considered.append(
            {
                "unit_id": activation.unit_id,
                "mode": _UNIT_TO_MODE[activation.unit_id],
                "root_score": round(activation.integrated_score, 6),
                "selection_score": round(
                    activation.integrated_score,
                    6,
                ),
                "covered_unit_ids": [activation.unit_id],
                "planned_steps": 0,
                "planned_depth": 0,
                "selected": False,
                "reason": reason,
            }
        )

    selected_ids = {
        activation.unit_id
        for activation, _plan, _selection_score in selected
    }
    unknown_outputs = set(outputs) - selected_ids
    if unknown_outputs:
        raise ValueError(
            "hybrid output provided for unselected stack: "
            f"{sorted(unknown_outputs)[0]}"
        )

    stack_records = []
    completed = []
    waiting = []
    blocked = []
    for rank, (activation, plan, selection_score) in enumerate(selected):
        stack_outputs = outputs.get(activation.unit_id, {})
        if not isinstance(stack_outputs, Mapping):
            raise ValueError(
                f"hybrid stack outputs for {activation.unit_id} "
                "must be an object"
            )
        progress = evaluate_vertical_outputs(
            plan,
            stack_outputs,
            vertical_config,
        )
        record = {
            "stack_id": activation.unit_id,
            "rank": rank,
            "candidate_score": round(selection_score, 6),
            "root_score": round(activation.integrated_score, 6),
            "plan": plan.as_dict(),
            "progress": progress.as_dict(),
        }
        stack_records.append(record)
        if progress.status == "completed":
            completed.append(record)
        elif progress.status == "waiting":
            waiting.append(record)
        else:
            blocked.append(record)

    next_dispatch = None
    winning_stack_id = None
    stop_reason = None
    if waiting:
        chosen = waiting[0]
        next_dispatch = {
            "stack_id": chosen["stack_id"],
            "unit_id": chosen["progress"]["next_unit_id"],
        }
        status = "waiting"
        final_mode = chosen["progress"]["next_unit_id"]
    elif completed:
        winner = min(
            completed,
            key=lambda record: (
                -record["candidate_score"],
                record["rank"],
            ),
        )
        status = "completed"
        winning_stack_id = winner["stack_id"]
        final_mode = _UNIT_TO_MODE[winner["stack_id"]]
    else:
        status = "fallback"
        if blocked:
            stop_reason = blocked[0]["progress"]["stop_reason"]
        else:
            stop_reason = (
                "budget_exhausted" if pool else "no_eligible_candidates"
            )
        final_mode = config.fallback_mode_by_reason.get(
            stop_reason,
            horizontal_mesh.winning_mode,
        )

    return HybridDecision(
        status=status,
        considered_candidates=tuple(considered),
        stacks=tuple(stack_records),
        next_dispatch=next_dispatch,
        winning_stack_id=winning_stack_id,
        final_mode=final_mode,
        stop_reason=stop_reason,
        used_stacks=len(selected),
        used_steps=used_steps,
        config=config,
    )


def evaluate_hybrid_candidate_coverage(
    cases: Sequence[Mapping[str, Any]],
    config: HybridConfig = DEFAULT_HYBRID_CONFIG,
) -> Dict[str, Any]:
    if not cases:
        raise ValueError("at least one hybrid evaluation case is required")
    horizontal_hits = 0
    hybrid_hits = 0
    required_total = 0
    results = []
    for case in cases:
        required = case.get("required_root_units")
        activations = case.get("activations")
        horizontal_root = case.get("horizontal_root_unit")
        if (
            not isinstance(required, list)
            or not required
            or not isinstance(activations, Sequence)
            or not isinstance(horizontal_root, str)
        ):
            raise ValueError("invalid hybrid evaluation case")
        required_set = set(required)
        if any(
            not isinstance(item, UnitActivation)
            for item in activations
        ):
            raise ValueError("hybrid evaluation activations are invalid")
        selected_pool = _candidate_pool(activations, config)
        descriptors = _candidate_descriptors(
            selected_pool,
            activations,
            config,
            DEFAULT_VERTICAL_STACK_CONFIG,
        )
        floor = (
            max(
                descriptor["activation"].integrated_score
                for descriptor in descriptors
            )
            * config.relative_score_threshold
            if descriptors
            else 0.0
        )
        selected_roots = []
        covered_units = set()
        used_steps = 0
        for descriptor in descriptors:
            activation = descriptor["activation"]
            plan = descriptor["plan"]
            cost = len(plan.execution_order)
            if activation.unit_id in covered_units:
                continue
            if activation.integrated_score < floor:
                continue
            if len(selected_roots) >= config.budget.max_stacks:
                continue
            if used_steps + cost > config.budget.max_total_steps:
                continue
            selected_roots.append(activation.unit_id)
            covered_units.update(descriptor["covered_unit_ids"])
            used_steps += cost
        horizontal_case_hits = int(horizontal_root in required_set)
        hybrid_case_hits = len(required_set & covered_units)
        horizontal_hits += horizontal_case_hits
        hybrid_hits += hybrid_case_hits
        required_total += len(required_set)
        results.append(
            {
                "name": case.get("name", ""),
                "required_root_units": sorted(required_set),
                "horizontal_root_unit": horizontal_root,
                "hybrid_root_units": selected_roots,
                "hybrid_covered_units": sorted(covered_units),
                "horizontal_hits": horizontal_case_hits,
                "hybrid_hits": hybrid_case_hits,
                "used_steps": used_steps,
            }
        )
    return {
        "schema_version": HYBRID_EVALUATION_SCHEMA_VERSION,
        "case_count": len(cases),
        "required_branch_count": required_total,
        "horizontal_branch_recall": round(
            horizontal_hits / required_total,
            6,
        ),
        "hybrid_branch_recall": round(
            hybrid_hits / required_total,
            6,
        ),
        "budget_compliant": all(
            result["used_steps"] <= config.budget.max_total_steps
            and len(result["hybrid_root_units"])
            <= config.budget.max_stacks
            for result in results
        ),
        "results": results,
        "interpretation": (
            "This evaluates required candidate-branch coverage under a fixed "
            "budget, not semantic answer quality."
        ),
    }
