import json
from pathlib import Path

import pytest

from semantic_routing import (
    KNOWLEDGE_INDEX_SCHEMA_VERSION,
    RETRIEVAL_PACKET_SCHEMA_VERSION,
    build_retrieval_packet,
    load_knowledge_index,
    parse_knowledge_index,
    parse_retrieval_packet,
    route,
)


ROOT = Path(__file__).parents[1]
INDEX_PATH = ROOT / "data" / "knowledge_index_v1.json"


def test_knowledge_index_fixture_round_trips() -> None:
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    index = parse_knowledge_index(payload)

    assert payload["schema_version"] == KNOWLEDGE_INDEX_SCHEMA_VERSION
    assert index.as_dict() == payload
    assert {entry.domain for entry in index.entries} >= {
        "basic_it",
        "legal_guard",
        "medical_guard",
        "router_design",
    }


def test_basic_it_hook_builds_retrieval_packet_without_current_check() -> None:
    packet = build_retrieval_packet("HTTPの正式名称は何ですか？")

    assert packet.as_dict()["schema_version"] == RETRIEVAL_PACKET_SCHEMA_VERSION
    assert packet.needed is True
    assert packet.domains == ("basic_it",)
    assert packet.hooks == ("HTTP",)
    assert packet.libraries == ("basic_it_v1",)
    assert packet.current_check is False
    assert packet.risk == "low"
    assert parse_retrieval_packet(packet.as_dict()).as_dict() == packet.as_dict()


def test_guard_domains_keep_risk_and_current_flags_separate() -> None:
    legal = build_retrieval_packet(
        "現在進行中のAI規制・ガイドラインについて説明してください。"
    )
    medical = build_retrieval_packet(
        "片頭痛や強い不安が続く時に何を提案できますか。"
    )

    assert "legal_guard" in legal.domains
    assert legal.current_check is True
    assert legal.risk == "high"
    assert "medical_guard" in medical.domains
    assert medical.current_check is False
    assert medical.risk == "high"


def test_route_exposes_retrieval_packet_without_changing_semantic_packet() -> None:
    result = route("M.2スロットにAIアクセラレーターを差す案を検証してください。")

    assert result.retrieval.needed is True
    assert "hardware_feasibility" in result.retrieval.domains
    assert "hardware_feasibility_v1" in result.retrieval.libraries
    assert result.trace["retrieval"] == result.retrieval.as_dict()
    assert "retrieval" not in result.packet.as_dict()


def test_no_hook_returns_empty_retrieval_packet() -> None:
    packet = build_retrieval_packet("こんにちは。今日は雑談したいです。")

    assert packet.needed is False
    assert packet.domains == ()
    assert packet.hooks == ()
    assert packet.libraries == ()
    assert packet.current_check is False
    assert packet.risk == "low"
    assert packet.matches == ()


def test_negation_context_softens_relationship_boundary_risk() -> None:
    # Grounded in v11 diagnostic case plm-sealed-v10-explain-01: the text
    # explicitly argues *against* the dependency-risk framing ("...と決め
    # つけない理由を説明してください"), so the "依存" hook should not carry
    # full risk weight the way a direct dependency statement does.
    softened = build_retrieval_packet(
        "AIと雑談して癒やされる話を、依存リスクと決めつけない理由を説明してください。"
    )
    direct = build_retrieval_packet("AIだけが心の支えで、依存しています。")

    assert "ai_relationship_boundary" in softened.domains
    assert softened.risk == "low"
    assert softened.current_check is False
    assert parse_retrieval_packet(softened.as_dict()).as_dict() == softened.as_dict()

    assert "ai_relationship_boundary" in direct.domains
    assert direct.risk == "medium"


def test_definitional_context_softens_legal_guard_risk() -> None:
    # Grounded in v11 diagnostic case plm-sealed-v10-respond-03: asking for
    # the general meaning of a license name is a definitional question, not
    # an actionable legal request, so it shouldn't force current_check/high
    # risk the way a live regulation question does.
    softened = build_retrieval_packet("Apache 2.0の一般的な意味を短く答えてください。")
    direct = build_retrieval_packet(
        "現在進行中のAI規制・ガイドラインについて説明してください。"
    )

    assert "legal_guard" in softened.domains
    assert softened.risk == "low"
    assert softened.current_check is False

    assert "legal_guard" in direct.domains
    assert direct.risk == "high"
    assert direct.current_check is True


def test_comparative_context_softens_medical_guard_risk() -> None:
    # Grounded in v11 diagnostic case plm-sealed-v10-explain-03: comparing
    # medical-AI screen design against an actual diagnosis consultation is a
    # meta/comparative explain request, not a real diagnosis request, so the
    # risk shouldn't escalate the way a direct symptom question does.
    softened = build_retrieval_packet(
        "医療AIの画面設計と患者の診断相談の違いを説明してください。"
    )
    direct = build_retrieval_packet("片頭痛や強い不安が続く時に何を提案できますか。")

    assert "medical_guard" in softened.domains
    assert softened.risk == "low"

    assert "medical_guard" in direct.domains
    assert direct.risk == "high"


def test_knowledge_index_rejects_duplicate_domains() -> None:
    payload = load_knowledge_index(str(INDEX_PATH)).as_dict()
    payload["entries"].append(dict(payload["entries"][0]))

    with pytest.raises(ValueError, match="duplicate domain"):
        parse_knowledge_index(payload)
