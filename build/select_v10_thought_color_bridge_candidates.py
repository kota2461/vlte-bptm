"""Select Thought Color bridge candidates for V10 mainline review.

Thought Color adopted samples are useful as boundary judgments, but they are
not mainline training data. This script distills the adopted experiment-only
samples into a review worksheet for V10 bridge candidates.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments" / "2026-06-26_layered-thought-color" / "data" / "thought_color_adopted_full_v0_2.json"
SOURCE_REPORT = ROOT / "experiments" / "2026-06-26_layered-thought-color" / "reports" / "thought_color_adoption_full_v0_2.json"
V9_MEASUREMENT = ROOT / "build" / "pattern_language_sealed_v9_measurement_report.json"
OUTPUT = ROOT / "build" / "v10_thought_color_bridge_candidate_selection_v1.json"
WORKSHEET = ROOT / "build" / "v10_thought_color_bridge_review_worksheet_v1.md"


POLICY = {
    "source_scope": "thought_color_experiment_only",
    "source_mainline_training_allowed": False,
    "source_experiment_training_allowed": True,
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "bridge_selection_is_training_data": False,
    "raw_thought_color_samples_direct_training_allowed": False,
    "human_review_required_before_fixture_adoption": True,
    "human_rewrite_required_before_gate": True,
    "same_cycle_gate_use_allowed": False,
}

PRIMARY_QUOTAS = {
    "constraint_bridge": 18,
    "risk_bridge": 16,
    "information_state_bridge": 14,
    "operation_bridge": 14,
    "intent_boundary_bridge": 10,
}

CATEGORY_NOTES = {
    "constraint_bridge": "Use modifier stance/intensity as a constraint-boundary judgment; rewrite into explicit must/must_not or response-style controls.",
    "risk_bridge": "Use challenge/reserve/empathize/high-intensity modifiers to calibrate low/medium/high risk without overfiring.",
    "information_state_bridge": "Use clarify/hold/missing-context modifiers to decide when information is missing and when to ask first.",
    "operation_bridge": "Use operation-channel contrasts to stabilize terminal action and operation ordering.",
    "intent_boundary_bridge": "Use base-label contrasts to stabilize primary_intent boundaries without copying Thought Color labels.",
}

BASE_TO_INTENT = {
    "direct_answer": "respond",
    "mechanism_explanation": "explain",
    "clarification_gate": "clarify",
    "artifact_generation": "build",
    "verification_review": "verify",
    "summary_compression": "summarize",
    "exploration_tradeoff": "explore",
    "supportive_processing": "respond",
}

OPERATION_TO_MAINLINE = {
    "respond": "respond",
    "reason": "explain",
    "compare": "compare",
    "verify": "verify",
    "generate": "build",
    "remember": "summarize",
    "route": "clarify",
}

SOURCE_KIND_WEIGHT = {
    "codex_corrective_contrast": 48,
    "codex_weakness_isolated_contrast": 44,
    "codex_summary_share_stance_correction": 42,
    "codex_targeted_gap_contrast": 38,
    "gemma4_synthetic_contrast": 24,
}

LANE_CATEGORY_WEIGHTS = {
    "constraint_bridge": {
        "same_base_different_stance": 26,
        "intensity_anchor": 26,
        "supportive_modifier": 22,
        "summary_share_stance_correction": 34,
        "collision_should_share": 14,
    },
    "risk_bridge": {
        "verify_stance_variants_isolated": 34,
        "empathy_across_bases_isolated": 24,
        "intensity_anchor": 22,
        "collision_should_split": 18,
        "same_base_different_stance": 12,
    },
    "information_state_bridge": {
        "missing_context": 48,
        "same_base_different_stance": 18,
        "collision_should_split": 16,
    },
    "operation_bridge": {
        "same_base_different_operation": 34,
        "same_operation_different_base": 28,
        "code_request_split_correction": 36,
        "build_operation_variants_correction": 38,
        "summary_share_variants_isolated": 30,
        "generate_across_bases_isolated": 24,
        "explore_operation_variants_isolated": 24,
    },
    "intent_boundary_bridge": {
        "same_operation_different_base": 34,
        "collision_should_split": 26,
        "collision_should_share": 22,
        "code_request_split_correction": 18,
    },
}

V9_FIELD_TO_CATEGORY_WEIGHT = {
    "constraints": {"constraint_bridge": 5, "operation_bridge": 1},
    "risk": {"risk_bridge": 5, "constraint_bridge": 1},
    "information_state": {"information_state_bridge": 5, "intent_boundary_bridge": 1},
    "operations": {"operation_bridge": 5, "intent_boundary_bridge": 2},
    "primary_intent": {"intent_boundary_bridge": 5, "operation_bridge": 1},
}

CRITICAL_SIGNAL_TO_CATEGORY_WEIGHT = {
    "contains_unverified_claims": {"risk_bridge": 10, "operation_bridge": 2},
    "multiple_intents": {"operation_bridge": 8, "intent_boundary_bridge": 6, "information_state_bridge": 2},
    "missing_required_information": {"information_state_bridge": 5},
    "requires_current_information": {"risk_bridge": 3, "information_state_bridge": 2},
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _v9_field_counts(measurement: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in measurement["measurements"].get("errors", []):
        counts.update(error.get("fields", []))
    return counts


def _critical_miss_counts(measurement: dict[str, Any]) -> dict[str, int]:
    signals = measurement["measurements"].get("critical_signals", {})
    return {
        name: int(round(float(data.get("support", 0)) * (1.0 - float(data.get("recall", 0.0)))))
        for name, data in signals.items()
    }


def _candidate_categories(sample: dict[str, Any]) -> set[str]:
    expected = sample["expected"]
    lane = sample.get("lane", "")
    stance = expected.get("stance")
    operation = expected.get("operation")
    intensity = expected.get("intensity")
    base = expected.get("base_label")
    categories: set[str] = set()

    if lane in {"same_base_different_stance", "intensity_anchor", "supportive_modifier", "summary_share_stance_correction", "collision_should_share"}:
        categories.add("constraint_bridge")
    if stance in {"clarify", "empathize", "challenge", "reserve"} or intensity in {"high", "hold"}:
        categories.add("constraint_bridge")

    if lane in {"verify_stance_variants_isolated", "empathy_across_bases_isolated"} or stance in {"challenge", "reserve"} or intensity == "high":
        categories.add("risk_bridge")

    if lane == "missing_context" or stance == "clarify" or intensity == "hold":
        categories.add("information_state_bridge")

    if lane in {
        "same_base_different_operation",
        "same_operation_different_base",
        "code_request_split_correction",
        "build_operation_variants_correction",
        "summary_share_variants_isolated",
        "summary_share_stance_correction",
        "generate_across_bases_isolated",
        "explore_operation_variants_isolated",
    }:
        categories.add("operation_bridge")
    if operation in {"compare", "verify", "generate", "remember", "route"}:
        categories.add("operation_bridge")

    if lane in {"same_operation_different_base", "collision_should_split", "collision_should_share", "code_request_split_correction"}:
        categories.add("intent_boundary_bridge")
    if base in {"clarification_gate", "verification_review", "summary_compression", "supportive_processing"}:
        categories.add("intent_boundary_bridge")

    return categories or {"intent_boundary_bridge"}


def _category_score(sample: dict[str, Any], category: str, field_counts: Counter[str], critical_misses: dict[str, int]) -> int:
    expected = sample["expected"]
    lane = sample.get("lane", "")
    score = SOURCE_KIND_WEIGHT.get(sample.get("source_kind", ""), 10)
    score += LANE_CATEGORY_WEIGHTS.get(category, {}).get(lane, 0)
    for field, count in field_counts.items():
        score += V9_FIELD_TO_CATEGORY_WEIGHT.get(field, {}).get(category, 0) * int(count)
    for signal, count in critical_misses.items():
        score += CRITICAL_SIGNAL_TO_CATEGORY_WEIGHT.get(signal, {}).get(category, 0) * int(count)
    if sample.get("near_miss"):
        score += 14
    if sample.get("collision_policy"):
        score += 8
    if sample.get("judgment_questions"):
        score += min(8, len(sample.get("judgment_questions", [])) * 2)
    if expected.get("stance") in {"challenge", "reserve", "clarify"}:
        score += 8
    if expected.get("intensity") == "hold":
        score += 8
    if expected.get("intensity") == "high" and category == "risk_bridge":
        score += 8
    if sample.get("display_safe_repair"):
        score -= 3
    if len(str(sample.get("input", ""))) < 18:
        score -= 6
    return score


def _semantic_packet_hint(sample: dict[str, Any], category: str) -> dict[str, Any]:
    expected = sample["expected"]
    primary = BASE_TO_INTENT.get(expected.get("base_label", ""), "respond")
    operation = OPERATION_TO_MAINLINE.get(expected.get("operation", ""), primary)
    operations = [operation]
    if category == "operation_bridge" and operation != primary:
        operations = [primary, operation]
    if category == "intent_boundary_bridge":
        operations = [primary]
    if expected.get("stance") == "explore" and "compare" not in operations:
        operations.append("compare")
    if expected.get("stance") == "challenge" and "verify" not in operations:
        operations.append("verify")

    missing = category == "information_state_bridge" or expected.get("stance") == "clarify" or expected.get("intensity") == "hold"
    unverified = expected.get("stance") in {"challenge", "reserve"}
    multiple = len(set(operations)) > 1
    risk_level = "low"
    if expected.get("stance") in {"challenge", "reserve"} or expected.get("intensity") == "high":
        risk_level = "medium"
    if expected.get("intensity") == "hold" and expected.get("stance") == "reserve":
        risk_level = "high"

    must = []
    if expected.get("stance") == "clarify" or missing:
        must.append("ask_first")
    if expected.get("stance") == "challenge":
        must.append("avoid_overclaim")
    if expected.get("stance") == "empathize":
        must.append("supportive_tone")
    if expected.get("stance") == "reserve":
        must.append("defer_or_verify")

    return {
        "primary_intent_hint": primary,
        "operations_hint": list(dict.fromkeys(operations)),
        "information_state_hint": {
            "missing_required_information": missing,
            "contains_unverified_claims": unverified,
            "requires_current_information": False,
            "multiple_intents": multiple,
        },
        "constraints_hint": {
            "must": must,
            "must_not": [],
            "response_length": "unspecified",
        },
        "risk_hint": {
            "level": risk_level,
            "flags": ["unverified_claim"] if unverified else [],
        },
    }


def _compact(sample: dict[str, Any], category: str, rank: int | None, field_counts: Counter[str], critical_misses: dict[str, int]) -> dict[str, Any]:
    expected = sample["expected"]
    return {
        "id": f"v10-tc-bridge-{category}-{sample['id']}",
        "source_sample_id": sample["id"],
        "selection_bucket": "primary_review" if rank is not None else "reserve_review",
        "priority_rank": rank,
        "bridge_category": category,
        "bridge_score": _category_score(sample, category, field_counts, critical_misses),
        "input": sample.get("input", ""),
        "language": sample.get("language", "unknown"),
        "source_lane": sample.get("lane", ""),
        "source_kind": sample.get("source_kind", ""),
        "source_group_id": sample.get("group_id", ""),
        "thought_color_expected": {
            "base_label": expected.get("base_label"),
            "base_id": expected.get("base_id"),
            "stance": expected.get("stance"),
            "operation": expected.get("operation"),
            "intensity": expected.get("intensity"),
        },
        "semantic_packet_bridge_hint": _semantic_packet_hint(sample, category),
        "judgment_note": sample.get("generation_note", ""),
        "judgment_questions": sample.get("judgment_questions", []),
        "near_miss": sample.get("near_miss"),
        "collision_policy": sample.get("collision_policy"),
        "v10_use_note": CATEGORY_NOTES[category],
        "rewrite_instruction": "Rewrite into a short self-contained mainline semantic-packet review sample; do not copy this row directly into training.",
        "training_status": "not_training_data",
        "allowed_use": "mainline_bridge_review_only",
        "human_review_required": True,
    }


def build_selection() -> dict[str, Any]:
    source = _load(SOURCE)
    source_report = _load(SOURCE_REPORT)
    measurement = _load(V9_MEASUREMENT)
    samples = source["samples"]
    field_counts = _v9_field_counts(measurement)
    critical_misses = _critical_miss_counts(measurement)

    if source["policy"]["mainline_training_allowed"] is not False:
        raise ValueError("Thought Color source must not be mainline training data")
    if source["policy"]["sealed_fixtures_used"] is not False:
        raise ValueError("Thought Color source must not use sealed fixtures")

    candidates_by_category: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for sample in samples:
        if sample.get("adoption_scope") != "thought_color_experiment_only":
            continue
        if sample.get("human_review_required") is not False:
            continue
        for category in _candidate_categories(sample):
            score = _category_score(sample, category, field_counts, critical_misses)
            candidates_by_category[category].append((score, sample))

    primary: list[dict[str, Any]] = []
    selected_source_ids: set[str] = set()
    selected_inputs: set[str] = set()
    category_deficits: dict[str, int] = {}
    for category, quota in PRIMARY_QUOTAS.items():
        ordered = sorted(
            candidates_by_category[category],
            key=lambda item: (-item[0], str(item[1].get("lane", "")), str(item[1].get("id", ""))),
        )
        selected_for_category = []
        lane_counts: Counter[str] = Counter()
        group_counts: Counter[str] = Counter()
        base_counts: Counter[str] = Counter()
        lane_cap = 8 if category == "information_state_bridge" else 6
        group_cap = 4
        base_cap = max(4, quota // 2)

        def can_take(sample: dict[str, Any], *, relaxed: bool = False) -> bool:
            normalized_input = " ".join(str(sample.get("input", "")).split()).lower()
            if sample["id"] in selected_source_ids or normalized_input in selected_inputs:
                return False
            if relaxed:
                return True
            expected = sample["expected"]
            return (
                lane_counts[str(sample.get("lane", ""))] < lane_cap
                and group_counts[str(sample.get("group_id", ""))] < group_cap
                and base_counts[str(expected.get("base_label", ""))] < base_cap
            )

        for _score, sample in ordered:
            if not can_take(sample):
                continue
            normalized_input = " ".join(str(sample.get("input", "")).split()).lower()
            selected_for_category.append(sample)
            selected_source_ids.add(sample["id"])
            selected_inputs.add(normalized_input)
            lane_counts[str(sample.get("lane", ""))] += 1
            group_counts[str(sample.get("group_id", ""))] += 1
            base_counts[str(sample["expected"].get("base_label", ""))] += 1
            if len(selected_for_category) >= quota:
                break
        if len(selected_for_category) < quota:
            for _score, sample in ordered:
                if not can_take(sample, relaxed=True):
                    continue
                normalized_input = " ".join(str(sample.get("input", "")).split()).lower()
                selected_for_category.append(sample)
                selected_source_ids.add(sample["id"])
                selected_inputs.add(normalized_input)
                if len(selected_for_category) >= quota:
                    break
        category_deficits[category] = max(0, quota - len(selected_for_category))
        primary.extend(
            _compact(sample, category, None, field_counts, critical_misses)
            for sample in selected_for_category
        )

    primary.sort(key=lambda row: (-row["bridge_score"], row["bridge_category"], row["source_sample_id"]))
    for index, row in enumerate(primary, start=1):
        row["priority_rank"] = index
        row["selection_bucket"] = "primary_review"

    reserve: list[dict[str, Any]] = []
    reserve_seen: set[str] = set()
    for category, scored in candidates_by_category.items():
        for _score, sample in scored:
            if sample["id"] in selected_source_ids or sample["id"] in reserve_seen:
                continue
            reserve.append(_compact(sample, category, None, field_counts, critical_misses))
            reserve_seen.add(sample["id"])
    reserve.sort(key=lambda row: (-row["bridge_score"], row["bridge_category"], row["source_sample_id"]))

    summary = {
        "source_sample_count": len(samples),
        "source_training_allowed_count": sum(1 for sample in samples if sample.get("training_allowed") is True),
        "primary_review_count": len(primary),
        "reserve_review_count": len(reserve),
        "primary_category_counts": dict(sorted(Counter(row["bridge_category"] for row in primary).items())),
        "reserve_category_counts": dict(sorted(Counter(row["bridge_category"] for row in reserve).items())),
        "category_deficits": {key: value for key, value in sorted(category_deficits.items()) if value},
        "v9_error_field_counts": dict(sorted(field_counts.items())),
        "v9_critical_miss_counts": dict(sorted(critical_misses.items())),
        "source_lane_counts": source_report["adopted_summary"]["lane_counts"],
        "source_base_counts": source_report["adopted_summary"]["base_counts"],
    }

    return {
        "schema_version": "v10-thought-color-bridge-candidate-selection.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "thought_color_bridge_candidates_selected_for_v10_review",
        "sources": {
            "thought_color_adopted_full": str(SOURCE.relative_to(ROOT)),
            "thought_color_adoption_report": str(SOURCE_REPORT.relative_to(ROOT)),
            "v9_sealed_measurement_report": str(V9_MEASUREMENT.relative_to(ROOT)),
        },
        "policy": POLICY,
        "selection_rules": {
            "primary_quotas": PRIMARY_QUOTAS,
            "unique_primary_inputs": True,
            "use_thought_color_as_boundary_judgment_only": True,
            "mainline_expected_packets_are_hints_not_labels": True,
            "human_rewrite_required": True,
        },
        "summary": summary,
        "primary_review": primary,
        "reserve_review": reserve,
    }


def write_worksheet(selection: dict[str, Any]) -> None:
    lines = [
        "# V10 Thought Color Bridge Review Worksheet v1",
        "",
        "Thought Color adopted samples are experiment-only. These rows are bridge candidates for human review and rewrite, not mainline training data.",
        "",
        "## Summary",
        "",
    ]
    for key, value in selection["summary"].items():
        lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Primary Review",
        "",
        "| rank | id | category | score | source lane | thought color | packet hint | note |",
        "|---:|---|---|---:|---|---|---|---|",
    ])
    for row in selection["primary_review"]:
        tc = row["thought_color_expected"]
        hint = row["semantic_packet_bridge_hint"]
        note = row["v10_use_note"].replace("|", "&#124;")
        lines.append(
            f"| {row['priority_rank']} | {row['source_sample_id']} | {row['bridge_category']} | {row['bridge_score']} | "
            f"{row['source_lane']} | {tc['base_label']} / {tc['stance']} / {tc['operation']} / {tc['intensity']} | "
            f"{hint['primary_intent_hint']}:{','.join(hint['operations_hint'])}:{hint['risk_hint']['level']} | {note} |"
        )

    lines.extend([
        "",
        "## Primary Inputs For Rewrite",
        "",
        "Use these only as short source prompts for rewriting. Do not copy directly into training fixtures.",
        "",
    ])
    for row in selection["primary_review"]:
        input_text = row["input"].replace("\n", " ").replace("|", "&#124;")
        near = row.get("near_miss") or {}
        near_text = near.get("why_wrong", "") if isinstance(near, dict) else ""
        lines.extend([
            f"### {row['priority_rank']}. {row['source_sample_id']} ({row['bridge_category']})",
            "",
            f"- input: {input_text}",
            f"- bridge_hint: `{row['semantic_packet_bridge_hint']['primary_intent_hint']}` / `{row['semantic_packet_bridge_hint']['operations_hint']}` / risk `{row['semantic_packet_bridge_hint']['risk_hint']['level']}`",
            f"- judgment_note: {row['judgment_note']}",
            f"- near_miss_note: {near_text}",
            f"- rewrite_instruction: {row['rewrite_instruction']}",
            "",
        ])

    lines.extend([
        "## Reserve Review",
        "",
        "| id | category | score | source lane | packet hint |",
        "|---|---|---:|---|---|",
    ])
    for row in selection["reserve_review"][:60]:
        hint = row["semantic_packet_bridge_hint"]
        lines.append(
            f"| {row['source_sample_id']} | {row['bridge_category']} | {row['bridge_score']} | {row['source_lane']} | "
            f"{hint['primary_intent_hint']}:{','.join(hint['operations_hint'])}:{hint['risk_hint']['level']} |"
        )
    if len(selection["reserve_review"]) > 60:
        lines.append(f"| ... | ... | ... | ... | {len(selection['reserve_review']) - 60} more reserve rows in JSON |")

    lines.extend([
        "",
        "## Contract",
        "",
        "- training_status: not_training_data",
        "- allowed_use: mainline_bridge_review_only",
        "- source_mainline_training_allowed: false",
        "- human_review_required_before_fixture_adoption: true",
        "- sealed_text_used: false",
        "- sealed_labels_used: false",
    ])
    WORKSHEET.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    selection = build_selection()
    _write_json(OUTPUT, selection)
    write_worksheet(selection)
    print(json.dumps({
        "status": selection["status"],
        "output": str(OUTPUT.relative_to(ROOT)),
        "worksheet": str(WORKSHEET.relative_to(ROOT)),
        "summary": selection["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
