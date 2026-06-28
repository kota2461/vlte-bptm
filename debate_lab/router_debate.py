"""Run router-mediated debates between Gemma and Qwen.

The runner creates raw debate logs only. It deliberately marks outputs as
not training data until a human review step turns short, synthesized samples
into a candidate fixture.
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import route  # noqa: E402

LAB_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = LAB_ROOT / "debate_config.json"
DEFAULT_TOPICS_PATH = LAB_ROOT / "topics_seed.json"
RUNS_DIR = LAB_ROOT / "runs"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def topic_route_text(theme: str) -> str:
    return (
        f"{theme}\n"
        "中立に検証し、リスクと反論も含め、過断定を避けて議論してください。"
    )


def packet_summary(text: str) -> dict[str, Any]:
    routed = route(text)
    packet = routed.packet
    return {
        "packet": {
            "primary_intent": packet.primary_intent,
            "operations": list(packet.operations),
            "information_state": packet.information_state.as_dict(),
            "constraints": packet.constraints.as_dict(),
            "risk": packet.risk.as_dict(),
            "confidence": packet.confidence,
        },
        "processing_plan": routed.plan.as_dict(),
        "failure_guard": routed.trace.get("failure_guard", {}),
        "decided_by": routed.trace.get("decided_by", ""),
        "intent_margin": routed.trace.get("intent_margin"),
    }


def append_list_section(lines: list[str], title: str, items: list[str]) -> None:
    if not items:
        return
    lines.extend(["", title])
    lines.extend(f"- {item}" for item in items)


def router_instruction(
    theme: str,
    axis_ids: list[str],
    stage: str,
    previous: str = "",
    *,
    config: Mapping[str, Any] | None = None,
    moderator_comment: Mapping[str, Any] | str | None = None,
) -> str:
    routed = packet_summary(topic_route_text(theme))
    packet = routed["packet"]
    guard = routed["failure_guard"]
    active_config = config or {}
    goal = active_config.get("debate_goal", {})
    guidance = active_config.get("llm_guidance", {})
    output_contract = guidance.get("output_contract", {})
    contrast_guidance = active_config.get("contrast_negative_guidance", {})
    lines = [
        "You are participating in a controlled debate used to create non-sealed routing samples.",
        "The purpose is boundary calibration, especially avoiding false positives.",
        "Do not claim certainty where the theme is speculative.",
        "Separate facts, assumptions, risks, open questions, and no-risk contrasts.",
        "Do not output hidden chain-of-thought; give concise reasoning summaries only.",
        f"Stage: {stage}",
        f"Router intent: {packet['primary_intent']}",
        f"Router operations: {', '.join(packet['operations'])}",
        f"Router information_state: {json.dumps(packet['information_state'], ensure_ascii=False)}",
        f"Router constraints: {json.dumps(packet['constraints'], ensure_ascii=False)}",
        f"Router risk: {json.dumps(packet['risk'], ensure_ascii=False)}",
        f"Router guard_actions: {json.dumps(guard.get('guard_actions', []), ensure_ascii=False)}",
        f"Topic axes: {', '.join(axis_ids)}",
    ]
    if goal:
        lines.extend(
            [
                "",
                f"Debate goal: {goal.get('name', '')}",
                f"Debate objective: {goal.get('objective', '')}",
                f"Expected artifact: {goal.get('expected_artifact', '')}",
            ]
        )
    append_list_section(lines, "Shared calibration rules:", list(guidance.get("shared_rules", [])))
    if "expander" in stage:
        append_list_section(lines, "Expander tasks:", list(guidance.get("expander_tasks", [])))
    if "critic" in stage:
        append_list_section(lines, "Critic tasks:", list(guidance.get("critic_tasks", [])))
    append_list_section(
        lines,
        "Required output sections:",
        list(output_contract.get("required_sections", [])),
    )
    append_list_section(lines, "Forbidden outputs:", list(output_contract.get("forbidden", [])))
    if contrast_guidance:
        lines.extend(
            [
                "",
                f"Contrast-negative source: {contrast_guidance.get('source_fixture', '')}",
                f"Current contrast-negative gap count: {contrast_guidance.get('current_gap_count', '')}",
            ]
        )
        append_list_section(
            lines,
            "Contrast-negative focus groups:",
            list(contrast_guidance.get("focus_groups", [])),
        )
        append_list_section(
            lines,
            "Contrast-negative required discussion:",
            list(contrast_guidance.get("required_discussion", [])),
        )
    v7_guidance = active_config.get("v7_router_repair_guidance", {})
    if v7_guidance and v7_guidance.get("enabled", True):
        axis_blob = " ".join(str(axis).lower() for axis in axis_ids)
        match_tokens = [str(token).lower() for token in v7_guidance.get("match_any", [])]
        if not match_tokens or any(token in axis_blob for token in match_tokens):
            title = str(v7_guidance.get("instruction_title", "V7 router repair guidance"))
            purpose = str(v7_guidance.get("purpose", "")).strip()
            lines.extend(["", f"{title}:"])
            if purpose:
                lines.append(purpose)
            append_list_section(
                lines,
                "V7 facilitator moves:",
                list(v7_guidance.get("facilitator_moves", [])),
            )
    if moderator_comment:
        comment_text = (
            moderator_comment
            if isinstance(moderator_comment, str)
            else str(moderator_comment.get("comment", ""))
        ).strip()
        if comment_text:
            lines.extend(["", "Router moderator note:", comment_text])
    lines.extend(["", f"Theme: {theme}"])
    if previous:
        lines.extend(["", "Previous participant output:", previous])
    return "\n".join(lines)


def parse_reply(response: dict[str, Any]) -> dict[str, Any]:
    choice = response["choices"][0]
    message = choice.get("message", {})
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning_content") or "").strip()
    if content:
        via = "content"
        stored = content
    elif reasoning:
        via = "reasoning_content_suppressed"
        stored = "[reasoning_content suppressed; no final content returned]"
    else:
        via = "empty"
        stored = ""
    return {
        "content": stored,
        "via": via,
        "finish_reason": choice.get("finish_reason"),
        "reasoning_content_chars": len(reasoning),
    }


class OpenAICompatibleClient:
    def __init__(self, base_url: str, *, timeout: float = 180.0) -> None:
        self.endpoint = base_url.rstrip("/") + "/v1/chat/completions"
        self.timeout = timeout

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        data = json.dumps(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


class DryRunClient:
    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        user = messages[-1]["content"]
        if "critic" in user.lower() or "反論" in user:
            content = (
                "[dry-run] 反論: 仮説は有用だが、根拠不足・過断定・"
                "安全境界を確認してから候補化するべきです。"
            )
        else:
            content = (
                "[dry-run] 展開: テーマを事実、仮説、リスク、"
                "確認事項に分けて議論できます。"
            )
        return {
            "choices": [
                {
                    "message": {"content": content[:max_tokens]},
                    "finish_reason": "dry_run",
                }
            ]
        }


def model_turn(
    client: Any,
    *,
    model: str,
    role_name: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    reply = parse_reply(response)
    content = reply["content"]
    return {
        "role": role_name,
        "model": model,
        "content": content,
        "via": reply["via"],
        "finish_reason": reply["finish_reason"],
        "reasoning_content_chars": reply["reasoning_content_chars"],
        "router_after_turn": packet_summary(content),
    }


def candidate_stub(topic: dict[str, Any], turns: list[dict[str, Any]]) -> dict[str, Any]:
    combined = "\n".join(turn["content"] for turn in turns)
    routed = packet_summary(topic_route_text(topic["theme"]) + "\n" + combined[:1200])
    return {
        "status": "draft_stub_requires_human_review",
        "training_allowed": False,
        "source": "router_debate_raw_log",
        "topic_id": topic["id"],
        "suggested_input": topic["theme"],
        "suggested_axes": topic["axis_ids"],
        "router_packet_hint": routed["packet"],
        "notes": "Use only as a review aid. Rewrite into a short self-contained sample before fixture adoption.",
    }


def moderator_settings(config: dict[str, Any]) -> dict[str, int | bool]:
    moderator = dict(config.get("moderator", {}))
    min_rounds = int(moderator.get("min_rounds", 1))
    max_rounds = int(moderator.get("max_rounds", config.get("rounds", min_rounds)))
    max_rounds = max(min_rounds, max_rounds)
    return {
        "min_rounds": min_rounds,
        "max_rounds": max_rounds,
        "min_total_chars_to_close": int(moderator.get("min_total_chars_to_close", 80)),
        "require_critic_final_content": bool(moderator.get("require_critic_final_content", True)),
    }


def router_moderation_decision(
    topic: dict[str, Any],
    turns: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    settings = moderator_settings(config)
    completed_rounds = len(turns) // 2
    combined = "\n".join(turn["content"] for turn in turns)
    routed = packet_summary(topic_route_text(topic["theme"]) + "\n" + combined[:2000])
    roles = {turn["role"] for turn in turns}
    critic_turns = [turn for turn in turns if turn["role"] == "qwen_critic"]
    last_critic = critic_turns[-1] if critic_turns else None
    critic_has_final_content = bool(
        last_critic
        and last_critic["via"] == "content"
        and last_critic["content"].strip()
    )
    has_suppressed_reasoning = any(
        turn["via"] == "reasoning_content_suppressed" for turn in turns
    )
    total_content_chars = sum(
        len(turn["content"])
        for turn in turns
        if turn["via"] == "content"
    )
    checks = {
        "completed_rounds": completed_rounds,
        "has_gemma_expander": "gemma_expander" in roles,
        "has_qwen_critic": "qwen_critic" in roles,
        "critic_has_final_content": critic_has_final_content,
        "has_suppressed_reasoning": has_suppressed_reasoning,
        "total_content_chars": total_content_chars,
        "min_rounds": settings["min_rounds"],
        "max_rounds": settings["max_rounds"],
        "min_total_chars_to_close": settings["min_total_chars_to_close"],
    }
    reasons: list[str] = []
    close_ready = (
        completed_rounds >= settings["min_rounds"]
        and checks["has_gemma_expander"]
        and checks["has_qwen_critic"]
        and total_content_chars >= settings["min_total_chars_to_close"]
        and (
            critic_has_final_content
            or not settings["require_critic_final_content"]
        )
    )
    if completed_rounds >= settings["max_rounds"]:
        closed = True
        reasons.append("max_rounds_reached")
    elif close_ready:
        closed = True
        reasons.append("router_close_criteria_met")
    else:
        closed = False
        if completed_rounds < settings["min_rounds"]:
            reasons.append("below_min_rounds")
        if not checks["has_qwen_critic"]:
            reasons.append("critic_turn_missing")
        if settings["require_critic_final_content"] and not critic_has_final_content:
            reasons.append("critic_final_content_missing")
        if total_content_chars < settings["min_total_chars_to_close"]:
            reasons.append("insufficient_content")
        if has_suppressed_reasoning:
            reasons.append("reasoning_content_suppressed")
    return {
        "schema_version": "router-debate-moderation-decision.v1",
        "topic_id": topic["id"],
        "decision": "close_topic" if closed else "continue_topic",
        "closed": closed,
        "reasons": reasons,
        "checks": checks,
        "router_packet": routed["packet"],
        "failure_guard": routed["failure_guard"],
        "next_gemma_action": "start_next_topic" if closed else "continue_current_topic",
    }

def _axis_blob(topic: Mapping[str, Any]) -> str:
    parts = [
        str(topic.get("id", "")),
        str(topic.get("target_set", "")),
        str(topic.get("theme", "")),
    ]
    parts.extend(str(axis) for axis in topic.get("axis_ids", []))
    return " ".join(parts).lower()


def router_moderator_comment(
    topic: dict[str, Any],
    turns: list[dict[str, Any]],
    decision: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    support = dict(config.get("moderator_support", {}))
    if not support.get("enabled", True):
        return {
            "enabled": False,
            "style": "disabled",
            "comment": "",
            "matched_rule_ids": [],
            "weak_metrics": [],
        }

    blob = _axis_blob(topic)
    matched_rules: list[dict[str, Any]] = []
    for rule in support.get("theme_focus_rules", []):
        tokens = [str(token).lower() for token in rule.get("match_any", [])]
        if any(token in blob for token in tokens):
            matched_rules.append(rule)

    max_focus_notes = int(support.get("max_focus_notes", 4))
    notes = [str(rule.get("note", "")).strip() for rule in matched_rules]
    notes = [note for note in notes if note][:max_focus_notes]
    if not notes:
        notes = list(support.get("fallback_focus", []))[:max_focus_notes]

    measured = dict(support.get("measured_weaknesses", {}))
    metric_names = list(
        support.get(
            "weak_metric_names",
            [
                "intent_accuracy",
                "critical_signal_recall",
                "operation_exact_match",
                "constraint_exact_match",
                "risk_exact_match",
            ],
        )
    )
    weak_metric_threshold = float(support.get("weak_metric_threshold", 0.5))
    weak_metrics = [
        metric
        for metric in metric_names
        if metric in measured and float(measured.get(metric, 1.0)) < weak_metric_threshold
    ]
    metric_text = ", ".join(weak_metrics) if weak_metrics else "current weak fields"
    next_action = "close extraction" if decision.get("closed") else "next Gemma turn"
    directive = (
        f"Moderator note: for {next_action}, focus on {metric_text}. "
        "Make the boundary explicit, add one should_fire and one should_not_fire pair, "
        "and avoid turning mere sensitive words into high-risk routes."
    )
    if notes:
        directive += " Focus notes: " + " / ".join(notes)
    v7_guidance = dict(config.get("v7_router_repair_guidance", {}))
    if v7_guidance.get("enabled", False):
        match_tokens = [str(token).lower() for token in v7_guidance.get("match_any", [])]
        if match_tokens and any(token in blob for token in match_tokens):
            comment = str(v7_guidance.get("moderator_comment", "")).strip()
            if comment:
                directive += " V7 facilitator note: " + comment
    if turns and turns[-1].get("via") == "reasoning_content_suppressed":
        directive += " Ask for concise final content because the previous turn returned suppressed reasoning."

    return {
        "enabled": True,
        "style": str(support.get("style", "light_facilitator_comment")),
        "comment": directive,
        "matched_rule_ids": [str(rule.get("id", "")) for rule in matched_rules if rule.get("id")],
        "weak_metrics": weak_metrics,
        "topic_target_set": topic.get("target_set"),
    }

def run_topic(
    client: Any,
    *,
    topic: dict[str, Any],
    config: dict[str, Any],
    gemma_model: str,
    qwen_model: str,
) -> dict[str, Any]:
    max_tokens = int(config["max_tokens"])
    temperature = float(config["temperature"])
    settings = moderator_settings(config)
    turns: list[dict[str, Any]] = []
    moderation_events: list[dict[str, Any]] = []
    next_moderator_comment: dict[str, Any] | None = None
    last_critic_output = ""
    theme = topic["theme"]
    axis_ids = list(topic["axis_ids"])

    for index in range(1, int(settings["max_rounds"]) + 1):
        gemma_previous = last_critic_output if index > 1 else ""
        gemma_user = router_instruction(
            theme,
            axis_ids,
            f"round-{index}: expander",
            previous=gemma_previous,
            config=config,
            moderator_comment=next_moderator_comment,
        )
        gemma_turn = model_turn(
            client,
            model=gemma_model,
            role_name="gemma_expander",
            system="Expand the theme into useful contrast rules and candidate sample ideas. Follow router facilitator notes and keep claims bounded.",
            user=gemma_user,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        turns.append(gemma_turn)

        qwen_user = "/no_think\n" + router_instruction(
            theme,
            axis_ids,
            f"round-{index}: critic",
            previous=gemma_turn["content"],
            config=config,
            moderator_comment=next_moderator_comment,
        )
        qwen_turn = model_turn(
            client,
            model=qwen_model,
            role_name="qwen_critic",
            system=(
                "/no_think\n"
                "Critique the previous answer. Return only the final critique. "
                "Check false positives, negated scope, mention-vs-use, current/search split, severity, risks, terminal actions, and better labels."
            ),
            user=qwen_user,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        turns.append(qwen_turn)
        last_critic_output = qwen_turn["content"]

        decision = router_moderation_decision(topic, turns, config)
        next_moderator_comment = router_moderator_comment(topic, turns, decision, config)
        decision["moderator_comment"] = next_moderator_comment
        moderation_events.append(decision)
        if decision["closed"]:
            break

    final_decision = moderation_events[-1] if moderation_events else router_moderation_decision(topic, turns, config)
    return {
        "topic_id": topic["id"],
        "theme": theme,
        "axis_ids": axis_ids,
        "router_before": packet_summary(topic_route_text(theme)),
        "turns": turns,
        "moderation_events": moderation_events,
        "router_decision": final_decision,
        "candidate_stub": candidate_stub(topic, turns),
    }

def select_topics(
    payload: dict[str, Any],
    topic_id: str | None,
    target_set: str | None,
    max_topics: int | None,
) -> list[dict[str, Any]]:
    topics = list(payload["topics"])
    if topic_id:
        topics = [topic for topic in topics if topic["id"] == topic_id]
        if not topics:
            raise ValueError(f"unknown topic id: {topic_id}")
    if target_set:
        topics = [topic for topic in topics if topic.get("target_set") == target_set]
        if not topics:
            raise ValueError(f"unknown target_set: {target_set}")
    if max_topics is not None:
        topics = topics[:max_topics]
    return topics


def build_router_progression(topic_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = []
    for index, result in enumerate(topic_results):
        next_topic_id = (
            topic_results[index + 1]["topic_id"]
            if index + 1 < len(topic_results)
            else None
        )
        decision = result["router_decision"]
        events.append(
            {
                "event": "topic_closed" if decision["closed"] else "topic_paused",
                "topic_id": result["topic_id"],
                "router_decision": decision["decision"],
                "reasons": decision["reasons"],
                "next_topic_id": next_topic_id,
                "next_gemma_action": (
                    "start_next_topic"
                    if decision["closed"] and next_topic_id is not None
                    else "stop_queue"
                    if decision["closed"]
                    else "continue_current_topic"
                ),
            }
        )
    return events

def build_run_payload(
    *,
    config: dict[str, Any],
    topics_payload: dict[str, Any],
    topic_results: list[dict[str, Any]],
    dry_run: bool,
    output_path: Path,
    gemma_model: str,
    qwen_model: str,
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "router-debate-run.v1",
        "generated_at": generated_at,
        "dry_run": dry_run,
        "output": display_path(output_path),
        "config_schema_version": config["schema_version"],
        "topics_schema_version": topics_payload["schema_version"],
        "models": {
            "gemma": {**config["models"]["gemma"], "id": gemma_model},
            "qwen": {**config["models"]["qwen"], "id": qwen_model},
        },
        "policy": config["policy"],
        "router_topic_stock": {
            "stock_count": len(topics_payload["topics"]),
            "selected_count": len(topic_results),
            "selected_topic_ids": [item["topic_id"] for item in topic_results],
        },
        "router_progression": build_router_progression(topic_results),
        "summary": {
            "topic_count": len(topic_results),
            "turn_count": sum(len(item["turns"]) for item in topic_results),
            "closed_topic_count": sum(
                1 for item in topic_results if item["router_decision"]["closed"]
            ),
            "candidate_stub_count": len(topic_results),
            "training_allowed": False,
            "human_review_required": True,
            "moderator_comment_count": sum(
                1
                for item in topic_results
                for event in item["moderation_events"]
                if event.get("moderator_comment", {}).get("enabled")
            ),
        },
        "topics": topic_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run router-mediated Gemma/Qwen debates.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--topics", default=str(DEFAULT_TOPICS_PATH))
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--gemma-model", default=None)
    parser.add_argument("--qwen-model", default=None)
    parser.add_argument("--topic-id", default=None)
    parser.add_argument("--target-set", default=None)
    parser.add_argument("--max-topics", type=int, default=None)
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--min-rounds", type=int, default=None)
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_json(Path(args.config))
    topics_payload = load_json(Path(args.topics))
    moderator = config.setdefault("moderator", {})
    if args.rounds is not None:
        config["rounds"] = args.rounds
        moderator["min_rounds"] = args.rounds
        moderator["max_rounds"] = args.rounds
    if args.min_rounds is not None:
        moderator["min_rounds"] = args.min_rounds
    if args.max_rounds is not None:
        moderator["max_rounds"] = args.max_rounds
    if args.max_tokens is not None:
        config["max_tokens"] = args.max_tokens
    if args.temperature is not None:
        config["temperature"] = args.temperature
    base_url = args.base_url or config["base_url"]
    gemma_model = args.gemma_model or config["models"]["gemma"]["id"]
    qwen_model = args.qwen_model or config["models"]["qwen"]["id"]
    topics = select_topics(topics_payload, args.topic_id, args.target_set, args.max_topics)
    client = DryRunClient() if args.dry_run else OpenAICompatibleClient(base_url)

    topic_results = [
        run_topic(
            client,
            topic=topic,
            config=config,
            gemma_model=gemma_model,
            qwen_model=qwen_model,
        )
        for topic in topics
    ]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = Path(args.output) if args.output else RUNS_DIR / f"{timestamp}_router_debate.json"
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    payload = build_run_payload(
        config=config,
        topics_payload=topics_payload,
        topic_results=topic_results,
        dry_run=args.dry_run,
        output_path=output_path,
        gemma_model=gemma_model,
        qwen_model=qwen_model,
    )
    write_json(output_path, payload)
    print(json.dumps({
        "status": "wrote_router_debate_run",
        "output": display_path(output_path),
        "summary": payload["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
