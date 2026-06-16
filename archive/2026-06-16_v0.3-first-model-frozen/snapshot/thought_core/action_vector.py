from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Tuple

from .state import UnitActivation
from .units import DEFAULT_UNITS, PatternUnit, units_by_id


ACTION_AXES = (
    "reply",
    "ask",
    "explain",
    "plan",
    "verify",
    "summarize",
    "creative",
    "caution",
)
ACTION_VECTOR_SCHEMA_VERSION = "vlte-bptm.action-vector.v1"


@dataclass(frozen=True)
class ActionVector:
    values: Mapping[str, float]

    def as_dict(self) -> Dict[str, float]:
        return {axis: float(self.values.get(axis, 0.0)) for axis in ACTION_AXES}

    @property
    def dominant_axis(self) -> str:
        return max(ACTION_AXES, key=lambda axis: self.values.get(axis, 0.0))


def build_action_vector(
    integrated_units: Iterable[UnitActivation],
    units: Iterable[PatternUnit] = DEFAULT_UNITS,
) -> ActionVector:
    totals, _contributions = build_action_vote_details(
        integrated_units,
        units,
    )
    return ActionVector(totals)


def build_action_vote_details(
    integrated_units: Iterable[UnitActivation],
    units: Iterable[PatternUnit] = DEFAULT_UNITS,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    catalog = units_by_id(units)
    totals = {axis: 0.0 for axis in ACTION_AXES}
    contributions: Dict[str, Dict[str, float]] = {}

    for activation in integrated_units:
        unit = catalog[activation.unit_id]
        unit_contributions: Dict[str, float] = {}
        for axis, weight in unit.action_weights.items():
            if axis not in totals:
                raise ValueError(f"unknown action axis: {axis}")
            amount = activation.integrated_score * weight
            totals[axis] += amount
            unit_contributions[axis] = amount
        contributions[activation.unit_id] = unit_contributions

    peak = max(totals.values(), default=0.0)
    if peak == 0.0:
        totals["reply"] = 1.0
    elif peak > 1.0:
        totals = {axis: value / peak for axis, value in totals.items()}
        contributions = {
            unit_id: {
                axis: value / peak for axis, value in values.items()
            }
            for unit_id, values in contributions.items()
        }

    return totals, contributions
