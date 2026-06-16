import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .order_builder import MODE_INSTRUCTIONS
from .state import UnitActivation
from .units import DEFAULT_UNITS


VERTICAL_STACK_SCHEMA_VERSION = "vertical-unit-stack.v1"
VERTICAL_OUTPUT_SCHEMA_VERSION = "vertical-unit-output.v1"
VERTICAL_PROGRESS_SCHEMA_VERSION = "vertical-stack-progress.v1"
DEFAULT_VERTICAL_STACK_PATH = (
    Path(__file__).resolve().parent / "config" / "vertical_stack.json"
)
_FIELD_TYPES = {"array", "boolean", "object", "string"}


@dataclass(frozen=True)
class VerticalOutputContract:
    schema_version: str
    required_fields: Mapping[str, str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "required_fields": dict(self.required_fields),
        }


@dataclass(frozen=True)
class VerticalStackConfig:
    output_schema_version: str
    max_depth: int
    root_unit_by_mode: Mapping[str, str]
    input_dependencies: Mapping[str, Tuple[str, ...]]
    verifier_unit_id: str
    verification_targets: Tuple[str, ...]
    verification_failure_reason: str
    blocking_signal_unit_id: str
    blocking_targets: Tuple[str, ...]
    blocking_minimum_relative_score: float
    blocking_failure_reason: str
    common_output_fields: Mapping[str, str]
    output_contracts: Mapping[str, VerticalOutputContract]
    allowed_output_statuses: Tuple[str, ...]
    stop_reasons: Tuple[str, ...]


@dataclass(frozen=True)
class VerticalStackPlan:
    root_unit_id: str
    root_mode: str
    status: str
    final_mode: str
    execution_order: Tuple[str, ...]
    steps: Tuple[Mapping[str, Any], ...]
    initial_unit_id: Optional[str]
    stop_reason: Optional[str]
    max_depth: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": VERTICAL_STACK_SCHEMA_VERSION,
            "output_schema_version": VERTICAL_OUTPUT_SCHEMA_VERSION,
            "root_unit_id": self.root_unit_id,
            "root_mode": self.root_mode,
            "status": self.status,
            "final_mode": self.final_mode,
            "execution_order": list(self.execution_order),
            "steps": [dict(step) for step in self.steps],
            "initial_unit_id": self.initial_unit_id,
            "stop_reason": self.stop_reason,
            "max_depth": self.max_depth,
        }


@dataclass(frozen=True)
class VerticalStackProgress:
    status: str
    completed_unit_ids: Tuple[str, ...]
    next_unit_id: Optional[str]
    stop_reason: Optional[str]
    failed_unit_id: Optional[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": VERTICAL_PROGRESS_SCHEMA_VERSION,
            "status": self.status,
            "completed_unit_ids": list(self.completed_unit_ids),
            "next_unit_id": self.next_unit_id,
            "stop_reason": self.stop_reason,
            "failed_unit_id": self.failed_unit_id,
        }


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _string_list(value: Any, field: str) -> Tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{field} must contain unique non-empty strings")
    return tuple(value)


def _field_contract(value: Any, field: str) -> Dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{field} must be a non-empty object")
    result: Dict[str, str] = {}
    for name, type_name in value.items():
        field_name = _non_empty_string(name, f"{field}.name")
        if type_name not in _FIELD_TYPES:
            raise ValueError(f"{field_name} has an unsupported field type")
        result[field_name] = type_name
    return result


def _dependency_depth(
    unit_id: str,
    dependencies: Mapping[str, Tuple[str, ...]],
    visiting: Tuple[str, ...] = (),
) -> int:
    if unit_id in visiting:
        cycle = " -> ".join((*visiting, unit_id))
        raise ValueError(f"vertical dependency cycle: {cycle}")
    children = dependencies[unit_id]
    if not children:
        return 1
    return 1 + max(
        _dependency_depth(child, dependencies, (*visiting, unit_id))
        for child in children
    )


