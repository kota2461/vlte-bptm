import copy
import hashlib
import json
from pathlib import Path

import pytest

from semantic_routing.core_bridge import run_core_shadow
from semantic_routing.processing_plan import (
    PROCESSING_PLAN_SCHEMA_VERSION,
    build_processing_plan,
    parse_processing_plan,
)
from semantic_routing.baseline import extract_semantic_packet
from semantic_routing.semantic_packet import (
    SEMANTIC_PACKET_SCHEMA_VERSION,
    parse_semantic_packet,
    request_digest,
)


FIXTURES = Path(__file__).parent / "fixtures"
SEMANTIC_PACKET_FIXTURE = FIXTURES / "semantic_packet_v1.json"
PROCESSING_PLAN_FIXTURE = FIXTURES / "processing_plan_v1.json"
SEMANTIC_FIXTURE_PROMPT = (
    "この情報が最新か、出典付きで確認してください。"
)


def _packet_payload(
    primary: str,
    *,
    confidence: float = 0.90,
    missing: bool = False,
    unverified: bool = False,
    current: bool = False,
    multiple: bool = False,
    risk: str = "low",
    operations: list[str] | None = None,
    response_length: str = "short",
    unknowns: list[str] | None = None,
    conflicts: list[str] | None = None,
) -> dict:
    return {
        "schema_version": SEMANTIC_PACKET_SCHEMA_VERSION,
        "request_digest": "0" * 64,
        "adapter": {
            "kind": "deterministic_signal_extractor",
            "version": "test",
        },
        "language": "ja",
        "intent_candidates": [
            {"intent": primary, "confidence": confidence}
        ],
        "operations": operations if operations is not None else [primary],
        "information_state": {
            "missing_required_information": missing,
            "contains_unverified_claims": unverified,
            "requires_current_information": current,
            "multiple_intents": multiple,
        },
        "constraints": {
            "response_length": response_length,
            "formats": [],
            "must": [],
            "must_not": [],
        },
        "risk": {"level": risk, "flags": []},
        "evidence": [],
        "unknowns": unknowns or [],
        "conflicts": conflicts or [],
        "confidence": confidence,
    }


def test_semantic_packet_fixture_round_trips_without_raw_prompt() -> None:
    payload = json.loads(
        SEMANTIC_PACKET_FIXTURE.read_text(encoding="utf-8")
    )
    packet = parse_semantic_packet(payload)

    assert packet.as_dict() == payload
    assert packet.primary_intent == "verify"
    assert packet.request_digest == request_digest(SEMANTIC_FIXTURE_PROMPT)
    evidence = packet.evidence[0]
    assert (
        SEMANTIC_FIXTURE_PROMPT[evidence.start:evidence.end]
        == "確認してください"
    )
    serialized = json.dumps(packet.as_dict(), ensure_ascii=False)
    assert "user_input" not in serialized
    assert "raw_prompt" not in serialized
    assert "answer" not in serialized


def test_request_digest_is_utf8_sha256() -> None:
    assert request_digest("abc") == hashlib.sha256(b"abc").hexdigest()
    with pytest.raises(TypeError, match="string"):
        request_digest(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update({"raw_prompt": "do not store"}),
            "unknown field",
        ),
        (
            lambda payload: payload.update({"request_digest": "not-a-hash"}),
            "SHA-256",
        ),
        (
            lambda payload: payload["adapter"].update({"extra": True}),
            "unknown field",
        ),
        (
            lambda payload: payload["intent_candidates"].reverse(),
            "descending confidence",
        ),
        (
            lambda payload: payload["constraints"].update(
                {
                    "must": ["cite_sources"],
                    "must_not": ["cite_sources"],
                }
            ),
            "both must and must_not",
        ),
        (
            lambda payload: payload["evidence"][0].update({"start": True}),
            "start < end",
        ),
    ],
)
def test_semantic_packet_rejects_contract_violations(
    mutate,
    message: str,
) -> None:
    payload = json.loads(
        SEMANTIC_PACKET_FIXTURE.read_text(encoding="utf-8")
    )
    mutate(payload)
    with pytest.raises(ValueError, match=message):
        parse_semantic_packet(payload)


def test_processing_plan_fixture_round_trips() -> None:
    payload = json.loads(
        PROCESSING_PLAN_FIXTURE.read_text(encoding="utf-8")
    )
    plan = parse_processing_plan(payload)

    assert plan.as_dict() == payload
    assert plan.processing_class == "verified"
    assert plan.core_mode == "vertical"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update({"raw_prompt": "forbidden"}),
            "unknown field",
        ),
        (
            lambda payload: payload["budgets"].update(
                {"max_dispatches": 0}
            ),
            "max_dispatches",
        ),
        (
            lambda payload: payload.update(
                {
                    "processing_class": "economy",
                    "core_mode": "horizontal",
                    "model_class": "small",
                }
            ),
            "economy contract",
        ),
        (
            lambda payload: payload.update({"core_mode": "recursive"}),
            "unknown core mode",
        ),
    ],
)
def test_processing_plan_rejects_contract_violations(
    mutate,
    message: str,
) -> None:
    payload = json.loads(
        PROCESSING_PLAN_FIXTURE.read_text(encoding="utf-8")
    )
    mutate(payload)
    with pytest.raises(ValueError, match=message):
        parse_processing_plan(payload)


def test_fixture_packet_builds_the_frozen_processing_plan() -> None:
    packet = parse_semantic_packet(
        json.loads(SEMANTIC_PACKET_FIXTURE.read_text(encoding="utf-8"))
    )
    expected = json.loads(
        PROCESSING_PLAN_FIXTURE.read_text(encoding="utf-8")
    )

    assert build_processing_plan(packet).as_dict() == expected


