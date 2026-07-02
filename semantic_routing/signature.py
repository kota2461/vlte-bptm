"""SIG-64 semantic signature (route-cam.v1 companion).

Builds a deterministic 64-bit signature from a validated SemanticPacket plus
the raw text. The layout is two-natured by design:

- bits 0-31  SEMANTIC: a direct bit encoding of semantic-packet.v1 enum
  fields. Every bit is human-readable and auditable; ordered fields (risk,
  response_length) use thermometer codes so Hamming distance is monotone in
  the enum ordering ("risk one level apart" == distance 1).
- bits 32-63 NON-SEMANTIC, LOCALITY-SENSITIVE: a 32-bit SimHash over the
  same hashed n-gram features used by the intent model
  (pattern_learning.trainer.text_features). Hamming distance approximates
  surface similarity; individual bits carry no meaning.

The signature contains no raw text and cannot be inverted to the prompt
(packet enums + a 32-bit sketch), so it stays inside the existing privacy
boundary of semantic-packet.v1.

Bit layout (LSB = bit 0):

    bits  0-6   intent one-hot (INTENTS order)
    bits  7-10  information_state (missing / unverified / current / multiple)
    bits 11-13  risk thermometer   (low=000, medium=001, high=011, critical=111)
    bits 14-16  response_length thermometer (unspecified=000 ... long=111)
    bits 17-18  language (und=00, ja=01, en=10, mixed=11)
    bits 19-21  operations flags (search / calculate / compare)
    bits 22-26  temporal_kind one-hot — RESERVED for the v0.4 Temporal
                Normalizer (always 0 until that module exists)
    bits 27-31  reserved (always 0)
    bits 32-63  SimHash over text_features(text, 2048)
"""

from hashlib import blake2b
from typing import Dict

from pattern_learning.trainer import text_features

from .semantic_packet import (
    INTENTS,
    RESPONSE_LENGTHS,
    RISK_LEVELS,
    SemanticPacket,
)


SIGNATURE_WIDTH = 64
SIGNATURE_MASK = (1 << SIGNATURE_WIDTH) - 1

# Field masks (documented layout above; keep in sync with build_signature).
INTENT_BITS_MASK = 0x0000_0000_0000_007F          # bits 0-6
INFORMATION_STATE_MASK = 0x0000_0000_0000_0780    # bits 7-10
RISK_MASK = 0x0000_0000_0000_3800                 # bits 11-13
RESPONSE_LENGTH_MASK = 0x0000_0000_0001_C000      # bits 14-16
LANGUAGE_MASK = 0x0000_0000_0006_0000             # bits 17-18
OPERATIONS_MASK = 0x0000_0000_0038_0000           # bits 19-21
TEMPORAL_RESERVED_MASK = 0x0000_0000_07C0_0000    # bits 22-26
RESERVED_MASK = 0x0000_0000_F800_0000             # bits 27-31
SEMANTIC_MASK = 0x0000_0000_FFFF_FFFF             # bits 0-31
SIMHASH_MASK = 0xFFFF_FFFF_0000_0000              # bits 32-63

SIMHASH_WIDTH = 32
SIMHASH_FEATURE_DIMENSION = 2048
_SIMHASH_PERSON = b"SIG64-simhash-v1"

_OPERATION_FLAGS = ("search", "calculate", "compare")
_LANGUAGE_CODES = {"und": 0b00, "ja": 0b01, "en": 0b10, "mixed": 0b11}


def _thermometer(index: int, width: int) -> int:
    """index 0 -> 000, 1 -> 001, 2 -> 011, 3 -> 111 (LSB-first fill)."""

    if not 0 <= index <= width:
        raise ValueError("thermometer index out of range")
    return (1 << index) - 1


def _simhash_signs(feature_index: int) -> int:
    """Deterministic 32-bit sign mask for one feature index."""

    digest = blake2b(
        feature_index.to_bytes(4, "big"),
        digest_size=4,
        person=_SIMHASH_PERSON,
    ).digest()
    return int.from_bytes(digest, "big")


def simhash32(features: Dict[int, float]) -> int:
    """32-bit SimHash of a sparse feature vector (deterministic)."""

    accumulator = [0.0] * SIMHASH_WIDTH
    for index, value in features.items():
        signs = _simhash_signs(index)
        for position in range(SIMHASH_WIDTH):
            if signs & (1 << position):
                accumulator[position] += value
            else:
                accumulator[position] -= value
    result = 0
    for position in range(SIMHASH_WIDTH):
        if accumulator[position] > 0.0:
            result |= 1 << position
    return result


def build_signature(packet: SemanticPacket, text: str) -> int:
    """Build the deterministic SIG-64 signature for a packet + raw text."""

    if not isinstance(packet, SemanticPacket):
        raise TypeError("build_signature requires a validated SemanticPacket")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("build_signature requires non-empty text")

    signature = 0

    # bits 0-6: intent one-hot
    signature |= 1 << INTENTS.index(packet.primary_intent)

    # bits 7-10: information_state
    state = packet.information_state
    if state.missing_required_information:
        signature |= 1 << 7
    if state.contains_unverified_claims:
        signature |= 1 << 8
    if state.requires_current_information:
        signature |= 1 << 9
    if state.multiple_intents:
        signature |= 1 << 10

    # bits 11-13: risk thermometer
    signature |= _thermometer(RISK_LEVELS.index(packet.risk.level), 3) << 11

    # bits 14-16: response_length thermometer
    signature |= (
        _thermometer(
            RESPONSE_LENGTHS.index(packet.constraints.response_length), 3
        )
        << 14
    )

    # bits 17-18: language (und=00 so the all-zero signature reads "unknown")
    signature |= _LANGUAGE_CODES[packet.language] << 17

    # bits 19-21: operations flags
    for offset, operation in enumerate(_OPERATION_FLAGS):
        if operation in packet.operations:
            signature |= 1 << (19 + offset)

    # bits 22-31: reserved (temporal_kind + spare) stay 0.

    # bits 32-63: SimHash over the shared hashed n-gram features
    features = text_features(text, SIMHASH_FEATURE_DIMENSION)
    signature |= simhash32(features) << 32

    return signature & SIGNATURE_MASK


def hamming_distance(left: int, right: int, care_mask: int = SIGNATURE_MASK) -> int:
    """popcount((left XOR right) AND care_mask)."""

    return ((left ^ right) & care_mask & SIGNATURE_MASK).bit_count()


def signature_hex(signature: int) -> str:
    return f"0x{signature & SIGNATURE_MASK:016X}"
