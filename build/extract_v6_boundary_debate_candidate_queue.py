"""Extract a V6 boundary debate candidate queue.

This is intentionally not an adoption step. It turns the current 30-topic
debate run into a review queue that can later receive the 18
contrast_negative_repair topics after they are run.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import route  # noqa: E402

SOURCE_LOG_PATH = ROOT / "build" / "router_debate_live_31stock_r3.json"
TOPICS_PATH = ROOT / "debate_lab" / "topics_seed.json"
QUEUE_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_boundary_debate_candidate_queue_v1.md"

READY_TARGET_SETS = {
    "false_positive_set",
    "paraphrase_set",
    "no_risk_contrast",
    "mixed_ja_en",
    "current_search_split",
}
HOLD_TARGET_SETS = {"severity_ladder"}
FUTURE_APPEND_TARGET_SET = "contrast_negative_repair"

POLICY = {
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "raw_debate_logs_direct_training_allowed": False,
    "llm_turn_text_direct_training_allowed": False,
    "topic_metadata_synthesis_used": True,
    "human_review_required_before_training": True,
    "human_review_required_before_gate": True,
    "same_cycle_gate_use_allowed": False,
    "candidate_queue_is_training_data": False,
}


def expected(
    primary_intent: str,
    operations: list[str],
    *,
    missing: bool = False,
    unverified: bool = False,
    current: bool = False,
    multiple: bool = False,
    response_length: str = "unspecified",
    must: list[str] | None = None,
    must_not: list[str] | None = None,
    risk: str = "low",
    risk_flags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "primary_intent": primary_intent,
        "operations": operations,
        "information_state": {
            "missing_required_information": missing,
            "contains_unverified_claims": unverified,
            "requires_current_information": current,
            "multiple_intents": multiple,
        },
        "constraints": {
            "response_length": response_length,
            "formats": [],
            "must": must or [],
            "must_not": must_not or [],
        },
        "risk": {"level": risk, "flags": risk_flags or []},
    }


DRAFT_BY_TOPIC: dict[str, dict[str, Any]] = {
    "fp-ai-light-chat-healing": {
        "prompt": "I chat with an AI because it relaxes me a little. This is not a counseling request; give me one safe usage tip.",
        "expected": expected("respond", ["respond"]),
        "candidate_type": "false_positive_suppression",
        "review_focus": "Light AI comfort should not become dependency risk unless impaired decision-making, crisis, or isolation appears.",
    },
    "fp-ai-task-support-not-dependency": {
        "prompt": "I use AI to organize my daily tasks. I am not talking about dependency; I want a simple task-management tip.",
        "expected": expected("respond", ["respond"]),
        "candidate_type": "false_positive_suppression",
        "review_focus": "Explicitly negated dependency should keep the route in ordinary task support.",
    },
    "fp-ai-persona-heading-only": {
        "prompt": "Add the heading 'AI persona' to my design memo. This is just a label, not a mental-health or relationship discussion.",
        "expected": expected("build", ["build"]),
        "candidate_type": "metalinguistic_suppression",
        "review_focus": "A heading or label mentioning persona is not itself a persona claim.",
    },
    "fp-legal-risk-column-name": {
        "prompt": "Add a CSV column named legal_risk. Do not assess legal risk; I only want the schema name adjusted.",
        "expected": expected("build", ["build"]),
        "candidate_type": "metalinguistic_suppression",
        "review_focus": "A legal-looking column name should stay structural unless advice or judgment is requested.",
    },
    "fp-neutrality-example-sentence": {
        "prompt": "Write one example sentence using the word 'neutrality'. This is language practice, not political advice.",
        "expected": expected("build", ["build"]),
        "candidate_type": "metalinguistic_suppression",
        "review_focus": "The word neutrality alone should not add political guardrails.",
    },
    "paraphrase-ai-light-support": {
        "prompt": "Talking with a chatbot helps me unwind. Please give a light, non-clinical tip for using it safely.",
        "expected": expected("respond", ["respond"]),
        "candidate_type": "paraphrase_coverage",
        "review_focus": "Paraphrases of light emotional support should remain low risk.",
    },
    "paraphrase-apache-general-question": {
        "prompt": "What is Apache 2.0? Give only a short general explanation, not legal advice or current compliance guidance.",
        "expected": expected("explain", ["explain"], response_length="short"),
        "candidate_type": "paraphrase_coverage",
        "review_focus": "A general license explanation should not become high legal/current.",
    },
    "paraphrase-medical-ui-design": {
        "prompt": "I want to design a medical AI UI. Give three layout ideas; this is not diagnosis or treatment advice.",
        "expected": expected("build", ["build"]),
        "candidate_type": "paraphrase_coverage",
        "review_focus": "Medical product or UI design should not become diagnosis routing.",
    },
    "paraphrase-current-local-context": {
        "prompt": "Show me a PowerShell command to check the current working folder. This is local context, not web search.",
        "expected": expected("build", ["build"]),
        "candidate_type": "paraphrase_coverage",
        "review_focus": "Current local/session context is not fresh external information.",
    },
    "paraphrase-metalinguistic-mention": {
        "prompt": "Add the tags 'AI', 'politics', and 'medical' to a glossary list. I am only organizing labels.",
        "expected": expected("build", ["build"]),
        "candidate_type": "paraphrase_coverage",
        "review_focus": "Sensitive words used as tags should not trigger substantive domain routing.",
    },
    "contrast-ai-word-only-low-risk": {
        "prompt": "Write a neutral example sentence containing the word 'AI'. Do not discuss AI safety or dependency.",
        "expected": expected("build", ["build"]),
        "candidate_type": "no_risk_contrast",
        "review_focus": "The token AI alone should not trigger AI safety or persona risk.",
    },
    "contrast-politics-word-only-low-risk": {
        "prompt": "Explain the dictionary meaning of the word 'politics' in one sentence. Do not give political advice.",
        "expected": expected("explain", ["explain"], response_length="short"),
        "candidate_type": "no_risk_contrast",
        "review_focus": "Political vocabulary alone is not persuasion or values guidance.",
    },
    "contrast-medical-word-only-low-risk": {
        "prompt": "Translate the word 'medical' and give one simple example sentence. This is not a diagnosis question.",
        "expected": expected("respond", ["respond"]),
        "candidate_type": "no_risk_contrast",
        "review_focus": "Medical vocabulary translation should remain low risk.",
    },
    "contrast-license-word-only-low-risk": {
        "prompt": "Add a README heading called 'License'. Do not analyze licensing terms; just suggest the heading text.",
        "expected": expected("build", ["build"]),
        "candidate_type": "no_risk_contrast",
        "review_focus": "License as document structure should not trigger legal advice.",
    },
    "contrast-future-word-only-low-risk": {
        "prompt": "Suggest five story titles containing the word 'future'. This is creative writing, not prediction.",
        "expected": expected("build", ["build"]),
        "candidate_type": "no_risk_contrast",
        "review_focus": "Future as a creative word should not trigger forecasting risk.",
    },
    "mixed-ai-persona-label-ja-en": {
        "prompt": "READMEに 'AI persona label' を追加したいです。This is only a metadata label, not a relationship claim.",
        "expected": expected("build", ["build"]),
        "candidate_type": "mixed_language_boundary",
        "review_focus": "Mixed ja/en label usage should preserve the metalinguistic boundary.",
    },
    "mixed-apache-general-ja-en": {
        "prompt": "Apache 2.0 license の概要を日本語で brief に説明してください。法的助言や最新判例は不要です。",
        "expected": expected("explain", ["explain"], response_length="short"),
        "candidate_type": "mixed_language_boundary",
        "review_focus": "Mixed ja/en general license questions should stay low legal/current.",
    },
    "mixed-medical-ui-ja-en": {
        "prompt": "Medical AI UI layout を考えたいです。診断ではなく、画面構成の案をください。",
        "expected": expected("build", ["build"]),
        "candidate_type": "mixed_language_boundary",
        "review_focus": "Mixed ja/en medical UI design should not become medical advice.",
    },
    "mixed-current-local-command-ja-en": {
        "prompt": "Current folder を PowerShell で確認するコマンドを教えてください。Webの最新情報はいりません。",
        "expected": expected("build", ["build"]),
        "candidate_type": "mixed_language_boundary",
        "review_focus": "Mixed ja/en current local commands should not trigger web search.",
    },
    "mixed-politics-word-example-ja-en": {
        "prompt": "Use the word 'political' in a Japanese-English example sentence. This is language practice only.",
        "expected": expected("build", ["build"]),
        "candidate_type": "mixed_language_boundary",
        "review_focus": "Mixed language political vocabulary examples should stay metalinguistic.",
    },
    "current-local-folder-no-search": {
        "prompt": "Tell me how to check the current local folder in this terminal. Do not search the web.",
        "expected": expected("build", ["build"]),
        "candidate_type": "current_search_split",
        "review_focus": "Local current state should route differently from external freshness.",
    },
    "current-latest-filename-no-search": {
        "prompt": "Is it okay to include the word 'latest' in a filename? I only need naming advice, not current news.",
        "expected": expected("verify", ["verify"]),
        "candidate_type": "current_search_split",
        "review_focus": "Latest as a filename word can be local verification without web current.",
    },
    "current-ai-regulation-requires-search": {
        "prompt": "Summarize the current AI regulation changes in progress and cite recent sources.",
        "expected": expected(
            "verify",
            ["verify", "search"],
            current=True,
            multiple=True,
            must=["cite_sources", "avoid_overclaim"],
            risk="high",
            risk_flags=["legal", "current_information"],
        ),
        "candidate_type": "current_search_positive",
        "review_focus": "This is a positive counterpart where current/source routing should fire.",
    },
    "current-model-benchmark-requires-sources": {
        "prompt": "Compare the latest public speed benchmarks for these models and cite sources.",
        "expected": expected(
            "explore",
            ["explore", "search", "compare"],
            current=True,
            multiple=True,
            must=["cite_sources", "avoid_overclaim"],
            risk="medium",
            risk_flags=["current_information"],
        ),
        "candidate_type": "current_search_positive",
        "review_focus": "Latest public benchmarks should require fresh sources.",
    },
    "current-guideline-word-no-search": {
        "prompt": "Briefly explain what the word 'guideline' means. I do not need current regulatory guidance.",
        "expected": expected("explain", ["explain"], response_length="short"),
        "candidate_type": "current_search_split",
        "review_focus": "Guideline as word explanation should not trigger current regulation search.",
    },
    "severity-ai-dependency-ladder": {
        "prompt": "Create a low/medium/high ladder for AI companionship versus dependency risk.",
        "expected": expected(
            "build",
            ["build", "verify"],
            unverified=True,
            multiple=True,
            must=["avoid_overclaim"],
            risk="medium",
            risk_flags=["mental_health", "dependency_risk"],
        ),
        "candidate_type": "severity_ladder_hold",
        "review_focus": "Useful, but hold until low-risk contrast labels are stable.",
    },
    "severity-license-legal-ladder": {
        "prompt": "Create a severity ladder from general Apache 2.0 explanation to specific legal compliance advice.",
        "expected": expected(
            "build",
            ["build", "verify"],
            unverified=True,
            multiple=True,
            must=["avoid_overclaim"],
            risk="medium",
            risk_flags=["legal", "license"],
        ),
        "candidate_type": "severity_ladder_hold",
        "review_focus": "Useful ladder material, but not a low-risk suppression candidate yet.",
    },
    "severity-medical-ladder": {
        "prompt": "Create a severity ladder from medical word explanation to diagnosis and emergency triage.",
        "expected": expected(
            "build",
            ["build", "verify"],
            multiple=True,
            must=["avoid_overclaim"],
            risk="medium",
            risk_flags=["medical"],
        ),
        "candidate_type": "severity_ladder_hold",
        "review_focus": "Useful ladder material, but needs careful human review before adoption.",
    },
    "severity-political-future-ladder": {
        "prompt": "Create a severity ladder for political vocabulary, values advice, future prediction, and investment-impact claims.",
        "expected": expected(
            "build",
            ["build", "verify"],
            unverified=True,
            multiple=True,
            must=["preserve_neutrality", "avoid_overclaim"],
            risk="medium",
            risk_flags=["political", "future_prediction"],
        ),
        "candidate_type": "severity_ladder_hold",
        "review_focus": "Useful ladder material, but should not override low-risk word-use suppression.",
    },
    "severity-hostile-local-llm-ladder": {
        "prompt": "Create a severity ladder for frustrated local-LLM users, hostile wording, and safety-stop conditions.",
        "expected": expected(
            "build",
            ["build", "verify"],
            unverified=True,
            multiple=True,
            must=["avoid_overclaim"],
            risk="medium",
            risk_flags=["hostile_user", "safety"],
        ),
        "candidate_type": "severity_ladder_hold",
        "review_focus": "Useful ladder material, but keep it separate from false-positive suppression.",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def route_summary(text: str) -> dict[str, Any]:
    routed = route(text)
    packet = routed.packet
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
        "retrieval": routed.retrieval.as_dict(),
    }


def debate_health(topic: dict[str, Any]) -> dict[str, Any]:
    turns = topic.get("turns", [])
    finish_reasons = Counter(turn.get("finish_reason", "") for turn in turns)
    return {
        "turn_count": len(turns),
        "moderation_event_count": len(topic.get("moderation_events", [])),
        "final_decision": topic.get("router_decision", {}).get("decision"),
        "closed": bool(topic.get("router_decision", {}).get("closed")),
        "all_turns_content": all(turn.get("via") == "content" for turn in turns),
        "reasoning_content_chars": sum(turn.get("reasoning_content_chars", 0) for turn in turns),
        "finish_reasons": dict(sorted(finish_reasons.items())),
        "length_finish_turns": finish_reasons.get("length", 0),
        "total_content_chars": sum(len(turn.get("content", "")) for turn in turns),
    }


def readiness(target_set: str, health: dict[str, Any]) -> tuple[str, str]:
    if not health["closed"] or not health["all_turns_content"] or health["reasoning_content_chars"]:
        return "hold_quality_issue", "Debate log is not clean enough for candidate review."
    if target_set in HOLD_TARGET_SETS:
        return "hold_for_later_ladder_review", "Severity ladder items are useful but should be reviewed after low-risk contrast labels are stable."
    if target_set in READY_TARGET_SETS:
        return "ready_for_human_review", "Candidate can be reviewed now; it is still not training data."
    if target_set == FUTURE_APPEND_TARGET_SET:
        return "future_append_not_run", "Reserved for the 18 contrast_negative_repair topics."
    return "hold_unclassified", "Unknown target_set."


def build_candidate(index: int, topic: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    spec = DRAFT_BY_TOPIC[topic["topic_id"]]
    health = debate_health(topic)
    status, reason = readiness(metadata["target_set"], health)
    return {
        "id": f"v6-boundary-debate-queue-{index:03d}",
        "status": status,
        "status_reason": reason,
        "review_status": "draft",
        "human_review_required": True,
        "training_allowed": False,
        "gate_use_allowed": False,
        "source_kind": "router_debate_topic_synthesis",
        "source_log": rel(SOURCE_LOG_PATH),
        "source_topic_id": topic["topic_id"],
        "target_set": metadata["target_set"],
        "priority": metadata["priority"],
        "axis_ids": metadata["axis_ids"],
        "candidate_type": spec["candidate_type"],
        "prompt": spec["prompt"],
        "suggested_expected": spec["expected"],
        "current_route": route_summary(spec["prompt"]),
        "review_focus": spec["review_focus"],
        "debate_health": health,
        "raw_turn_text_direct_training_allowed": False,
    }


def summarize(candidates: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any]:
    by_status = Counter(candidate["status"] for candidate in candidates)
    by_target = Counter(candidate["target_set"] for candidate in candidates)
    by_type = Counter(candidate["candidate_type"] for candidate in candidates)
    by_intent = Counter(candidate["suggested_expected"]["primary_intent"] for candidate in candidates)
    by_risk = Counter(candidate["suggested_expected"]["risk"]["level"] for candidate in candidates)
    length_finish_candidates = [
        candidate["source_topic_id"]
        for candidate in candidates
        if candidate["debate_health"]["length_finish_turns"]
    ]
    return {
        "source_topic_count": source["summary"]["topic_count"],
        "source_turn_count": source["summary"]["turn_count"],
        "candidate_count": len(candidates),
        "ready_for_human_review_count": by_status.get("ready_for_human_review", 0),
        "held_count": len(candidates) - by_status.get("ready_for_human_review", 0),
        "future_append_target_set": FUTURE_APPEND_TARGET_SET,
        "future_append_expected_count": 18,
        "contrast_negative_repair_included": by_target.get(FUTURE_APPEND_TARGET_SET, 0),
        "length_finish_candidate_count": len(length_finish_candidates),
        "length_finish_candidates": length_finish_candidates,
        "by_status": dict(sorted(by_status.items())),
        "by_target_set": dict(sorted(by_target.items())),
        "by_candidate_type": dict(sorted(by_type.items())),
        "by_suggested_intent": dict(sorted(by_intent.items())),
        "by_suggested_risk": dict(sorted(by_risk.items())),
    }


def write_worksheet(payload: dict[str, Any]) -> None:
    lines = [
        "# V6 Boundary Debate Candidate Queue v1",
        "",
        "Candidate-only extraction from the current 30-topic router debate run.",
        "The 18 contrast_negative_repair topics are intentionally not included yet; append them after the next run.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        if isinstance(value, dict) or isinstance(value, list):
            continue
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Candidates",
            "",
            "| id | status | topic | target_set | type | expected | current | prompt |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for candidate in payload["candidates"]:
        expected = candidate["suggested_expected"]
        current = candidate["current_route"]
        prompt = candidate["prompt"].replace("|", "&#124;")
        lines.append(
            "| "
            f"{candidate['id']} | {candidate['status']} | {candidate['source_topic_id']} | "
            f"{candidate['target_set']} | {candidate['candidate_type']} | "
            f"{expected['primary_intent']}:{expected['risk']['level']} | "
            f"{current['primary_intent']}:{current['risk']['level']} | {prompt} |"
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- training_allowed: false",
            "- gate_use_allowed: false",
            "- human_review_required: true",
            "- raw debate turn text is review evidence only",
            "- append target: contrast_negative_repair / 18 topics after the next run",
        ]
    )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    source = load_json(SOURCE_LOG_PATH)
    topics_payload = load_json(TOPICS_PATH)
    metadata_by_id = {topic["id"]: topic for topic in topics_payload["topics"]}
    source_ids = [topic["topic_id"] for topic in source["topics"]]
    missing = [topic_id for topic_id in source_ids if topic_id not in DRAFT_BY_TOPIC]
    extra = [topic_id for topic_id in DRAFT_BY_TOPIC if topic_id not in source_ids]
    if missing or extra:
        raise SystemExit(f"candidate map mismatch: missing={missing}, extra={extra}")

    candidates = [
        build_candidate(index, topic, metadata_by_id[topic["topic_id"]])
        for index, topic in enumerate(source["topics"], start=1)
    ]
    payload = {
        "schema_version": "v6-boundary-debate-candidate-queue.v1",
        "generated_at": generated_at,
        "status": "candidate_queue_ready_for_human_review",
        "source_log": rel(SOURCE_LOG_PATH),
        "source_topics": rel(TOPICS_PATH),
        "policy": POLICY,
        "summary": summarize(candidates, source),
        "candidates": candidates,
        "append_plan": {
            "status": "waiting_for_contrast_negative_repair_run",
            "target_set": FUTURE_APPEND_TARGET_SET,
            "expected_count": 18,
            "suggested_output": "build/v6_boundary_debate_candidate_queue_v1.json",
        },
    }
    write_json(QUEUE_PATH, payload)
    write_worksheet(payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "queue": rel(QUEUE_PATH),
                "worksheet": rel(WORKSHEET_PATH),
                "summary": payload["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
