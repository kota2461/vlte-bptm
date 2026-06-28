"""Reference implementation for Thought Color Code v0.1.

Packing is provided for compact transport. Learning and routing code should use
the factorized fields exposed by ``factorized_features`` and
``generalization_keys``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Iterable, Mapping, Tuple


BASE_BITS = 11
STANCE_BITS = 3
OPERATION_BITS = 3
INTENSITY_BITS = 2
TOTAL_BITS = BASE_BITS + STANCE_BITS + OPERATION_BITS + INTENSITY_BITS

BASE_COUNT = 2024
RAW_BASE_CAPACITY = 1 << BASE_BITS

STANCE_LABELS = (
    "neutral",
    "affirm",
    "negate",
    "explore",
    "clarify",
    "empathize",
    "challenge",
    "reserve",
)
OPERATION_LABELS = (
    "respond",
    "reason",
    "compare",
    "verify",
    "generate",
    "remember",
    "route",
    "reserve",
)
INTENSITY_LABELS = ("low", "medium", "high", "hold")

_BASE_MASK = (1 << BASE_BITS) - 1
_STANCE_MASK = (1 << STANCE_BITS) - 1
_OPERATION_MASK = (1 << OPERATION_BITS) - 1
_INTENSITY_MASK = (1 << INTENSITY_BITS) - 1

_STANCE_SHIFT = BASE_BITS
_OPERATION_SHIFT = BASE_BITS + STANCE_BITS
_INTENSITY_SHIFT = BASE_BITS + STANCE_BITS + OPERATION_BITS


def raw_capacity() -> int:
    return 1 << TOTAL_BITS


def valid_capacity() -> int:
    return (
        BASE_COUNT
        * len(STANCE_LABELS)
        * len(OPERATION_LABELS)
        * len(INTENSITY_LABELS)
    )


def _validate_int(name: str, value: int, upper_exclusive: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if not 0 <= value < upper_exclusive:
        raise ValueError(f"{name} must be in [0, {upper_exclusive - 1}]")


def _index_from_label(
    name: str,
    value: int | str,
    labels: Tuple[str, ...],
) -> int:
    if isinstance(value, str):
        if value not in labels:
            raise ValueError(f"unknown {name} label: {value}")
        return labels.index(value)
    _validate_int(name, value, len(labels))
    return value


@dataclass(frozen=True)
class ThoughtColorCode:
    """Layered color code with a Base2024 hue and three modifier channels."""

    base_id: int
    stance: int = 0
    operation: int = 0
    intensity: int = 0

    SCHEMA_VERSION: ClassVar[str] = "thought-color-code.v0.1"

    def __post_init__(self) -> None:
        _validate_int("base_id", self.base_id, BASE_COUNT)
        _validate_int("stance", self.stance, len(STANCE_LABELS))
        _validate_int("operation", self.operation, len(OPERATION_LABELS))
        _validate_int("intensity", self.intensity, len(INTENSITY_LABELS))

    @classmethod
    def from_labels(
        cls,
        *,
        base_id: int,
        stance: int | str = 0,
        operation: int | str = 0,
        intensity: int | str = 0,
    ) -> "ThoughtColorCode":
        return cls(
            base_id=base_id,
            stance=_index_from_label("stance", stance, STANCE_LABELS),
            operation=_index_from_label(
                "operation",
                operation,
                OPERATION_LABELS,
            ),
            intensity=_index_from_label(
                "intensity",
                intensity,
                INTENSITY_LABELS,
            ),
        )

    def pack(self) -> int:
        """Pack fields into 19 bits for storage or transport."""

        return (
            self.base_id
            | (self.stance << _STANCE_SHIFT)
            | (self.operation << _OPERATION_SHIFT)
            | (self.intensity << _INTENSITY_SHIFT)
        )

    @classmethod
    def unpack(cls, packed: int) -> "ThoughtColorCode":
        """Unpack a storage token and reject reserved Base2024 values."""

        _validate_int("packed", packed, raw_capacity())
        return cls(
            base_id=packed & _BASE_MASK,
            stance=(packed >> _STANCE_SHIFT) & _STANCE_MASK,
            operation=(packed >> _OPERATION_SHIFT) & _OPERATION_MASK,
            intensity=(packed >> _INTENSITY_SHIFT) & _INTENSITY_MASK,
        )

    def channel_tuple(self) -> Tuple[int, int, int, int]:
        return (self.base_id, self.stance, self.operation, self.intensity)

    def label_tuple(self) -> Tuple[int, str, str, str]:
        return (
            self.base_id,
            STANCE_LABELS[self.stance],
            OPERATION_LABELS[self.operation],
            INTENSITY_LABELS[self.intensity],
        )

    def factorized_features(self) -> Dict[str, int]:
        """Return fields as separate model features."""

        return {
            "base_id": self.base_id,
            "stance": self.stance,
            "operation": self.operation,
            "intensity": self.intensity,
        }

    def sparse_features(self) -> Tuple[str, ...]:
        """Return stable feature names for sparse linear or rule models."""

        return (
            f"base:{self.base_id:04d}",
            f"stance:{STANCE_LABELS[self.stance]}",
            f"operation:{OPERATION_LABELS[self.operation]}",
            f"intensity:{INTENSITY_LABELS[self.intensity]}",
            f"base_stance:{self.base_id:04d}:{STANCE_LABELS[self.stance]}",
            (
                f"base_operation:{self.base_id:04d}:"
                f"{OPERATION_LABELS[self.operation]}"
            ),
        )

    def generalization_keys(self) -> Mapping[str, Tuple[int, ...]]:
        """Expose coarse-to-specific grouping keys.

        The ``full`` key is useful for diagnostics, but ``base`` and the
        two-way keys preserve the intended collision sharing.
        """

        return {
            "base": (self.base_id,),
            "modifier": (self.stance, self.operation, self.intensity),
            "base_stance": (self.base_id, self.stance),
            "base_operation": (self.base_id, self.operation),
            "base_intensity": (self.base_id, self.intensity),
            "full": self.channel_tuple(),
        }

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "packed": self.pack(),
            "fields": self.factorized_features(),
            "labels": {
                "stance": STANCE_LABELS[self.stance],
                "operation": OPERATION_LABELS[self.operation],
                "intensity": INTENSITY_LABELS[self.intensity],
            },
            "sparse_features": list(self.sparse_features()),
            "generalization_keys": {
                key: list(value)
                for key, value in self.generalization_keys().items()
            },
        }


def collision_profile(codes: Iterable[ThoughtColorCode]) -> Dict[str, int]:
    """Summarize whether collisions are retained or separated by channels."""

    items = tuple(codes)
    base_counts = Counter(code.base_id for code in items)
    full_counts = Counter(code.channel_tuple() for code in items)

    full_by_base: Dict[int, set[Tuple[int, int, int, int]]] = defaultdict(set)
    for code in items:
        full_by_base[code.base_id].add(code.channel_tuple())

    return {
        "sample_count": len(items),
        "unique_base_count": len(base_counts),
        "unique_full_count": len(full_counts),
        "base_collision_bucket_count": sum(
            1 for count in base_counts.values() if count > 1
        ),
        "base_colliding_sample_count": sum(
            count for count in base_counts.values() if count > 1
        ),
        "modifier_separated_base_count": sum(
            1 for values in full_by_base.values() if len(values) > 1
        ),
        "exact_duplicate_count": sum(
            count - 1 for count in full_counts.values() if count > 1
        ),
    }

