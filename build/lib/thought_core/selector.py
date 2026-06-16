from typing import Iterable, List

from .encoder import EncodedInput
from .state import UnitActivation
from .units import DEFAULT_UNITS, PatternUnit


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


def _keyword_score(text: str, unit: PatternUnit) -> float:
    if not unit.keywords:
        return 0.0
    folded = text.casefold()
    hits = sum(keyword in folded for keyword in unit.keywords)
    return min(1.0, hits / 2.0)


def select_units(
    encoded: EncodedInput,
    units: Iterable[PatternUnit] = DEFAULT_UNITS,
    max_units: int = 3,
) -> List[UnitActivation]:
    if max_units < 1:
        raise ValueError("max_units must be at least 1")

    if not encoded.user_input.strip():
        unit = next(
            unit for unit in units if unit.unit_id == "clarify"
        )
        return [
            UnitActivation(
                unit_id=unit.unit_id,
                label=unit.label,
                raw_score=1.0,
                integrated_score=1.0,
                pattern_shape=unit.shape,
                unit_type=unit.unit_type,
                channel_schema=unit.channel_schema,
                process_mode=unit.process_mode,
            )
        ]

    ranked: List[UnitActivation] = []
    for unit in units:
        score = (
            0.40 * _routing_score(encoded, unit)
            + 0.20 * _feature_score(encoded, unit)
            + 0.40 * _keyword_score(encoded.user_input, unit)
        )
        if unit.unit_id == "respond":
            score += 0.12
        ranked.append(
            UnitActivation(
                unit_id=unit.unit_id,
                label=unit.label,
                raw_score=score,
                integrated_score=score,
                pattern_shape=unit.shape,
                unit_type=unit.unit_type,
                channel_schema=unit.channel_schema,
                process_mode=unit.process_mode,
            )
        )

    ranked.sort(key=lambda item: (-item.raw_score, item.unit_id))
    if not ranked:
        return []

    relative_threshold = max(0.12, ranked[0].raw_score * 0.68)
    selected = [
        item for item in ranked if item.raw_score >= relative_threshold
    ][:max_units]
    return selected or ranked[:1]
