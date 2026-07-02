"""SIG-64 signature + route-cam.v1: layout, lookup, escalation-only merge,
and the do-not-regress guarantee that an empty store is a no-op."""

import pytest

from semantic_routing import route
from semantic_routing.route_cam import (
    DEFAULT_ROUTE_CAM_PATH,
    MAX_ENTRIES,
    RouteCamStore,
    apply_route_cam,
    load_route_cam,
    parse_route_cam,
)
from semantic_routing.baseline import extract_semantic_packet
from semantic_routing.processing_plan import build_processing_plan
from semantic_routing.semantic_packet import parse_semantic_packet
from semantic_routing.signature import (
    INTENT_BITS_MASK,
    LANGUAGE_MASK,
    RISK_MASK,
    SEMANTIC_MASK,
    SIGNATURE_MASK,
    build_signature,
    hamming_distance,
    signature_hex,
)


def _packet(
    *,
    intent: str = "respond",
    risk: str = "low",
    response_length: str = "unspecified",
    language: str = "ja",
    information_state: dict | None = None,
    operations: list | None = None,
):
    return parse_semantic_packet(
        {
            "schema_version": "semantic-packet.v1",
            "request_digest": "0" * 64,
            "adapter": {
                "kind": "deterministic_signal_extractor",
                "version": "0.2",
            },
            "language": language,
            "intent_candidates": [{"intent": intent, "confidence": 0.9}],
            "operations": operations if operations is not None else [intent],
            "information_state": information_state
            or {
                "missing_required_information": False,
                "contains_unverified_claims": False,
                "requires_current_information": False,
                "multiple_intents": False,
            },
            "constraints": {
                "response_length": response_length,
                "formats": [],
                "must": [],
                "must_not": [],
            },
            "risk": {"level": risk, "flags": []},
            "evidence": [],
            "unknowns": [],
            "conflicts": [],
            "confidence": 0.9,
        }
    )


def _entry(**overrides):
    payload = {
        "entry_id": "entry_a",
        "value": "0x0000000000000000",
        "care": "0x0000000000000780",
        "max_distance": 0,
        "plan_class": "verified",
        "evidence_fixture": "tests#unit",
    }
    payload.update(overrides)
    return payload


def _store(*entries):
    return parse_route_cam(
        {"schema_version": "route-cam.v1", "entries": list(entries)}
    )


# --- signature -------------------------------------------------------------


def test_signature_is_deterministic_and_64_bit() -> None:
    packet = _packet(intent="build")
    first = build_signature(packet, "手順を作ってください")
    second = build_signature(packet, "手順を作ってください")
    assert first == second
    assert 0 <= first <= SIGNATURE_MASK
    assert signature_hex(first).startswith("0x")


def test_signature_semantic_bits_follow_the_layout() -> None:
    packet = _packet(intent="build", language="ja")
    signature = build_signature(packet, "手順を作ってください")
    # INTENTS order: respond, explain, clarify, build, ... -> build = bit 3
    assert signature & INTENT_BITS_MASK == 1 << 3
    # ja = 0b01 at bits 17-18
    assert (signature & LANGUAGE_MASK) >> 17 == 0b01
    # low risk -> thermometer 000
    assert signature & RISK_MASK == 0


def test_information_state_bits() -> None:
    packet = _packet(
        information_state={
            "missing_required_information": True,
            "contains_unverified_claims": False,
            "requires_current_information": True,
            "multiple_intents": False,
        }
    )
    signature = build_signature(packet, "テスト入力")
    assert signature & (1 << 7)          # missing
    assert not signature & (1 << 8)      # unverified
    assert signature & (1 << 9)          # current
    assert not signature & (1 << 10)     # multiple


def test_risk_thermometer_distance_is_monotone() -> None:
    text = "テスト入力"
    signatures = {
        level: build_signature(_packet(risk=level), text)
        for level in ("low", "medium", "high", "critical")
    }
    ladder = ("low", "medium", "high", "critical")
    for left, right in zip(ladder, ladder[1:]):
        assert hamming_distance(
            signatures[left], signatures[right], RISK_MASK
        ) == 1
    assert hamming_distance(
        signatures["low"], signatures["critical"], RISK_MASK
    ) == 3


def test_signature_matches_live_extraction() -> None:
    text = "手順を作ってください"
    packet = extract_semantic_packet(text)
    signature = build_signature(packet, text)
    assert signature & INTENT_BITS_MASK == 1 << 3  # markers say build
    # upper 32 bits are the SimHash sketch and must be non-degenerate
    assert (signature & ~SEMANTIC_MASK) != 0


# --- store validation ------------------------------------------------------


def test_intent_bits_require_explicit_override() -> None:
    with pytest.raises(ValueError, match="intent bits"):
        _store(_entry(care="0x000000000000007F"))
    store = _store(
        _entry(care="0x000000000000007F", intent_care_override=True)
    )
    assert len(store) == 1


def test_economy_entries_are_rejected() -> None:
    with pytest.raises(ValueError, match="economy"):
        _store(_entry(plan_class="economy"))


