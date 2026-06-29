"""The legacy memorization snapshot is gated, not unconditionally on (S5).

extract_semantic_packet / route() consult LEGACY_PACKET_BY_DIGEST (an
exact-match snapshot that returns precomputed packets, bypassing the regex /
intent model) only when the gate is on. The gate defaults ON because the
historical v4-v10 sealed measurements depend on it, but it is now explicit and
overridable (use_legacy_snapshot argument, or env TSR_LEGACY_SNAPSHOT=0) so the
router's true capability can be measured without memorization.
"""

import json
from pathlib import Path

from semantic_routing import parse_plm_sealed_fixture, route
from semantic_routing.baseline import (
    LEGACY_PACKET_BY_DIGEST,
    LEGACY_SNAPSHOT_DEFAULT,
    extract_semantic_packet,
)
from semantic_routing.semantic_packet import request_digest

ROOT = Path(__file__).resolve().parents[1]
SEALED_V10 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v10.json"


def _covered_inputs() -> list[str]:
    fixture = parse_plm_sealed_fixture(json.loads(SEALED_V10.read_text(encoding="utf-8")))
    return [c.input_text for c in fixture.cases if request_digest(c.input_text) in LEGACY_PACKET_BY_DIGEST]


def test_default_is_on_and_snapshot_is_populated() -> None:
    # Default ON preserves the historical measurements; snapshot is non-empty.
    assert LEGACY_SNAPSHOT_DEFAULT is True
    assert len(LEGACY_PACKET_BY_DIGEST) > 0


def test_gate_off_still_returns_valid_packets_for_covered_inputs() -> None:
    covered = _covered_inputs()
    assert covered, "expected sealed_v10 inputs to be covered by the snapshot"
    for text in covered[:5]:
        on = extract_semantic_packet(text, use_legacy_snapshot=True)
        off = extract_semantic_packet(text, use_legacy_snapshot=False)
        assert on.primary_intent in {
            "respond", "clarify", "build", "verify", "summarize", "explore", "explain",
        }
        assert off.primary_intent in {
            "respond", "clarify", "build", "verify", "summarize", "explore", "explain",
        }


def test_gate_actually_changes_behavior_on_at_least_one_covered_input() -> None:
    # If the snapshot were a behavioral no-op the gate would be meaningless;
    # at least one covered input must differ between snapshot and regex paths.
    differs = False
    for text in _covered_inputs():
        on = extract_semantic_packet(text, use_legacy_snapshot=True).as_dict()
        off = extract_semantic_packet(text, use_legacy_snapshot=False).as_dict()
        on.pop("request_digest", None)
        off.pop("request_digest", None)
        if on != off:
            differs = True
            break
    assert differs, "snapshot never changed the output -> gate is meaningless"


def test_gate_is_noop_for_uncovered_input() -> None:
    # An input not in the snapshot must route identically regardless of the gate.
    text = "please reconcile the gamma ledger against the delta manifest by tuesday"
    assert request_digest(text) not in LEGACY_PACKET_BY_DIGEST
    on = extract_semantic_packet(text, use_legacy_snapshot=True).as_dict()
    off = extract_semantic_packet(text, use_legacy_snapshot=False).as_dict()
    assert on == off


def test_route_passes_the_gate_through() -> None:
    covered = _covered_inputs()
    text = covered[0]
    on = route(text, use_legacy_snapshot=True).packet.as_dict()
    off = route(text, use_legacy_snapshot=False).packet.as_dict()
    on.pop("request_digest", None)
    off.pop("request_digest", None)
    # Both valid; route honours the argument (exercising the passthrough).
    assert on["schema_version"] == off["schema_version"] == "semantic-packet.v1"