def load_vertical_stack_config(
    path: Optional[Path] = None,
) -> VerticalStackConfig:
    config_path = path or DEFAULT_VERTICAL_STACK_PATH
    payload: Any = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("vertical stack config must be an object")
    if payload.get("schema_version") != VERTICAL_STACK_SCHEMA_VERSION:
        raise ValueError("unsupported vertical stack schema")
    if payload.get("output_schema_version") != VERTICAL_OUTPUT_SCHEMA_VERSION:
        raise ValueError("unsupported vertical output schema")

    max_depth = payload.get("max_depth")
    if (
        isinstance(max_depth, bool)
        or not isinstance(max_depth, int)
        or not 1 <= max_depth <= 8
    ):
        raise ValueError("max_depth must be an integer in [1, 8]")

    known_units = {unit.unit_id for unit in DEFAULT_UNITS}
    roots = payload.get("root_unit_by_mode")
    if not isinstance(roots, dict) or set(roots) != set(MODE_INSTRUCTIONS):
        raise ValueError("root_unit_by_mode must cover every LLM Order mode")
    for mode, unit_id in roots.items():
        if unit_id not in known_units:
            raise ValueError(f"unknown root unit for mode {mode}: {unit_id}")

    raw_dependencies = payload.get("input_dependencies")
    if not isinstance(raw_dependencies, dict):
        raise ValueError("input_dependencies must be an object")
    if set(raw_dependencies) != known_units:
        raise ValueError("input_dependencies must cover every Pattern Unit")
    dependencies: Dict[str, Tuple[str, ...]] = {}
    for unit_id, raw_children in raw_dependencies.items():
        children = _string_list(
            raw_children,
            f"input_dependencies.{unit_id}",
        )
        if unit_id in children:
            raise ValueError("vertical stack does not allow self-dependency")
        unknown = set(children) - known_units
        if unknown:
            raise ValueError(
                f"unknown vertical dependency: {sorted(unknown)[0]}"
            )
        dependencies[unit_id] = children
    if max(
        _dependency_depth(unit_id, dependencies)
        for unit_id in known_units
    ) > max_depth:
        raise ValueError("vertical dependency graph exceeds max_depth")

    verification = payload.get("verification_policy")
    if not isinstance(verification, dict):
        raise ValueError("verification_policy must be an object")
    verifier = _non_empty_string(
        verification.get("verifier_unit_id"),
        "verifier_unit_id",
    )
    targets = _string_list(
        verification.get("required_before"),
        "verification_policy.required_before",
    )
    if verifier not in known_units or set(targets) - known_units:
        raise ValueError("verification policy references unknown units")
    for target in targets:
        if verifier not in dependencies[target]:
            raise ValueError(
                f"{target} must directly depend on verifier {verifier}"
            )

    blocking = payload.get("blocking_policy")
    if not isinstance(blocking, dict):
        raise ValueError("blocking_policy must be an object")
    signal_unit = _non_empty_string(
        blocking.get("signal_unit_id"),
        "blocking_policy.signal_unit_id",
    )
    blocking_targets = _string_list(
        blocking.get("blocks_targets"),
        "blocking_policy.blocks_targets",
    )
    if signal_unit not in known_units or set(blocking_targets) - known_units:
        raise ValueError("blocking policy references unknown units")
    minimum_relative_score = blocking.get("minimum_relative_score")
    if (
        isinstance(minimum_relative_score, bool)
        or not isinstance(minimum_relative_score, (int, float))
        or not math.isfinite(minimum_relative_score)
        or not 0.0 <= minimum_relative_score <= 1.0
    ):
        raise ValueError("minimum_relative_score must be in [0, 1]")

    common_fields = _field_contract(
        payload.get("common_output_fields"),
        "common_output_fields",
    )
    if set(common_fields) != {
        "schema_version",
        "unit_id",
        "status",
        "assumptions",
        "evidence",
    }:
        raise ValueError("common_output_fields do not match the v1 contract")

    raw_contracts = payload.get("output_contracts")
    if not isinstance(raw_contracts, dict) or set(raw_contracts) != known_units:
        raise ValueError("output_contracts must cover every Pattern Unit")
    contracts: Dict[str, VerticalOutputContract] = {}
    schemas = set()
    for unit_id, raw_contract in raw_contracts.items():
        if not isinstance(raw_contract, dict):
            raise ValueError(f"output contract for {unit_id} must be an object")
        schema = _non_empty_string(
            raw_contract.get("schema_version"),
            f"output_contracts.{unit_id}.schema_version",
        )
        if schema in schemas:
            raise ValueError("vertical output contract schemas must be unique")
        schemas.add(schema)
        required_fields = _field_contract(
            raw_contract.get("required_fields"),
            f"output_contracts.{unit_id}.required_fields",
        )
        if set(required_fields) & set(common_fields):
            raise ValueError(
                "unit output fields cannot override common output fields"
            )
        contracts[unit_id] = VerticalOutputContract(
            schema_version=schema,
            required_fields=required_fields,
        )

    statuses = _string_list(
        payload.get("allowed_output_statuses"),
        "allowed_output_statuses",
    )
    if statuses != ("completed", "blocked"):
        raise ValueError("allowed_output_statuses must be completed, blocked")
    stop_reasons = _string_list(
        payload.get("stop_reasons"),
        "stop_reasons",
    )
    verification_reason = _non_empty_string(
        verification.get("failure_reason"),
        "verification_policy.failure_reason",
    )
    blocking_reason = _non_empty_string(
        blocking.get("failure_reason"),
        "blocking_policy.failure_reason",
    )
    required_reasons = {
        verification_reason,
        blocking_reason,
        "missing_dependency_output",
        "invalid_output_contract",
        "dependency_failed",
        "unverified_assumption",
    }
    if not required_reasons.issubset(stop_reasons):
        raise ValueError("stop_reasons omit required failure reasons")

    return VerticalStackConfig(
        output_schema_version=payload["output_schema_version"],
        max_depth=max_depth,
        root_unit_by_mode=dict(roots),
        input_dependencies=dependencies,
        verifier_unit_id=verifier,
        verification_targets=targets,
        verification_failure_reason=verification_reason,
        blocking_signal_unit_id=signal_unit,
        blocking_targets=blocking_targets,
        blocking_minimum_relative_score=float(minimum_relative_score),
        blocking_failure_reason=blocking_reason,
        common_output_fields=common_fields,
        output_contracts=contracts,
        allowed_output_statuses=statuses,
        stop_reasons=stop_reasons,
    )


