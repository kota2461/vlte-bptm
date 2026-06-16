from dataclasses import dataclass
from hashlib import blake2b
from math import sqrt
from typing import Dict, Iterable, Mapping, Tuple

from .channel_schema import (
    CHANNEL_SCHEMA_CONFIG_VERSION,
    ChannelSchemaDefinition,
    load_channel_schemas,
)
from .unit_catalog import (
    UNIT_CATALOG_SCHEMA_VERSION,
    PatternUnitDefinition,
    load_unit_catalog,
)


PATTERN_CHANNELS = 64
PATTERN_HEIGHT = 16
PATTERN_WIDTH = 16
PATTERN_SHAPE = (PATTERN_CHANNELS, PATTERN_HEIGHT, PATTERN_WIDTH)

Coordinate = Tuple[int, int, int]


@dataclass(frozen=True)
class PatternTensor:
    """Sparse [C,H,W] tensor whose H/W cells are activation storage only."""

    values: Mapping[Coordinate, float]
    shape: Tuple[int, int, int] = PATTERN_SHAPE

    def __post_init__(self) -> None:
        if self.shape != PATTERN_SHAPE:
            raise ValueError(f"v1 pattern shape must be {PATTERN_SHAPE}")
        for (channel, row, column), value in self.values.items():
            if not 0 <= channel < PATTERN_CHANNELS:
                raise ValueError("pattern channel is out of range")
            if not 0 <= row < PATTERN_HEIGHT:
                raise ValueError("pattern row is out of range")
            if not 0 <= column < PATTERN_WIDTH:
                raise ValueError("pattern column is out of range")
            if value < 0.0:
                raise ValueError("pattern activations must be non-negative")

    def channel_energy(self) -> Tuple[float, ...]:
        energy = [0.0] * PATTERN_CHANNELS
        for (channel, _row, _column), value in self.values.items():
            energy[channel] += value
        return tuple(energy)

    def norm(self) -> float:
        return sqrt(sum(value * value for value in self.values.values()))

    def summary(self) -> dict:
        return {
            "shape": list(self.shape),
            "storage": "sparse_activation_buffer",
            "nonzero_cell_count": len(self.values),
            "spatial_semantics": False,
        }


@dataclass(frozen=True)
class PatternUnit:
    unit_id: str
    unit_type: str
    label: str
    route_mask: int
    pattern: PatternTensor
    keywords: Tuple[str, ...]
    action_weights: Mapping[str, float]
    channel_schema: str
    channel_schema_version: str
    channel_semantics: str
    catalog_schema_version: str
    process_mode: str = "horizontal"

    @property
    def shape(self) -> Tuple[int, int, int]:
        return self.pattern.shape

    @property
    def preferred_channels(self) -> Tuple[int, ...]:
        return tuple(
            index
            for index, value in enumerate(self.pattern.channel_energy())
            if value > 0.0
        )


def _digest(seed: str, size: int = 8) -> bytes:
    return blake2b(
        seed.encode("utf-8"),
        digest_size=size,
        person=b"VLTE-unit-v1a",
    ).digest()


def _route_mask(unit_id: str) -> int:
    return int.from_bytes(_digest(f"route:{unit_id}"), "big")


def _pattern(unit_id: str) -> PatternTensor:
    values: Dict[Coordinate, float] = {}
    seed = _digest(f"pattern:{unit_id}", size=32)
    for index, byte in enumerate(seed):
        channel = (byte + index * 11) % PATTERN_CHANNELS
        row = (byte * 3 + index) % PATTERN_HEIGHT
        column = (byte + index * 7) % PATTERN_WIDTH
        values[(channel, row, column)] = 0.5 + (byte / 510.0)
    return PatternTensor(values)


def _unit(definition: PatternUnitDefinition) -> PatternUnit:
    unit_id = definition.unit_id
    channel_schema = definition.channel_schema
    pattern = _pattern(unit_id)
    schema = DEFAULT_CHANNEL_SCHEMAS.get(unit_id)
    if schema is None:
        raise ValueError(f"missing channel schema for unit: {unit_id}")
    if schema.schema_id != channel_schema:
        raise ValueError(
            f"channel schema mismatch for {unit_id}: "
            f"{channel_schema!r} != {schema.schema_id!r}"
        )
    if schema.channel_count != PATTERN_CHANNELS:
        raise ValueError("channel schema width does not match Pattern Unit")
    preferred_channels = tuple(
        index
        for index, value in enumerate(pattern.channel_energy())
        if value > 0.0
    )
    if preferred_channels != schema.prototype_channels:
        raise ValueError(
            f"prototype channels do not match generated pattern for {unit_id}"
        )
    return PatternUnit(
        unit_id=unit_id,
        unit_type=definition.unit_type,
        label=definition.label,
        route_mask=_route_mask(unit_id),
        pattern=pattern,
        keywords=tuple(
            keyword.casefold() for keyword in definition.keywords
        ),
        action_weights=dict(definition.action_weights),
        channel_schema=channel_schema,
        channel_schema_version=CHANNEL_SCHEMA_CONFIG_VERSION,
        channel_semantics=schema.channel_semantics,
        catalog_schema_version=UNIT_CATALOG_SCHEMA_VERSION,
        process_mode=definition.process_mode,
    )


DEFAULT_CHANNEL_SCHEMAS: Dict[str, ChannelSchemaDefinition] = (
    load_channel_schemas()
)
DEFAULT_UNIT_DEFINITIONS: Tuple[PatternUnitDefinition, ...] = (
    load_unit_catalog()
)


DEFAULT_UNITS: Tuple[PatternUnit, ...] = (
    *(_unit(definition) for definition in DEFAULT_UNIT_DEFINITIONS),
)

if set(DEFAULT_CHANNEL_SCHEMAS) != {unit.unit_id for unit in DEFAULT_UNITS}:
    raise ValueError("channel schema Unit types do not match DEFAULT_UNITS")

_VALID_ACTION_AXES = {
    "reply",
    "ask",
    "explain",
    "plan",
    "verify",
    "summarize",
    "creative",
    "caution",
}
for unit in DEFAULT_UNITS:
    unknown_axes = set(unit.action_weights) - _VALID_ACTION_AXES
    if unknown_axes:
        raise ValueError(
            f"unknown action axes for {unit.unit_id}: "
            f"{', '.join(sorted(unknown_axes))}"
        )


def units_by_id(
    units: Iterable[PatternUnit] = DEFAULT_UNITS,
) -> Dict[str, PatternUnit]:
    return {unit.unit_id: unit for unit in units}
