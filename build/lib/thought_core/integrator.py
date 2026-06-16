from dataclasses import replace
from typing import Dict, Iterable, List, Mapping

from .state import UnitActivation


# inhibition_matrix[source_unit][target_unit] = suppression coefficient
DEFAULT_INHIBITION_MATRIX: Dict[str, Dict[str, float]] = {
    "build": {"respond": 0.20},
    "clarify": {"build": 0.45, "respond": 0.25},
    "summarize": {"explore": 0.30},
    "verify": {"build": 0.35, "explore": 0.20},
}


def _validate_matrix(
    inhibition_matrix: Mapping[str, Mapping[str, float]],
) -> None:
    for targets in inhibition_matrix.values():
        for coefficient in targets.values():
            if not 0.0 <= coefficient <= 1.0:
                raise ValueError("inhibition coefficients must be in [0, 1]")


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