DEFAULT_VERTICAL_STACK_CONFIG = load_vertical_stack_config()


def _execution_order(
    root_unit_id: str,
    dependencies: Mapping[str, Tuple[str, ...]],
) -> Tuple[str, ...]:
    ordered = []
    visited = set()

    def visit(unit_id: str) -> None:
        if unit_id in visited:
            return
        for dependency in dependencies[unit_id]:
            visit(dependency)
        visited.add(unit_id)
        ordered.append(unit_id)

    visit(root_unit_id)
    return tuple(ordered)


def _depths(
    root_unit_id: str,
    dependencies: Mapping[str, Tuple[str, ...]],
) -> Dict[str, int]:
    depths: Dict[str, int] = {}

    def visit(unit_id: str, depth: int) -> None:
        previous = depths.get(unit_id)
        if previous is None or depth < previous:
            depths[unit_id] = depth
        for dependency in dependencies[unit_id]:
            visit(dependency, depth + 1)

    visit(root_unit_id, 0)
    maximum = max(depths.values(), default=0)
    return {unit_id: maximum - depth for unit_id, depth in depths.items()}


def _activation_scores(
    activations: Sequence[UnitActivation],
) -> Dict[str, float]:
    return {
        activation.unit_id: activation.integrated_score
        for activation in activations
    }


def build_vertical_stack(
    root_mode: str,
    activations: Sequence[UnitActivation] = (),
    config: VerticalStackConfig = DEFAULT_VERTICAL_STACK_CONFIG,
) -> VerticalStackPlan:
    try:
        root_unit_id = config.root_unit_by_mode[root_mode]
    except KeyError as error:
        raise ValueError(f"unknown vertical root mode: {root_mode}") from error

    order = _execution_order(root_unit_id, config.input_dependencies)
    depths = _depths(root_unit_id, config.input_dependencies)
    scores = _activation_scores(activations)
    signal_score = scores.get(config.blocking_signal_unit_id, 0.0)
    root_score = scores.get(root_unit_id, 0.0)
    blocked = (
        root_unit_id in config.blocking_targets
        and signal_score > 0.0
        and (
            root_score <= 0.0
            or signal_score
            >= root_score * config.blocking_minimum_relative_score
        )
    )
    stop_reason = config.blocking_failure_reason if blocked else None
    final_mode = "clarify" if blocked else root_mode
    steps = []
    for index, unit_id in enumerate(order):
        dependencies = config.input_dependencies[unit_id]
        if unit_id == root_unit_id:
            role = "target"
        elif unit_id == config.verifier_unit_id:
            role = "verification_gate"
        else:
            role = "dependency"
        steps.append(
            {
                "index": index,
                "depth": depths[unit_id],
                "unit_id": unit_id,
                "role": role,
                "origin": (
                    "selected" if unit_id in scores else "injected"
                ),
                "integrated_score": round(scores.get(unit_id, 0.0), 6),
                "input_dependencies": list(dependencies),
                "output_contract": {
                    "schema_version": config.output_contracts[
                        unit_id
                    ].schema_version,
                    "required_fields": {
                        **config.common_output_fields,
                        **config.output_contracts[
                            unit_id
                        ].required_fields,
                    },
                },
                "status": (
                    "blocked" if blocked else "pending"
                ),
                "reason": stop_reason,
            }
        )
    return VerticalStackPlan(
        root_unit_id=root_unit_id,
        root_mode=root_mode,
        status="blocked" if blocked else "ready",
        final_mode=final_mode,
        execution_order=order,
        steps=tuple(steps),
        initial_unit_id=None if blocked else order[0],
        stop_reason=stop_reason,
        max_depth=config.max_depth,
    )


