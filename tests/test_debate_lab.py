import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from debate_lab.router_debate import (
    DryRunClient,
    load_json,
    router_instruction,
    router_moderator_comment,
    run_topic,
    select_topics,
    topic_route_text,
)
from semantic_routing import route


ROOT = Path(__file__).parents[1]
CONFIG_PATH = ROOT / "debate_lab" / "debate_config.json"
TOPICS_PATH = ROOT / "debate_lab" / "topics_seed.json"


EXPECTED_TARGET_SETS = {
    "false_positive_set",
    "paraphrase_set",
    "no_risk_contrast",
    "mixed_ja_en",
    "current_search_split",
    "severity_ladder",
    "contrast_negative_repair",
    "v7_router_repair_discussion",
}


def test_debate_config_keeps_raw_logs_out_of_training() -> None:
    config = load_json(CONFIG_PATH)

    assert config["schema_version"] == "router-debate-config.v1"
    assert config["temperature"] == 0.25
    assert config["max_tokens"] == 1200
    assert config["policy"] == {
        "sealed_fixtures_used_as_sources": False,
        "raw_debate_log_training_allowed": False,
        "candidate_training_allowed_without_human_review": False,
        "same_cycle_gate_use_allowed": False,
    }
    assert config["moderator"] == {
        "min_rounds": 4,
        "max_rounds": 4,
        "min_total_chars_to_close": 80,
        "require_critic_final_content": True,
    }
    assert set(config["models"]) == {"gemma", "qwen"}
    assert config["moderator_support"]["enabled"] is True
    assert config["moderator_support"]["style"] == "light_facilitator_comment"
    assert config["moderator_support"]["measured_weaknesses"]["intent_accuracy"] == 0.785714
    assert config["moderator_support"]["measured_weaknesses"]["critical_signal_recall"] == 0.642857
    assert config["moderator_support"]["measured_weaknesses"]["operation_exact_match"] == 0.714286
    assert config["moderator_support"]["measured_weaknesses"]["constraint_exact_match"] == 0.75
    assert config["moderator_support"]["measured_weaknesses"]["risk_exact_match"] == 0.785714
    assert config["moderator_support"]["weak_metric_threshold"] == 0.8
    assert "metalinguistic_mention" in {rule["id"] for rule in config["moderator_support"]["theme_focus_rules"]}
    assert config["debate_goal"]["name"] == "v8_recovery_round4_boundary_calibration"
    assert "Do not treat every sensitive-looking keyword as risk." in config["llm_guidance"]["shared_rules"]
    assert "classification_rule" in config["llm_guidance"]["output_contract"]["required_sections"]
    assert config["contrast_negative_guidance"]["source_fixture"] == "tests/fixtures/v6_contrast_negative_benchmark_v1.json"
    assert config["contrast_negative_guidance"]["current_gap_count"] == 17
    assert "ai_label_use" in config["contrast_negative_guidance"]["focus_groups"]
    assert config["v7_router_repair_guidance"]["enabled"] is True
    assert "cheap_sufficient_route" in config["llm_guidance"]["output_contract"]["required_sections"]
    assert "terminal_action" in config["llm_guidance"]["output_contract"]["required_sections"]


def test_topic_stock_is_replaced_with_v6_boundary_sets() -> None:
    topics = load_json(TOPICS_PATH)["topics"]
    counts = Counter(topic["target_set"] for topic in topics)

    assert len(topics) == 53
    assert set(counts) == EXPECTED_TARGET_SETS
    assert all(counts[target_set] == 5 for target_set in EXPECTED_TARGET_SETS if target_set != "contrast_negative_repair")
    assert counts["contrast_negative_repair"] == 18
    assert counts["v7_router_repair_discussion"] == 5
    assert topics[0]["id"] == "fp-ai-light-chat-healing"
    assert topics[0]["target_set"] == "false_positive_set"


def test_select_topics_can_filter_contrast_negative_repair() -> None:
    payload = load_json(TOPICS_PATH)
    selected = select_topics(payload, topic_id=None, target_set="contrast_negative_repair", max_topics=None)

    assert len(selected) == 18
    assert all(topic["target_set"] == "contrast_negative_repair" for topic in selected)
    assert selected[0]["id"] == "repair-ai-label-use-respond-vs-verify"
    assert selected[-1]["id"] == "repair-negative-positive-counterpair-matrix"