@pytest.mark.parametrize(
    ("payload", "processing_class", "core_mode", "model_class"),
    [
        (
            _packet_payload("respond"),
            "economy",
            "horizontal",
            "small",
        ),
        (
            _packet_payload("build"),
            "standard",
            "horizontal",
            "standard",
        ),
        (
            _packet_payload("clarify", missing=True),
            "clarify",
            "horizontal",
            "small",
        ),
        (
            _packet_payload("respond", confidence=0.40),
            "clarify",
            "horizontal",
            "small",
        ),
        (
            _packet_payload("verify", current=True),
            "verified",
            "vertical",
            "standard",
        ),
        (
            _packet_payload("build", unverified=True),
            "verified",
            "vertical",
            "standard",
        ),
        (
            _packet_payload("explore"),
            "deep",
            "hybrid",
            "large",
        ),
        (
            _packet_payload("respond", multiple=True),
            "deep",
            "hybrid",
            "large",
        ),
        (
            _packet_payload("respond", risk="critical"),
            "verified",
            "vertical",
            "large",
        ),
    ],
)
def test_processing_policy_selects_expected_resource_class(
    payload: dict,
    processing_class: str,
    core_mode: str,
    model_class: str,
) -> None:
    plan = build_processing_plan(parse_semantic_packet(payload))

    assert plan.processing_class == processing_class
    assert plan.core_mode == core_mode
    assert plan.model_class == model_class


def test_current_information_requires_web_search() -> None:
    packet = parse_semantic_packet(
        _packet_payload("respond", current=True)
    )
    plan = build_processing_plan(packet)

    assert plan.processing_class == "verified"
    assert "web_search" in plan.tools
    assert "current_information_required" in plan.reason_codes


def test_processing_router_rejects_raw_prompts() -> None:
    with pytest.raises(TypeError, match="raw prompts are not accepted"):
        build_processing_plan("please verify this")  # type: ignore[arg-type]


def test_parsers_do_not_mutate_input_payloads() -> None:
    packet_payload = json.loads(
        SEMANTIC_PACKET_FIXTURE.read_text(encoding="utf-8")
    )
    plan_payload = json.loads(
        PROCESSING_PLAN_FIXTURE.read_text(encoding="utf-8")
    )
    packet_before = copy.deepcopy(packet_payload)
    plan_before = copy.deepcopy(plan_payload)

    parse_semantic_packet(packet_payload)
    parse_processing_plan(plan_payload)

    assert packet_payload == packet_before
    assert plan_payload == plan_before


def test_processing_plan_drives_verified_build_vertical_stack() -> None:
    text = "提示された前提を確認してから実装計画を作ってください。"
    payload = _packet_payload(
        "build",
        unverified=True,
        operations=["build", "verify"],
    )
    payload["request_digest"] = request_digest(text)
    packet = parse_semantic_packet(payload)
    plan = build_processing_plan(packet)

    result = run_core_shadow(text, packet, plan).as_dict()
    pipeline = result["pipeline_state"]

    assert plan.core_mode == "vertical"
    assert pipeline["diagnostics"]["processing_mode"] == "vertical"
    assert pipeline["vertical_stack"]["root_mode"] == "build"
    assert pipeline["vertical_stack"]["execution_order"] == [
        "verify",
        "build",
    ]
    assert (
        pipeline["llm_order"]["metadata"]["vertical_stack_root_origin"]
        == "processing_plan"
    )


@pytest.mark.parametrize(
    ("text", "expected_intent"),
    [
        ("こんにちは！今日は少し相談したいです。", "respond"),
        ("ありがとうございます。とても助かりました。", "respond"),
        ("プロジェクトがうまく進まず、少し不安になっています。", "respond"),
        ("この挙動、どうしてこうなるんでしょうか。", "explain"),
        (
            "Could you walk me through what makes this retry policy safe?",
            "explain",
        ),
    ],
)
def test_conversational_and_indirect_requests_use_economy_path(
    text: str,
    expected_intent: str,
) -> None:
    packet = extract_semantic_packet(text)
    plan = build_processing_plan(packet)

    assert packet.primary_intent == expected_intent
    assert packet.confidence >= 0.60
    assert packet.unknowns == ()
    assert plan.processing_class == "economy"
    assert plan.core_mode == "horizontal"


def test_conversational_today_does_not_require_current_information() -> None:
    packet = extract_semantic_packet("こんにちは！今日は少し相談したいです。")

    assert packet.information_state.requires_current_information is False
    assert "search" not in packet.operations


@pytest.mark.parametrize(
    "text",
    [
        "前提の妥当性を検証し、その上で実装計画を作ってください。",
        "このAPI仕様を確認し、その上でimplementation planを作ってください。",
    ],
)
def test_sequenced_verification_build_uses_vertical_stack(text: str) -> None:
    packet = extract_semantic_packet(text)
    plan = build_processing_plan(packet)
    pipeline = run_core_shadow(text, packet, plan).pipeline_state

    assert packet.primary_intent == "build"
    assert packet.operations == ("build", "verify")
    assert packet.information_state.multiple_intents is True
    assert plan.processing_class == "verified"
    assert plan.core_mode == "vertical"
    assert pipeline["vertical_stack"]["execution_order"] == [
        "verify",
        "build",
    ]


def test_core_shadow_rejects_prompt_digest_mismatch() -> None:
    payload = _packet_payload("respond")
    payload["request_digest"] = request_digest("original")
    packet = parse_semantic_packet(payload)
    plan = build_processing_plan(packet)

    with pytest.raises(ValueError, match="digest"):
        run_core_shadow("different", packet, plan)