def _matches_type(value: Any, type_name: str) -> bool:
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "string":
        return isinstance(value, str)
    return False


def _valid_output(
    unit_id: str,
    output: Any,
    config: VerticalStackConfig,
) -> bool:
    if not isinstance(output, Mapping):
        return False
    contract = config.output_contracts[unit_id]
    fields = {
        **config.common_output_fields,
        **contract.required_fields,
    }
    if set(output) != set(fields):
        return False
    if output.get("schema_version") != contract.schema_version:
        return False
    if output.get("unit_id") != unit_id:
        return False
    if output.get("status") not in config.allowed_output_statuses:
        return False
    if not all(
        _matches_type(output[field], type_name)
        for field, type_name in fields.items()
    ):
        return False
    for field, type_name in fields.items():
        if type_name == "array" and any(
            not isinstance(item, str) for item in output[field]
        ):
            return False
    return True


def evaluate_vertical_outputs(
    plan: VerticalStackPlan,
    outputs: Mapping[str, Mapping[str, Any]],
    config: VerticalStackConfig = DEFAULT_VERTICAL_STACK_CONFIG,
) -> VerticalStackProgress:
    if not isinstance(outputs, Mapping):
        raise ValueError("vertical outputs must be an object keyed by unit id")
    unknown = set(outputs) - set(plan.execution_order)
    if unknown:
        raise ValueError(
            f"output provided for unit outside stack: {sorted(unknown)[0]}"
        )
    if plan.status == "blocked":
        return VerticalStackProgress(
            status="blocked",
            completed_unit_ids=(),
            next_unit_id=None,
            stop_reason=plan.stop_reason,
            failed_unit_id=plan.root_unit_id,
        )

    completed = []
    verified_assumptions = set()
    for unit_id in plan.execution_order:
        output = outputs.get(unit_id)
        if output is None:
            return VerticalStackProgress(
                status="waiting",
                completed_unit_ids=tuple(completed),
                next_unit_id=unit_id,
                stop_reason="missing_dependency_output",
                failed_unit_id=None,
            )
        if not _valid_output(unit_id, output, config):
            return VerticalStackProgress(
                status="blocked",
                completed_unit_ids=tuple(completed),
                next_unit_id=None,
                stop_reason="invalid_output_contract",
                failed_unit_id=unit_id,
            )
        if output["status"] != "completed":
            return VerticalStackProgress(
                status="blocked",
                completed_unit_ids=tuple(completed),
                next_unit_id=None,
                stop_reason="dependency_failed",
                failed_unit_id=unit_id,
            )
        if (
            unit_id == config.verifier_unit_id
            and plan.root_unit_id in config.verification_targets
            and output.get("verified") is not True
        ):
            return VerticalStackProgress(
                status="blocked",
                completed_unit_ids=tuple(completed),
                next_unit_id=None,
                stop_reason=config.verification_failure_reason,
                failed_unit_id=unit_id,
            )
        if unit_id == config.verifier_unit_id:
            verified_assumptions.update(
                output.get("verified_assumptions", [])
            )
        if (
            unit_id == plan.root_unit_id
            and unit_id in config.verification_targets
            and not set(output["assumptions"]).issubset(
                verified_assumptions
            )
        ):
            return VerticalStackProgress(
                status="blocked",
                completed_unit_ids=tuple(completed),
                next_unit_id=None,
                stop_reason="unverified_assumption",
                failed_unit_id=unit_id,
            )
        completed.append(unit_id)

    return VerticalStackProgress(
        status="completed",
        completed_unit_ids=tuple(completed),
        next_unit_id=None,
        stop_reason=None,
        failed_unit_id=None,
    )
