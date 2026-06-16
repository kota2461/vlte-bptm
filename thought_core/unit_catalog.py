import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


UNIT_CATALOG_SCHEMA_VERSION = "pattern-unit-catalog.v1"
DEFAULT_UNIT_CATALOG_PATH = (
    Path(__file__).resolve().parent / "config" / "pattern_units.json"
)


@dataclass(frozen=True)
class PatternUnitDefinition:
    unit_id: str
    unit_type: str
    label: str
    keywords: Tuple[str, ...]
    action_weights: Mapping[str, float]
    channel_schema: str
    process_mode: str
    rationale: str


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def load_unit_catalog(
    path: Optional[Path] = None,
) -> Tuple[PatternUnitDefinition, ...]:
    config_path = path or DEFAULT_UNIT_CATALOG_PATH
    payload: Any = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Pattern Unit catalog must be an object")
    if payload.get("schema_version") != UNIT_CATALOG_SCHEMA_VERSION:
        raise ValueError(
            "unsupported Pattern Unit catalog schema: "
            f"{payload.get('schema_version')!r}"
        )
    if payload.get("process_mode") != "horizontal":
        raise ValueError("v1 Pattern Unit catalog requires horizontal mode")
    raw_units = payload.get("units")
    if not isinstance(raw_units, list) or not raw_units:
        raise ValueError("Pattern Unit catalog requires a non-empty units list")

    definitions = []
    unit_ids = set()
    for raw_unit in raw_units:
        if not isinstance(raw_unit, dict):
            raise ValueError("Pattern Unit definition must be an object")
        unit_id = _non_empty_string(raw_unit.get("unit_id"), "unit_id")
        if unit_id in unit_ids:
            raise ValueError(f"duplicate Pattern Unit id: {unit_id}")
        unit_ids.add(unit_id)
        unit_type = _non_empty_string(
            raw_unit.get("unit_type"),
            f"{unit_id}.unit_type",
        )
        if unit_type != unit_id:
            raise ValueError("v1 Pattern Unit type must equal its unit id")

        raw_keywords = raw_unit.get("keywords")
        if not isinstance(raw_keywords, list):
            raise ValueError(f"{unit_id}.keywords must be a list")
        keywords = tuple(
            _non_empty_string(keyword, f"{unit_id}.keyword")
            for keyword in raw_keywords
        )
        if len(keywords) != len(set(keyword.casefold() for keyword in keywords)):
            raise ValueError(f"{unit_id}.keywords must be unique")

        raw_weights = raw_unit.get("action_weights")
        if not isinstance(raw_weights, dict) or not raw_weights:
            raise ValueError(f"{unit_id}.action_weights must be an object")
        action_weights: Dict[str, float] = {}
        for axis, weight in raw_weights.items():
            axis_name = _non_empty_string(axis, f"{unit_id}.action_axis")
            if (
                isinstance(weight, bool)
                or not isinstance(weight, (int, float))
                or not math.isfinite(weight)
                or not 0.0 <= weight <= 1.0
            ):
                raise ValueError("Pattern Unit action weights must be in [0, 1]")
            action_weights[axis_name] = float(weight)

        definitions.append(
            PatternUnitDefinition(
                unit_id=unit_id,
                unit_type=unit_type,
                label=_non_empty_string(
                    raw_unit.get("label"),
                    f"{unit_id}.label",
                ),
                keywords=keywords,
                action_weights=action_weights,
                channel_schema=_non_empty_string(
                    raw_unit.get("channel_schema"),
                    f"{unit_id}.channel_schema",
                ),
                process_mode="horizontal",
                rationale=_non_empty_string(
                    raw_unit.get("rationale"),
                    f"{unit_id}.rationale",
                ),
            )
        )
    return tuple(definitions)
