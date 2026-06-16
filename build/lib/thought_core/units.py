from dataclasses import dataclass
from hashlib import blake2b
from math import sqrt
from typing import Dict, Iterable, Mapping, Sequence, Tuple


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


def _unit(
    unit_id: str,
    label: str,
    keywords: Sequence[str],
    action_weights: Mapping[str, float],
    channel_schema: str,
) -> PatternUnit:
    return PatternUnit(
        unit_id=unit_id,
        unit_type=unit_id,
        label=label,
        route_mask=_route_mask(unit_id),
        pattern=_pattern(unit_id),
        keywords=tuple(keyword.casefold() for keyword in keywords),
        action_weights=dict(action_weights),
        channel_schema=channel_schema,
    )


DEFAULT_UNITS: Tuple[PatternUnit, ...] = (
    _unit(
        "explore",
        "Exploration",
        ("idea", "explore", "new", "発想", "構想", "新しい", "検討"),
        {"reply": 0.7, "explain": 0.8, "creative": 1.0},
        "novelty_and_hypothesis_features",
    ),
    _unit(
        "build",
        "Implementation",
        ("implement", "build", "code", "実装", "作成", "設計", "作って"),
        {"reply": 0.8, "plan": 1.0, "explain": 0.6},
        "implementation_and_planning_features",
    ),
    _unit(
        "verify",
        "Verification",
        (
            "verify",
            "review",
            "risk",
            "test",
            "レビュー",
            "検証",
            "確認",
            "リスク",
            "テスト",
        ),
        {"reply": 0.7, "verify": 1.0, "caution": 0.8},
        "evidence_risk_and_uncertainty_features",
    ),
    _unit(
        "summarize",
        "Compression",
        ("summary", "summarize", "要約", "まとめ", "短く"),
        {"reply": 0.8, "summarize": 1.0},
        "salience_and_compression_features",
    ),
    _unit(
        "clarify",
        "Clarification",
        ("unclear", "ambiguous", "missing", "不明", "曖昧", "不足", "質問"),
        {"reply": 0.5, "ask": 1.0, "caution": 0.5},
        "ambiguity_and_missing_information_features",
    ),
    _unit(
        "respond",
        "Direct Response",
        (),
        {"reply": 1.0, "explain": 0.4},
        "speech_style_and_response_features",
    ),
)


def units_by_id(
    units: Iterable[PatternUnit] = DEFAULT_UNITS,
) -> Dict[str, PatternUnit]:
    return {unit.unit_id: unit for unit in units}
