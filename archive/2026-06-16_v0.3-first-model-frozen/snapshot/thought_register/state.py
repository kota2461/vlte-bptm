from dataclasses import dataclass, field
from typing import Dict, List

from .bits import MASK_64, ThoughtBit, bit, layer_name


@dataclass
class ThoughtState:
    value: int = 0
    intensity: Dict[ThoughtBit, float] = field(default_factory=dict)
    sources: Dict[ThoughtBit, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.value < 0 or self.value > MASK_64:
            raise ValueError("ThoughtState.value must fit in an unsigned 64-bit integer")

    def set(
        self,
        flag: ThoughtBit,
        intensity: float = 1.0,
        source: str = "unknown",
    ) -> None:
        strength = max(0.0, min(1.0, float(intensity)))
        self.value = (self.value | bit(flag)) & MASK_64
        self.intensity[flag] = max(self.intensity.get(flag, 0.0), strength)
        flag_sources = self.sources.setdefault(flag, [])
        if source not in flag_sources:
            flag_sources.append(source)

    def clear(self, flag: ThoughtBit) -> None:
        self.value &= ~bit(flag) & MASK_64
        self.intensity.pop(flag, None)
        self.sources.pop(flag, None)

    def has(self, flag: ThoughtBit) -> bool:
        return bool(self.value & bit(flag))

    def strength(self, flag: ThoughtBit) -> float:
        return self.intensity.get(flag, 0.0)

    def active_flags(self) -> List[ThoughtBit]:
        return [flag for flag in ThoughtBit if self.has(flag)]

    def active_bits(self) -> List[str]:
        return [flag.name.lower() for flag in self.active_flags()]

    def active_by_layer(self) -> Dict[str, List[str]]:
        result = {"drive": [], "affect": [], "cognition": [], "action": []}
        for flag in self.active_flags():
            result[layer_name(flag)].append(flag.name.lower())
        return result

    def hex(self) -> str:
        return f"0x{self.value:016X}"

    def as_dict(self) -> dict:
        return {
            "state": self.hex(),
            "active_bits": self.active_bits(),
            "layers": self.active_by_layer(),
            "intensity": {
                flag.name.lower(): self.intensity[flag]
                for flag in self.active_flags()
            },
            "sources": {
                flag.name.lower(): self.sources.get(flag, [])
                for flag in self.active_flags()
            },
        }
