import json
import math
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .state import UnitActivation
from .units import DEFAULT_UNITS


# inhibition_matrix[source_unit][target_unit] = suppression coefficient.
# The values live in an external config file (frozen v1.0a contract) so the
# coefficients and their rationale are reviewable without reading code.
INHIBITION_MATRIX_SCHEMA = "inhibition-matrix.v1"
INHIBITION_GROUP_SCHEMA = "inhibition-matrix.v2"
DEFAULT_INHIBITION_MATRIX_PATH = (
    Path(__file__).resolve().parent / "config" / "inhibition_matrix.json"
)
_GROUP_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True)
class InhibitionPolicy:
    schema_version: str
    groups: Mapping[str, tuple[str, ...]]
    matrix: Mapping[str, Mapping[str, float]]


def _validate_matrix(
    inhibition_matrix: Mapping[str, Mapping[str, float]],
) -> None:
    for targets in inhibition_matrix.values():
        for coefficient in targets.values():
            if (
                isinstance(coefficient, bool)
                or not isinstance(coefficient, (int, float))
                or not math.isfinite(coefficient)
                or not 0.0 <= coefficient <= 1.0
            ):
                raise ValueError("inhibition coefficients must be in [0, 1]")


def _validate_config_matrix(
    inhibition_matrix: Mapping[str, Mapping[str, float]],
) -> None:
    known_units = {unit.unit_id for unit in DEFAULT_UNITS}
    for source, targets in inhibition_matrix.items():
        if source not in known_units:
            raise ValueError(f"unknown inhibition source unit: {source}")
        if not isinstance(targets, Mapping):
            raise ValueError(f"inhibition targets for {source} must be an object")
        for target, coefficient in targets.items():
            if target not in known_units:
                raise ValueError(f"unknown inhibition target unit: {target}")
            if source == target:
                raise ValueError("self-inhibition is not supported")
            if (
                isinstance(coefficient, bool)
                or not isinstance(coefficient, (int, float))
                or not math.isfinite(coefficient)
                or not 0.0 <= coefficient <= 1.0
            ):
                raise ValueError("inhibition coefficients must be in [0, 1]")


def _validate_groups(value: Any) -> Dict[str, tuple[str, ...]]:
    if not isinstance(value, dict) or not value:
        raise ValueError("inhibition groups must be a non-empty object")
    known_units = {unit.unit_id for unit in DEFAULT_UNITS}
    groups: Dict[str, tuple[str, ...]] = {}
    assigned = set()
    for group_id, raw_members in value.items():
        if (
            not isinstance(group_id, str)
            or _GROUP_ID_PATTERN.fullmatch(group_id) is None
        ):
            raise ValueError("inhibition group ids must be identifiers")
        if (
            not isinstance(raw_members, list)
            or not raw_members
            or any(not isinstance(item, str) for item in raw_members)
            or len(set(raw_members)) != len(raw_members)
        ):
            raise ValueError(
                f"inhibition group {group_id} must contain unique units"
            )
        unknown = set(raw_members) - known_units
        if unknown:
            raise ValueError(
                f"unknown inhibition group unit: {sorted(unknown)[0]}"
            )
        overlap = assigned & set(raw_members)
        if overlap:
            raise ValueError(
                f"inhibition unit belongs to multiple groups: "
                f"{sorted(overlap)[0]}"
            )
        assigned.update(raw_members)
        groups[group_id] = tuple(raw_members)
    if assigned != known_units:
        missing = sorted(known_units - assigned)
        raise ValueError(
            f"inhibition groups do not cover unit: {missing[0]}"
        )
    return groups