def test_store_rejects_bad_shapes() -> None:
    with pytest.raises(ValueError, match="schema"):
        parse_route_cam({"schema_version": "route-cam.v9", "entries": []})
    with pytest.raises(ValueError, match="unknown field"):
        parse_route_cam(
            {"schema_version": "route-cam.v1", "entries": [], "extra": 1}
        )
    with pytest.raises(ValueError, match="hex"):
        _store(_entry(value="12345"))
    with pytest.raises(ValueError, match="care"):
        _store(_entry(care="0x0000000000000000"))
    with pytest.raises(ValueError, match="unique"):
        _store(_entry(), _entry())
    with pytest.raises(ValueError, match="evidence_fixture"):
        _store(_entry(evidence_fixture="  "))
    with pytest.raises(ValueError, match="cap"):
        parse_route_cam(
            {
                "schema_version": "route-cam.v1",
                "entries": [
                    _entry(entry_id=f"entry_{index}")
                    for index in range(MAX_ENTRIES + 1)
                ],
            }
        )


def test_shipped_default_store_is_empty() -> None:
    store = load_route_cam(DEFAULT_ROUTE_CAM_PATH)
    assert len(store) == 0


# --- lookup ----------------------------------------------------------------


def test_lookup_prefers_min_distance_then_higher_rank() -> None:
    # care over information_state bits 7-10; signature has bit 7 set
    signature = 1 << 7
    near = _entry(
        entry_id="near_standard",
        value=f"0x{1 << 7:016X}",
        care="0x0000000000000780",
        max_distance=1,
        plan_class="standard",
    )
    far = _entry(
        entry_id="far_verified",
        value="0x0000000000000000",
        care="0x0000000000000780",
        max_distance=1,
        plan_class="verified",
    )
    hit = _store(near, far).lookup(signature)
    assert hit is not None
    assert hit.entry.entry_id == "near_standard"  # distance 0 beats rank
    assert hit.distance == 0

    # equal distance -> higher rank wins
    tie_low = _entry(
        entry_id="tie_standard",
        value=f"0x{1 << 7:016X}",
        care="0x0000000000000780",
        max_distance=0,
        plan_class="standard",
    )
    tie_high = _entry(
        entry_id="tie_verified",
        value=f"0x{1 << 7:016X}",
        care="0x0000000000000780",
        max_distance=0,
        plan_class="verified",
    )
    hit = _store(tie_low, tie_high).lookup(signature)
    assert hit is not None
    assert hit.entry.entry_id == "tie_verified"


def test_lookup_miss_returns_none() -> None:
    store = _store(_entry(max_distance=0, value=f"0x{1 << 7:016X}"))
    assert store.lookup(0) is None


# --- escalation-only merge --------------------------------------------------


def test_apply_route_cam_escalates_but_never_deescalates() -> None:
    packet = _packet()  # respond / low risk -> economy baseline
    plan = build_processing_plan(packet)
    assert plan.processing_class == "economy"
    signature = build_signature(packet, "テスト入力")

    escalating = _store(
        _entry(
            value=f"0x{signature & 0x60000:016X}",
            care=f"0x{0x60000:016X}",  # language bits
            plan_class="verified",
        )
    )
    merged, hit, applied = apply_route_cam(packet, plan, escalating, signature)
    assert applied and hit is not None
    assert merged.processing_class == "verified"
    assert merged.core_mode == "vertical"
    assert merged.reason_codes[-1] == "route_cam_entry_a"

    # now the baseline is already stronger than the entry: max-join keeps it
    verified_packet = _packet(
        information_state={
            "missing_required_information": False,
            "contains_unverified_claims": True,
            "requires_current_information": False,
            "multiple_intents": False,
        }
    )
    verified_plan = build_processing_plan(verified_packet)
    assert verified_plan.processing_class == "verified"
    weaker = _store(
        _entry(
            value=f"0x{build_signature(verified_packet, 'テスト入力') & 0x60000:016X}",
            care=f"0x{0x60000:016X}",
            plan_class="standard",
        )
    )
    merged, hit, applied = apply_route_cam(
        verified_packet,
        verified_plan,
        weaker,
        build_signature(verified_packet, "テスト入力"),
    )
    assert hit is not None and not applied
    assert merged is verified_plan


# --- adapter integration ----------------------------------------------------


def test_route_with_empty_store_is_byte_identical() -> None:
    text = "やっと終わってほっとした"
    baseline = route(text)
    with_empty = route(text, route_cam=RouteCamStore(entries=()))
    assert baseline.plan.as_dict() == with_empty.plan.as_dict()
    assert baseline.packet.as_dict() == with_empty.packet.as_dict()
    assert "route_cam" not in baseline.trace
    assert "route_cam" not in with_empty.trace


def test_route_applies_cam_hit_and_traces_it() -> None:
    text = "やっと終わってほっとした"  # markers silent -> economy floor
    assert route(text).plan.processing_class == "economy"
    store = _store(
        _entry(
            entry_id="ja_escalate",
            value=f"0x{0b01 << 17:016X}",
            care=f"0x{0x60000:016X}",
            max_distance=0,
            plan_class="verified",
        )
    )
    result = route(text, route_cam=store)
    assert result.plan.processing_class == "verified"
    assert result.plan.reason_codes[-1] == "route_cam_ja_escalate"
    cam_trace = result.trace["route_cam"]
    assert cam_trace["hit"] == "ja_escalate"
    assert cam_trace["distance"] == 0
    assert cam_trace["applied"] is True
    assert cam_trace["signature"].startswith("0x")
