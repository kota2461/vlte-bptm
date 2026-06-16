from dataclasses import dataclass
from hashlib import blake2b
from typing import Iterable, Tuple


THOUGHT_CODE_WIDTH = 64
THOUGHT_CODE_MASK = (1 << THOUGHT_CODE_WIDTH) - 1
_HASH_PERSON = b"VLTE-BPTM-v1a"


def routing_intensities(text: str) -> Tuple[float, ...]:
    """Return deterministic routing intensities, one for each external bit."""

    digest = blake2b(
        text.encode("utf-8"),
        digest_size=THOUGHT_CODE_WIDTH,
        person=_HASH_PERSON,
    ).digest()
    return tuple(byte / 255.0 for byte in digest)


@dataclass(frozen=True)
class ThoughtCode:
    """Unsigned 64-bit external routing key.

    A ThoughtCode identifies and routes an input. It is not a semantic tensor
    and must not be interpreted as the thought itself.
    """

    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value <= THOUGHT_CODE_MASK:
            raise ValueError("ThoughtCode.value must fit in unsigned 64 bits")

    @classmethod
    def from_active_bits(cls, active_bits: Iterable[int]) -> "ThoughtCode":
        value = 0
        for index in active_bits:
            if not 0 <= index < THOUGHT_CODE_WIDTH:
                raise ValueError("active bit index must be in [0, 63]")
            value |= 1 << index
        return cls(value)

    @classmethod
    def from_text(cls, text: str, threshold: float = 0.75) -> "ThoughtCode":
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
        intensities = routing_intensities(text)
        active_bits = (
            index
            for index, intensity in enumerate(intensities)
            if intensity >= threshold
        )
        return cls.from_active_bits(active_bits)

    @property
    def active_bits(self) -> Tuple[int, ...]:
        return tuple(
            index
            for index in range(THOUGHT_CODE_WIDTH)
            if self.value & (1 << index)
        )

    @property
    def active_bit_count(self) -> int:
        return self.value.bit_count()

    @property
    def active_bit_density(self) -> float:
        return self.active_bit_count / THOUGHT_CODE_WIDTH

    def hex(self) -> str:
        return f"0x{self.value:016X}"

    def as_dict(self) -> dict:
        return {
            "value": self.hex(),
            "width": THOUGHT_CODE_WIDTH,
            "role": "external_routing_key",
        }