def test_select_topics_can_filter_v7_router_repair_discussion() -> None:
    payload = load_json(TOPICS_PATH)
    selected = select_topics(payload, topic_id=None, target_set="v7_router_repair_discussion", max_topics=None)

    assert len(selected) == 5
    assert selected[0]["id"] == "v7-ambiguous-clarify-vs-build"
    assert selected[-1]["id"] == "v7-terminal-action-boundary"
    assert all("v7_router_repair" in topic["axis_ids"] for topic in selected)

def test_topic_route_text_turns_theme_into_moderated_verify_request() -> None:
    topics = load_json(TOPICS_PATH)["topics"]
    packet = route(topic_route_text(topics[0]["theme"])).packet

    assert packet.primary_intent == "verify"
    assert "verify" in packet.operations
    assert "preserve_neutrality" in packet.constraints.must
    assert "avoid_overclaim" in packet.constraints.must


def test_router_instruction_includes_boundary_calibration_guidance() -> None:
    config = load_json(CONFIG_PATH)
    topic = load_json(TOPICS_PATH)["topics"][0]
    instruction = router_instruction(
        topic["theme"],
        list(topic["axis_ids"]),
        "round-1: expander",
        config=config,
    )

    assert "Debate goal: v8_recovery_round4_boundary_calibration" in instruction
    assert "Shared calibration rules:" in instruction
    assert "Do not treat every sensitive-looking keyword as risk." in instruction
    assert "For AI-persona topics" in instruction
    assert "Expander tasks:" in instruction
    assert "Required output sections:" in instruction
    assert "classification_rule" in instruction
    assert "Contrast-negative source:" in instruction
    assert "Contrast-negative focus groups:" in instruction
    assert "positive-fire counterpart" in instruction


def test_router_instruction_includes_v7_facilitator_guidance() -> None:
    config = load_json(CONFIG_PATH)
    topic = next(
        topic
        for topic in load_json(TOPICS_PATH)["topics"]
        if topic["id"] == "v7-ambiguous-clarify-vs-build"
    )
    instruction = router_instruction(
        topic["theme"],
        list(topic["axis_ids"]),
        "round-1: expander",
        config=config,
    )

    assert "V7 router repair guidance:" in instruction
    assert "minimal should_fire / should_not_fire pair" in instruction
    assert "cheap sufficient route" in instruction
    assert "terminal action" in instruction

def test_router_instruction_accepts_light_moderator_comment() -> None:
    config = load_json(CONFIG_PATH)
    topic = load_json(TOPICS_PATH)["topics"][0]
    comment = {
        "enabled": True,
        "comment": "Moderator note: focus next turn on intent boundary and risk downshift.",
    }
    instruction = router_instruction(
        topic["theme"],
        list(topic["axis_ids"]),
        "round-2: expander",
        previous="Prior critic output",
        config=config,
        moderator_comment=comment,
    )

    assert "Router moderator note:" in instruction
    assert "intent boundary and risk downshift" in instruction
    assert "Previous participant output:" in instruction
    assert "Prior critic output" in instruction


def test_router_moderator_comment_focuses_measured_weaknesses() -> None:
    config = load_json(CONFIG_PATH)
    topic = load_json(TOPICS_PATH)["topics"][0]
    turns = [
        {"role": "gemma_expander", "content": "draft", "via": "content"},
        {"role": "qwen_critic", "content": "critique", "via": "content"},
    ]
    decision = {"closed": False}

    comment = router_moderator_comment(topic, turns, decision, config)

    assert comment["enabled"] is True
    assert comment["style"] == "light_facilitator_comment"
    assert comment["weak_metrics"] == [
        "intent_accuracy",
        "critical_signal_recall",
        "operation_exact_match",
        "constraint_exact_match",
        "risk_exact_match",
    ]
    assert "Moderator note:" in comment["comment"]
    assert "should_fire" in comment["comment"]
    assert "ai_dependency_boundary" in comment["matched_rule_ids"]

