"""Thought Delta Journal (TDJ) — inter-turn XOR-delta journal.

Extends the single-turn Thought State Register across turns without touching
the register layout. Two parallel records are kept per turn:

- the ENCODED state (straight out of the encoder, before journal feedback
  and conflict resolution) — used for revisit / continuity detection, so
  states are always compared like-for-like (the resolver's additions such
  as FINAL_ANSWER would otherwise make an exact revisit unreachable);
- the COMMITTED state (after conflict resolution) — used for the XOR delta
  chain and loop detection, because the action layer of the committed state
  is what the register actually decided.

Detection is pure bit arithmetic:

- revisit:     an earlier encoded state within Hamming distance 0
- neighbours:  4 exact-match tables over the register's own 16-bit layers
               (drive/affect/cognition/action). By the pigeonhole principle
               any earlier state within distance 3 shares at least one
               16-bit block, so lookup is O(1) with guaranteed recall for
               distance <= 3 (approximate beyond that).
- continuity:  drive+affect layers (bits 0-31) unchanged vs the previous
               encoded state
- loop:        the last two committed transitions are non-zero and confined
               to the action layer (bits 48-63) — the register is flapping
               between actions while the drive/affect/cognition context
               stands still.

Detected conditions feed back as ordinary register bits (with sources), so
they flow through the existing resolver / mode selector and stay auditable:

    revisit    -> RETRIEVE_MEMORY
    loop       -> REPAIR_DRIVE + CONTRADICTION_DETECTED
    continuity -> CONTINUITY_DRIVE

The journal stores 64-bit words only — never the input text or any answer
text — so it stays inside the raw-text-free privacy boundary.

Scope note (v0.1 encoder): the encoder reaches only a small part of the
state space (a handful of keyword rules), so revisit detection is expected
to fire on same-shaped inputs rather than provide general semantic recall.
The journal's value grows with the encoder; see the design doc.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .bits import MASK_64, ThoughtBit


DRIVE_AFFECT_MASK = 0x0000_0000_FFFF_FFFF   # bits 0-31
ACTION_MASK = 0xFFFF_0000_0000_0000          # bits 48-63

SUBKEY_COUNT = 4
SUBKEY_WIDTH = 16
SUBKEY_MASK = (1 << SUBKEY_WIDTH) - 1

# Pigeonhole: distance <= (SUBKEY_COUNT - 1) guarantees one equal block.
GUARANTEED_RADIUS = SUBKEY_COUNT - 1

# Feedback injections: (bit, intensity, source). Intensities follow the
# encoder's hand-tuned convention; like every other intensity they are
# metadata — the boolean bit is what the resolver / selector consume.
_REVISIT_FEEDBACK = ((ThoughtBit.RETRIEVE_MEMORY, 0.8, "journal.revisit"),)
_LOOP_FEEDBACK = (
    (ThoughtBit.REPAIR_DRIVE, 0.8, "journal.loop"),
    (ThoughtBit.CONTRADICTION_DETECTED, 0.8, "journal.loop"),
)
_CONTINUITY_FEEDBACK = (
    (ThoughtBit.CONTINUITY_DRIVE, 0.7, "journal.continuity"),
)


def _check_word(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int")
    if value < 0 or value > MASK_64:
        raise ValueError(f"{name} must fit in an unsigned 64-bit integer")
    return value


def _subkeys(value: int) -> Tuple[int, ...]:
    return tuple(
        (value >> (SUBKEY_WIDTH * block)) & SUBKEY_MASK
        for block in range(SUBKEY_COUNT)
    )


@dataclass
class ThoughtJournal:
    """Session-scoped, deterministic, append-only journal of 64-bit states."""

    _encoded: List[int] = field(default_factory=list)
    _committed: List[int] = field(default_factory=list)
    _deltas: List[int] = field(default_factory=list)
    _index: List[Dict[int, List[int]]] = field(
        default_factory=lambda: [{} for _ in range(SUBKEY_COUNT)]
    )

    @property
    def turn_count(self) -> int:
        return len(self._encoded)

    def append(self, encoded_value: int, committed_value: int) -> int:
        """Record one turn. Returns the turn id (0-based)."""

        encoded = _check_word(encoded_value, "encoded_value")
        committed = _check_word(committed_value, "committed_value")
        turn = len(self._encoded)
        previous = self._committed[-1] if self._committed else 0
        self._encoded.append(encoded)
        self._committed.append(committed)
        self._deltas.append(committed ^ previous)
        for block, subkey in enumerate(_subkeys(encoded)):
            self._index[block].setdefault(subkey, []).append(turn)
        return turn

    def find_neighbors(
        self,
        encoded_value: int,
        max_distance: int = GUARANTEED_RADIUS,
    ) -> List[Tuple[int, int]]:
        """Earlier turns whose encoded state is within `max_distance`.

        Returns [(turn, distance)] sorted by (distance, turn). Recall is
        guaranteed for max_distance <= 3 (pigeonhole over the 4 blocks);
        beyond that only candidates sharing a block are examined.
        """

        value = _check_word(encoded_value, "encoded_value")
        candidates = set()
        for block, subkey in enumerate(_subkeys(value)):
            candidates.update(self._index[block].get(subkey, ()))
        neighbors = []
        for turn in candidates:
            distance = (self._encoded[turn] ^ value).bit_count()
            if distance <= max_distance:
                neighbors.append((turn, distance))
        neighbors.sort(key=lambda item: (item[1], item[0]))
        return neighbors

    def detect_revisit(self, encoded_value: int) -> Optional[int]:
        """Most recent earlier turn with the identical encoded state."""

        matches = [
            turn
            for turn, distance in self.find_neighbors(encoded_value, 0)
            if distance == 0
        ]
        return max(matches) if matches else None

    def detect_continuity(self, encoded_value: int) -> bool:
        """Drive+affect layers unchanged vs the previous encoded state."""

        value = _check_word(encoded_value, "encoded_value")
        if not self._encoded:
            return False
        return ((value ^ self._encoded[-1]) & DRIVE_AFFECT_MASK) == 0

    def detect_loop(self) -> bool:
        """Last two committed transitions flap inside the action layer."""

        transitions = self._deltas[1:]  # delta[0] is the initial state
        if len(transitions) < 2:
            return False
        return all(
            delta != 0 and (delta & ~ACTION_MASK) == 0
            for delta in transitions[-2:]
        )

    def feedback(
        self,
        encoded_value: int,
    ) -> List[Tuple[ThoughtBit, float, str]]:
        """Bits to inject for the current turn, given its encoded state."""

        injections: List[Tuple[ThoughtBit, float, str]] = []
        if self.detect_revisit(encoded_value) is not None:
            injections.extend(_REVISIT_FEEDBACK)
        if self.detect_loop():
            injections.extend(_LOOP_FEEDBACK)
        if self.detect_continuity(encoded_value):
            injections.extend(_CONTINUITY_FEEDBACK)
        return injections

    def as_dict(self) -> dict:
        return {
            "turn_count": self.turn_count,
            "encoded": [f"0x{value:016X}" for value in self._encoded],
            "committed": [f"0x{value:016X}" for value in self._committed],
            "deltas": [f"0x{value:016X}" for value in self._deltas],
        }
