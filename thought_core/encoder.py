from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Tuple

from .bits import THOUGHT_CODE_WIDTH, ThoughtCode, routing_intensities
from .units import (
    PATTERN_CHANNELS,
    PATTERN_HEIGHT,
    PATTERN_WIDTH,
    PatternTensor,
)


@dataclass(frozen=True)
class ThresholdProfile:
    name: str
    intensity_threshold: float
    min_active_bits: int
    max_active_bits: int


THRESHOLD_PROFILES: Mapping[str, ThresholdProfile] = {
    "light_v1": ThresholdProfile("light_v1", 0.86, 4, 10),
    "normal_v1": ThresholdProfile("normal_v1", 0.75, 8, 18),
    "design_v1": ThresholdProfile("design_v1", 0.64, 14, 28),
    "deep_verify_v1": ThresholdProfile("deep_verify_v1", 0.52, 20, 36),
}

DESIGN_MARKERS = (
    "architecture",
    "build",
    "code",
    "design",
    "implement",
    "spec",
    "実装",
    "仕様",
    "設計",
)

VERIFY_MARKERS = (
    "audit",
    "review",
    "risk",
    "test",
    "verify",
    "レビュー",
    "リスク",
    "テスト",
    "検証",
    "確認",
)


@dataclass(frozen=True)
class EncodedInput:
    user_input: str
    thought_code: ThoughtCode
    feature_buffer: PatternTensor
    bit_intensities: Tuple[float, ...]
    threshold_profile: ThresholdProfile


def _contains(text: str, markers: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(marker in folded for marker in markers)


def select_threshold_profile(text: str) -> ThresholdProfile:
    has_design = _contains(text, DESIGN_MARKERS)
    has_verify = _contains(text, VERIFY_MARKERS)
    if has_verify and (has_design or len(text) >= 80):
        return THRESHOLD_PROFILES["deep_verify_v1"]
    if has_design or len(text) >= 80:
        return THRESHOLD_PROFILES["design_v1"]
    if len(text.strip()) <= 12:
        return THRESHOLD_PROFILES["light_v1"]
    return THRESHOLD_PROFILES["normal_v1"]


def _resolve_profile(
    text: str,
    profile_name: Optional[str],
) -> ThresholdProfile:
    if profile_name is None:
        return select_threshold_profile(text)
    try:
        return THRESHOLD_PROFILES[profile_name]
    except KeyError as error:
        choices = ", ".join(sorted(THRESHOLD_PROFILES))
        raise ValueError(
            f"unknown threshold profile {profile_name!r}; choose from {choices}"
        ) from error


def _active_bits(
    intensities: Tuple[float, ...],
    profile: ThresholdProfile,
) -> Tuple[int, ...]:
    ranked = sorted(
        range(THOUGHT_CODE_WIDTH),
        key=lambda index: (-intensities[index], index),
    )
    active = [
        index
        for index in ranked
        if intensities[index] >= profile.intensity_threshold
    ]
    if len(active) < profile.min_active_bits:
        active = ranked[: profile.min_active_bits]
    elif len(active) > profile.max_active_bits:
        active = ranked[: profile.max_active_bits]
    return tuple(sorted(active))


def _encode_feature_buffer(text: str) -> PatternTensor:
    """Project bytes into a non-semantic [64,16,16] activation buffer."""

    values: Dict[tuple[int, int, int], float] = {}
    payload = text.encode("utf-8") or b"\x00"
    for index, byte in enumerate(payload):
        channel = (byte + index * 17) % PATTERN_CHANNELS
        row = (index * 7 + byte) % PATTERN_HEIGHT
        column = (index + byte * 3) % PATTERN_WIDTH
        coordinate = (channel, row, column)
        values[coordinate] = min(
            1.0,
            values.get(coordinate, 0.0) + 0.25 + byte / 1020.0,
        )
    return PatternTensor(values)


def encode(
    user_input: str,
    threshold_profile: Optional[str] = None,
) -> EncodedInput:
    profile = _resolve_profile(user_input, threshold_profile)
    intensities = routing_intensities(user_input)
    active_bits = _active_bits(intensities, profile)
    return EncodedInput(
        user_input=user_input,
        thought_code=ThoughtCode.from_active_bits(active_bits),
        feature_buffer=_encode_feature_buffer(user_input),
        bit_intensities=intensities,
        threshold_profile=profile,
    )