def test_router_moderator_comment_adds_v7_facilitator_note() -> None:
    config = load_json(CONFIG_PATH)
    topic = next(
        topic
        for topic in load_json(TOPICS_PATH)["topics"]
        if topic["id"] == "v7-unverified-claim-strength"
    )
    turns = [
        {"role": "gemma_expander", "content": "draft", "via": "content"},
        {"role": "qwen_critic", "content": "critique", "via": "content"},
    ]
    decision = {"closed": False}

    comment = router_moderator_comment(topic, turns, decision, config)

    assert comment["enabled"] is True
    assert "V7 facilitator note:" in comment["comment"]
    assert "cheap_sufficient_route" in comment["comment"]
    assert "unverified_claim_boundary" in comment["matched_rule_ids"]

def test_contrast_negative_repair_topics_cover_current_misses() -> None:
    topics = load_json(TOPICS_PATH)["topics"]
    repair_topics = [topic for topic in topics if topic["target_set"] == "contrast_negative_repair"]
    axes = {axis for topic in repair_topics for axis in topic["axis_ids"]}

    assert len(repair_topics) == 18
    assert repair_topics[0]["id"] == "repair-ai-label-use-respond-vs-verify"
    assert repair_topics[-1]["id"] == "repair-negative-positive-counterpair-matrix"
    assert {
        "ai_label_use",
        "license_label_use",
        "legal_label_use",
        "medical_data_design",
        "current_local_context",
        "guideline_word_use",
        "search_label_use",
        "regulation_label_use",
    } <= axes
    assert all("positive_fire_counterpart" in topic["axis_ids"] for topic in repair_topics)


def test_dry_run_topic_has_gemma_qwen_turns_and_candidate_stub() -> None:
    config = load_json(CONFIG_PATH)
    topic = load_json(TOPICS_PATH)["topics"][0]
    result = run_topic(
        DryRunClient(),
        topic=topic,
        config=config,
        gemma_model="gemma-test",
        qwen_model="qwen-test",
    )

    assert result["topic_id"] == topic["id"]
    assert [turn["role"] for turn in result["turns"]] == [
        "gemma_expander",
        "qwen_critic",
        "gemma_expander",
        "qwen_critic",
        "gemma_expander",
        "qwen_critic",
        "gemma_expander",
        "qwen_critic",
    ]
    assert all(turn["finish_reason"] == "dry_run" for turn in result["turns"])
    assert result["candidate_stub"]["training_allowed"] is False
    assert result["candidate_stub"]["status"] == "draft_stub_requires_human_review"
    assert "avoid_overclaim" in result["candidate_stub"]["router_packet_hint"]["constraints"]["must"]
    assert result["router_decision"]["decision"] == "close_topic"
    assert result["router_decision"]["next_gemma_action"] == "start_next_topic"
    assert result["moderation_events"][0]["decision"] == "continue_topic"
    assert "below_min_rounds" in result["moderation_events"][0]["reasons"]
    assert result["moderation_events"][0]["moderator_comment"]["enabled"] is True
    assert "intent_accuracy" in result["moderation_events"][0]["moderator_comment"]["weak_metrics"]
    assert result["moderation_events"][0]["moderator_comment"]["matched_rule_ids"]
    assert len(result["moderation_events"]) == 4


def test_debate_cli_writes_dry_run_report(tmp_path: Path) -> None:
    output = tmp_path / "router_debate.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "debate_lab" / "router_debate.py"),
            "--dry-run",
            "--max-topics",
            "1",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "wrote_router_debate_run" in completed.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "router-debate-run.v1"
    assert payload["dry_run"] is True
    assert payload["summary"] == {
        "topic_count": 1,
        "turn_count": 8,
        "closed_topic_count": 1,
        "candidate_stub_count": 1,
        "training_allowed": False,
        "human_review_required": True,
        "moderator_comment_count": 4,
    }
    assert payload["router_topic_stock"]["stock_count"] == 53
    assert payload["router_topic_stock"]["selected_count"] == 1
    assert payload["router_progression"][0]["event"] == "topic_closed"
    assert payload["router_progression"][0]["next_gemma_action"] == "stop_queue"