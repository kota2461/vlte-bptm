import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional

from .encoder import EncodedInput
from .state import UnitActivation
from .units import DEFAULT_UNITS, PatternUnit


UNIT_SELECTION_POLICY_SCHEMA_VERSION = "unit-selection-policy.v1"
DEFAULT_UNIT_SELECTION_POLICY_PATH = (
    Path(__file__).resolve().parent / "config" / "unit_selection_policy.json"
)


@dataclass(frozen=True)
class UnitSelectionPolicy:
    routing_weight: float
    channel_affinity_weight: float
    keyword_weight: float
    respond_bias: float
    keyword_hit_saturation: int
    minimum_absolute_threshold: float
    relative_threshold_ratio: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": UNIT_SELECTION_POLICY_SCHEMA_VERSION,
            "weights": {
                "routing_overlap": self.routing_weight,
                "channel_affinity": self.channel_affinity_weight,
                "keyword": self.keyword_weight,
            },
            "respond_bias": self.respond_bias,
            "keyword_hit_saturation": self.keyword_hit_saturation,
            "minimum_absolute_threshold": self.minimum_absolute_threshold,
            "relative_threshold_ratio": self.relative_threshold_ratio,
        }


def _bounded_number(value: Any, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not 0.0 <= value <= 1.0
    ):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return float(value)


def load_unit_selection_policy(
    path: Optional[Path] = None,
) -> UnitSelectionPolicy:
    config_path = path or DEFAULT_UNIT_SELECTION_POLICY_PATH
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("unit selection policy must be an object")
    if payload.get("schema_version") != (
        UNIT_SELECTION_POLICY_SCHEMA_VERSION
    ):
        raise ValueError("unsupported unit selection policy schema")
    weights = payload.get("weights")
    if not isinstance(weights, Mapping) or set(weights) != {
        "routing_overlap",
        "channel_affinity",
        "keyword",
    }:
        raise ValueError("unit selection weights do not match the contract")
    routing_weight = _bounded_number(
        weights["routing_overlap"],
        "weights.routing_overlap",
    )
    channel_weight = _bounded_number(
        weights["channel_affinity"],
        "weights.channel_affinity",
    )
    keyword_weight = _bounded_number(
        weights["keyword"],
        "weights.keyword",
    )
    if not math.isclose(
        routing_weight + channel_weight + keyword_weight,
        1.0,
        abs_tol=1e-9,
    ):
        raise ValueError("unit selection weights must sum to 1.0")
    saturation = payload.get("keyword_hit_saturation")
    if (
        isinstance(saturation, bool)
        or not isinstance(saturation, int)
        or not 1 <= saturation <= 16
    ):
        raise ValueError("keyword_hit_saturation must be in [1, 16]")
    return UnitSelectionPolicy(
        routing_weight=routing_weight,
        channel_affinity_weight=channel_weight,
        keyword_weight=keyword_weight,
        respond_bias=_bounded_number(
            payload.get("respond_bias"),
            "respond_bias",
        ),
        keyword_hit_saturation=saturation,
        minimum_absolute_threshold=_bounded_number(
            payload.get("minimum_absolute_threshold"),
            "minimum_absolute_threshold",
        ),
        relative_threshold_ratio=_bounded_number(
            payload.get("relative_threshold_ratio"),
            "relative_threshold_ratio",
        ),
    )


DEFAULT_UNIT_SELECTION_POLICY = load_unit_selection_policy()


def _routing_score(encoded: EncodedInput, unit: PatternUnit) -> float:
    overlap = (encoded.thought_code.value & unit.route_mask).bit_count()
    union = (encoded.thought_code.value | unit.route_mask).bit_count()
    return overlap / union if union else 0.0


def _feature_score(encoded: EncodedInput, unit: PatternUnit) -> float:
    energy = encoded.feature_buffer.channel_energy()
    total = sum(energy)
    if total == 0.0:
        return 0.0
    return sum(energy[channel] for channel in unit.preferred_channels) / total


def _keyword_score(
    text: str,
    unit: PatternUnit,
    saturation: int,
) -> float:
    if not unit.keywords:
        return 0.0
    folded = text.casefold()
    hits = sum(keyword in folded for keyword in unit.keywords)
    return min(1.0, hits / saturation)


def select_units(
    encoded: EncodedInput,
    units: Iterable[PatternUnit] = DEFAULT_UNITS,
    max_units: int = 3,
    policy: UnitSelectionPolicy = DEFAULT_UNIT_SELECTION_POLICY,
) -> List[UnitActivation]:
    if max_units < 1:
        raise ValueError("max_units must be at least 1")

    catalog = list(units)
    if not encoded.user_input.strip():
        unit = next(
            (unit for unit in catalog if unit.unit_id == "clarify"),
            None,
        )
        if unit is not None:
            return [
                UnitActivation(
                    unit_id=unit.unit_id,
                    label=unit.label,
                    raw_score=1.0,
                    integrated_score=1.0,
                    pattern_shape=unit.shape,
                    unit_type=unit.unit_type,
                    channel_schema=unit.channel_schema,
                    channel_schema_version=unit.channel_schema_version,
                    channel_semantics=unit.channel_semantics,
                    prototype_channels=unit.preferred_channels,
                    catalog_schema_version=unit.catalog_schema_version,
                    process_mode=unit.process_mode,
                    score_components={
                        "routing_overlap": 0.0,
                        "channel_affinity": 0.0,
                        "keyword": 0.0,
                        "bias": 1.0,
                    },
                )
            ]

    ranked: List[UnitActivation] = []
    for unit in catalog:
        routing = _routing_score(encoded, unit)
        channel = _feature_score(encoded, unit)
        keyword = _keyword_score(
            encoded.user_input,
            unit,
            policy.keyword_hit_saturation,
        )
        bias = policy.respond_bias if unit.unit_id == "respond" else 0.0
        score = (
            policy.routing_weight * routing
            + policy.channel_affinity_weight * channel
            + policy.keyword_weight * keyword
            + bias
        )
        ranked.append(
            UnitActivation(
                unit_id=unit.unit_id,
                label=unit.label,
                raw_score=score,
                integrated_score=score,
                pattern_shape=unit.shape,
                unit_type=unit.unit_type,
                channel_schema=unit.channel_schema,
                channel_schema_version=unit.channel_schema_version,
                channel_semantics=unit.channel_semantics,
                prototype_channels=unit.preferred_channels,
                catalog_schema_version=unit.catalog_schema_version,
                process_mode=unit.process_mode,
                score_components={
                    "routing_overlap": routing,
                    "channel_affinity": channel,
                    "keyword": keyword,
                    "bias": bias,
                },
            )
        )

    ranked.sort(key=lambda item: (-item.raw_score, item.unit_id))
    if not ranked:
        return []

    relative_threshold = max(
        policy.minimum_absolute_threshold,
        ranked[0].raw_score * policy.relative_threshold_ratio,
    )
    selected = [
        item for item in ranked if item.raw_score >= relative_threshold
    ][:max_units]
    return selected or ranked[:1]
