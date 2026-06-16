from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

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
    catalog = units_by_id(units)
    totals = {axis: 0.0 for axis in ACTION_AXES}

    for activation in integrated_units:
        unit = catalog[activation.unit_id]
        for axis, weight in unit.action_weights.items():
            if axis not in totals:
                raise ValueError(f"unknown action axis: {axis}")
            totals[axis] += activation.integrated_score * weight

    peak = max(totals.values(), default=0.0)
    if peak == 0.0:
        totals["reply"] = 1.0
    elif peak > 1.0:
        totals = {axis: value / peak for axis, value in totals.items()}

    return ActionVector(totals)
