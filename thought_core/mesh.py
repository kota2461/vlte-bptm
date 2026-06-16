import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .action_vector import ACTION_AXES, build_action_vote_details
from .state import UnitActivation
from .units import DEFAULT_UNITS, PatternUnit


HORIZONTAL_MESH_SCHEMA_VERSION = "horizontal-unit-mesh.v1"
DEFAULT_HORIZONTAL_MESH_PATH = (
    Path(__file__).resolve().parent / "config" / "horizontal_mesh.json"
)
_VALID_MODES = {
    "build",
    "clarify",
    "explain",
    "explore",
    "respond",
    "summarize",
    "verify",
}


@dataclass(frozen=True)
class HorizontalMeshConfig:
    control_axis_priority: Tuple[str, ...]
    fallback_axis_priority: Tuple[str, ...]
    axis_to_mode: Mapping[str, str]
    decision_method: str
    normalization: str


@dataclass(frozen=True)
class HorizontalMeshDecision:
    votes: Mapping[str, float]
    unit_contributions: Mapping[str, Mapping[str, float]]
    winning_axis: str
    winning_mode: str
    candidates: Tuple[Mapping[str, Any], ...]
    config: HorizontalMeshConfig

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": HORIZONTAL_MESH_SCHEMA_VERSION,
            "decision_method": self.config.decision_method,
            "normalization": self.config.normalization,
            "control_axis_priority": list(
                self.config.control_axis_priority
            ),
            "fallback_axis_priority": list(
                self.config.fallback_axis_priority
            ),
            "votes": {
                axis: round(self.votes[axis], 6) for axis in ACTION_AXES
            },
            "unit_contributions": {
                unit_id: {
                    axis: round(value, 6)
                    for axis, value in sorted(values.items())
                }
                for unit_id, values in sorted(
                    self.unit_contributions.items()
                )
            },
            "winning_axis": self.winning_axis,
            "winning_mode": self.winning_mode,
            "candidates": [dict(candidate) for candidate in self.candidates],
        }


def load_horizontal_mesh_config(
    path: Optional[Path] = None,
) -> HorizontalMeshConfig:
    config_path = path or DEFAULT_HORIZONTAL_MESH_PATH
    payload: Any = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Horizontal Mesh config must be an object")
    if payload.get("schema_version") != HORIZONTAL_MESH_SCHEMA_VERSION:
        raise ValueError(
            "unsupported Horizontal Mesh schema: "
            f"{payload.get('schema_version')!r}"
        )

    control = payload.get("control_axis_priority")
    fallback = payload.get("fallback_axis_priority")
    if not isinstance(control, list) or not control:
        raise ValueError("control_axis_priority must be a non-empty list")
    if not isinstance(fallback, list) or not fallback:
        raise ValueError("fallback_axis_priority must be a non-empty list")
    if any(not isinstance(axis, str) for axis in control + fallback):
        raise ValueError("Mesh priority axes must be strings")
    ordered_axes = tuple(control + fallback)
    if len(ordered_axes) != len(set(ordered_axes)):
        raise ValueError("Mesh priority axes must be unique")
    if set(ordered_axes) != set(ACTION_AXES):
        raise ValueError("Mesh priority axes must cover Action Vector axes")

    axis_to_mode = payload.get("axis_to_mode")
    if not isinstance(axis_to_mode, dict):
        raise ValueError("axis_to_mode must be an object")
    if set(axis_to_mode) != set(ACTION_AXES):
        raise ValueError("axis_to_mode must cover Action Vector axes")
    if any(
        not isinstance(mode, str) or mode not in _VALID_MODES
        for mode in axis_to_mode.values()
    ):
        raise ValueError("Mesh modes must be valid LLM Order modes")

    decision_method = payload.get("decision_method")
    if decision_method != "integrated_score_times_action_weight":
        raise ValueError("unsupported Horizontal Mesh decision method")
    normalization = payload.get("normalization")
    if normalization != "divide_all_votes_when_peak_exceeds_one":
        raise ValueError("unsupported Horizontal Mesh normalization")
    return HorizontalMeshConfig(
        control_axis_priority=tuple(control),
        fallback_axis_priority=tuple(fallback),
        axis_to_mode=dict(axis_to_mode),
        decision_method=decision_method,
        normalization=normalization,
    )


DEFAULT_HORIZONTAL_MESH_CONFIG = load_horizontal_mesh_config()


def decide_axis_votes(
    votes: Mapping[str, float],
    config: HorizontalMeshConfig = DEFAULT_HORIZONTAL_MESH_CONFIG,
) -> Tuple[str, str, Tuple[Mapping[str, Any], ...]]:
    if set(votes) != set(ACTION_AXES):
        raise ValueError("Mesh votes must contain every Action Vector axis")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0.0
        for value in votes.values()
    ):
        raise ValueError("Mesh votes must be non-negative")

    control_winner = max(
        config.control_axis_priority,
        key=lambda axis: votes[axis],
    )
    if votes[control_winner] > 0.0:
        winning_axis = control_winner
        winning_group = "control"
        winning_reason = "highest_control_vote"
    else:
        winning_axis = max(
            config.fallback_axis_priority,
            key=lambda axis: votes[axis],
        )
        winning_group = "fallback"
        winning_reason = "highest_fallback_vote"

    candidates = []
    groups = (
        ("control", config.control_axis_priority),
        ("fallback", config.fallback_axis_priority),
    )
    for group_name, axes in groups:
        for priority_rank, axis in enumerate(axes):
            vote = votes[axis]
            if axis == winning_axis:
                reason = winning_reason
                selected = True
            elif winning_group == "control" and group_name == "fallback":
                reason = "suppressed_by_positive_control_vote"
                selected = False
            elif vote == 0.0:
                reason = "zero_vote"
                selected = False
            elif vote == votes[winning_axis]:
                reason = "tie_broken_by_priority"
                selected = False
            else:
                reason = "lower_vote"
                selected = False
            candidates.append(
                {
                    "axis": axis,
                    "mode": config.axis_to_mode[axis],
                    "vote": round(vote, 6),
                    "priority_group": group_name,
                    "priority_rank": priority_rank,
                    "selected": selected,
                    "reason": reason,
                }
            )
    return (
        winning_axis,
        config.axis_to_mode[winning_axis],
        tuple(candidates),
    )


def build_horizontal_mesh(
    integrated_units: Iterable[UnitActivation],
    units: Iterable[PatternUnit] = DEFAULT_UNITS,
    config: HorizontalMeshConfig = DEFAULT_HORIZONTAL_MESH_CONFIG,
) -> HorizontalMeshDecision:
    votes, contributions = build_action_vote_details(
        integrated_units,
        units,
    )
    winning_axis, winning_mode, candidates = decide_axis_votes(
        votes,
        config,
    )
    return HorizontalMeshDecision(
        votes=votes,
        unit_contributions=contributions,
        winning_axis=winning_axis,
        winning_mode=winning_mode,
        candidates=candidates,
        config=config,
    )