def _expand_group_matrix(
    groups: Mapping[str, tuple[str, ...]],
    value: Any,
) -> Dict[str, Dict[str, float]]:
    if not isinstance(value, dict):
        raise ValueError("group_matrix must be an object")
    expanded: Dict[str, Dict[str, float]] = {}
    for source_group, raw_targets in value.items():
        if source_group not in groups:
            raise ValueError(
                f"unknown inhibition source group: {source_group}"
            )
        if not isinstance(raw_targets, dict):
            raise ValueError(
                f"inhibition targets for group {source_group} "
                "must be an object"
            )
        for target_group, coefficient in raw_targets.items():
            if target_group not in groups:
                raise ValueError(
                    f"unknown inhibition target group: {target_group}"
                )
            if source_group == target_group:
                raise ValueError("self-inhibition groups are not supported")
            if (
                isinstance(coefficient, bool)
                or not isinstance(coefficient, (int, float))
                or not math.isfinite(coefficient)
                or not 0.0 <= coefficient <= 1.0
            ):
                raise ValueError(
                    "inhibition coefficients must be in [0, 1]"
                )
            for source_unit in groups[source_group]:
                for target_unit in groups[target_group]:
                    expanded.setdefault(source_unit, {})[target_unit] = (
                        float(coefficient)
                    )
    return expanded


def load_inhibition_policy(
    path: Optional[Path] = None,
) -> InhibitionPolicy:
    config_path = path or DEFAULT_INHIBITION_MATRIX_PATH
    payload: Any = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("inhibition matrix config must be an object")
    schema_version = payload.get("schema_version")
    if schema_version == INHIBITION_MATRIX_SCHEMA:
        raw_matrix = payload.get("matrix")
        if not isinstance(raw_matrix, dict):
            raise ValueError(
                "inhibition matrix config requires an object matrix"
            )
        _validate_config_matrix(raw_matrix)
        matrix = {
            str(source): {
                str(target): float(coefficient)
                for target, coefficient in targets.items()
            }
            for source, targets in raw_matrix.items()
        }
        groups = {
            unit.unit_id: (unit.unit_id,) for unit in DEFAULT_UNITS
        }
        return InhibitionPolicy(schema_version, groups, matrix)
    if schema_version != INHIBITION_GROUP_SCHEMA:
        raise ValueError(
            "unsupported inhibition matrix schema: "
            f"{schema_version!r}"
        )
    groups = _validate_groups(payload.get("groups"))
    matrix = _expand_group_matrix(groups, payload.get("group_matrix"))
    raw_overrides = payload.get("matrix", {})
    if not isinstance(raw_overrides, dict):
        raise ValueError("inhibition matrix overrides must be an object")
    _validate_config_matrix(raw_overrides)
    for source, targets in raw_overrides.items():
        for target, coefficient in targets.items():
            matrix.setdefault(source, {})[target] = float(coefficient)
    _validate_config_matrix(matrix)
    return InhibitionPolicy(schema_version, groups, matrix)


def load_inhibition_matrix(
    path: Optional[Path] = None,
) -> Dict[str, Dict[str, float]]:
    """Load and validate the inhibition matrix from its JSON config file."""
    policy = load_inhibition_policy(path)
    return {
        source: dict(targets)
        for source, targets in policy.matrix.items()
    }


DEFAULT_INHIBITION_MATRIX: Dict[str, Dict[str, float]] = (
    load_inhibition_matrix()
)
DEFAULT_INHIBITION_POLICY = load_inhibition_policy()


def integrate(
    selected_units: Iterable[UnitActivation],
    inhibition_matrix: Mapping[str, Mapping[str, float]] = (
        DEFAULT_INHIBITION_MATRIX
    ),
) -> List[UnitActivation]:
    """Apply pairwise inhibition simultaneously to selected unit scores."""

    _validate_matrix(inhibition_matrix)
    selected = list(selected_units)
    result: List[UnitActivation] = []

    for target in selected:
        inhibited_by: Dict[str, float] = {}
        for source in selected:
            if source.unit_id == target.unit_id:
                continue
            coefficient = inhibition_matrix.get(source.unit_id, {}).get(
                target.unit_id,
                0.0,
            )
            amount = source.raw_score * coefficient
            if amount > 0.0:
                inhibited_by[source.unit_id] = amount

        integrated_score = max(
            0.0,
            target.raw_score - sum(inhibited_by.values()),
        )
        result.append(
            replace(
                target,
                integrated_score=integrated_score,
                inhibited_by=inhibited_by,
            )
        )

    result.sort(key=lambda item: (-item.integrated_score, item.unit_id))
    return result
