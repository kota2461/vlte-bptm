"""Build and evaluate the isolated 72-sample weakness set."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .paths import DATA_DIR, REPORTS_DIR
from .sample_eval import PrototypeThoughtColorModel, _group_holdout, evaluate_samples
from .sample_pool import ThoughtColorSamplePool, load_sample_pool
from .synthetic_trial import (
    _augmented_hand_group_holdout,
    _base_catalog,
    _by_group_eval,
    _delta,
    _load_synthetic_samples,
    _summary_metrics,
)


ADOPTED_PATH = DATA_DIR / "thought_color_adopted_corrected_v0_1.json"
WEAKNESS_PLAN_PATH = DATA_DIR / "thought_color_weakness_isolated_plan_v0_1.json"
WEAKNESS_SAMPLES_PATH = DATA_DIR / "thought_color_weakness_isolated_samples_v0_1.json"
ADOPTED_PLUS_WEAKNESS_PATH = DATA_DIR / "thought_color_adopted_plus_weakness_ablation_v0_1.json"
WEAKNESS_EVAL_REPORT_PATH = REPORTS_DIR / "thought_color_weakness_isolated_eval_v0_1.json"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sample(
    *,
    sample_id: str,
    lane: str,
    group_id: str,
    text: str,
    base_id: int,
    base_label: str,
    stance: str,
    operation: str,
    intensity: str,
    note: str,
) -> Dict[str, Any]:
    return {
        "id": sample_id,
        "lane": lane,
        "group_id": group_id,
        "language": "en",
        "input": text,
        "expected": {
            "base_id": base_id,
            "base_label": base_label,
            "stance": stance,
            "operation": operation,
            "intensity": intensity,
        },
        "collision_policy": "share_base_split_modifier",
        "judgment_questions": [
            "Does this reinforce the isolated weakness boundary?",
            "Would adding this to the adopted set create a measurable delta?",
        ],
        "generation_note": note,
        "near_miss": {
            "wrong_base_label": "surface_neighbor",
            "wrong_modifier": "surface_neighbor",
            "why_wrong": "This sample is keyed by routing role, not surface wording alone.",
        },
        "input_sha256": _sha256(text),
        "adoption_status": "weakness_isolated_review_required",
        "training_allowed": False,
        "human_review_required": True,
        "source_kind": "codex_weakness_isolated_contrast",
    }


def _rows(
    *,
    prefix: str,
    lane: str,
    specs: Sequence[tuple[int, str, str, str, str, str, Sequence[str]]],
) -> list[Dict[str, Any]]:
    samples = []
    count = 1
    for base_id, base_label, stance, operation, intensity, group_suffix, texts in specs:
        for text in texts:
            samples.append(
                _sample(
                    sample_id=f"tc-weak-{prefix}-{count:02d}",
                    lane=lane,
                    group_id=f"weak-{prefix}-{group_suffix}",
                    text=text,
                    base_id=base_id,
                    base_label=base_label,
                    stance=stance,
                    operation=operation,
                    intensity=intensity,
                    note=f"Isolated weakness sample for {prefix}.",
                )
            )
            count += 1
    return samples


def _empathy_samples() -> list[Dict[str, Any]]:
    return _rows(
        prefix="empathy",
        lane="empathy_across_bases_isolated",
        specs=[
            (170, "supportive_processing", "empathize", "route", "medium", "support-route", [
                "I'm overwhelmed; help me pick one practical next step.",
                "I'm stuck and frustrated; guide me to the first action.",
                "This is getting to me; help me choose what to try next.",
                "I feel blocked; steady me and route me to a manageable next move.",
            ]),
            (150, "summary_compression", "empathize", "remember", "medium", "summary-empathize", [
                "This feedback hurt; summarize only the useful parts gently.",
                "The review was rough; condense the lessons in a kind tone.",
                "I'm discouraged by these notes; preserve the actionable points gently.",
                "This critique stings; recap what matters without amplifying the tone.",
            ]),
            (140, "verification_review", "challenge", "verify", "medium", "verify-kind-challenge", [
                "I may be wrong; challenge my plan kindly.",
                "Please test this idea firmly but without being harsh.",
                "Push back on weak assumptions in this plan with a respectful tone.",
                "Check my reasoning and challenge the risky parts carefully.",
            ]),
            (170, "supportive_processing", "empathize", "reason", "medium", "support-reason", [
                "I'm discouraged; explain what happened without making it harsher.",
                "Help me understand why this failed while keeping me grounded.",
                "I'm upset about the result; explain the cause in a calm way.",
                "This went badly; help me reason through it without piling on.",
            ]),
            (140, "verification_review", "challenge", "verify", "high", "verify-hard-risk", [
                "Do not reassure me; identify the serious risks in this plan.",
                "Skip comfort and point out the hard failure modes.",
                "Be direct: what could make this plan fail badly?",
                "Challenge this proposal hard and flag the highest-risk assumptions.",
            ]),
        ],
    )


def _summary_samples() -> list[Dict[str, Any]]:
    return _rows(
        prefix="summary",
        lane="summary_share_variants_isolated",
        specs=[
            (150, "summary_compression", "neutral", "remember", "low", "neutral-low", [
                "Give me the gist of this log.",
                "Summarize this briefly.",
                "Keep only the headline points.",
                "Compress this note into the main idea.",
            ]),
            (150, "summary_compression", "neutral", "remember", "medium", "neutral-medium", [
                "Summarize the meeting notes in clear bullets.",
                "Recap the decisions and open questions.",
                "Condense this discussion into a useful summary.",
                "Turn these notes into a concise recap.",
            ]),
            (150, "summary_compression", "neutral", "remember", "high", "neutral-high", [
                "Compress this long transcript into one dense page.",
                "Summarize the entire report thoroughly but compactly.",
                "Extract every major decision and risk from this long thread.",
                "Turn this large meeting log into a complete executive summary.",
            ]),
            (150, "summary_compression", "clarify", "remember", "medium", "clarify-medium", [
                "Recap the decisions, and ask if any ambiguous item needs more context.",
                "Summarize the notes but flag any unclear decision for follow-up.",
                "Condense this meeting and ask what to do with unresolved points.",
                "Summarize only the confirmed points and ask about the uncertain ones.",
            ]),
        ],
    )


def _generate_samples() -> list[Dict[str, Any]]:
    return _rows(
        prefix="generate",
        lane="generate_across_bases_isolated",
        specs=[
            (130, "artifact_generation", "neutral", "generate", "medium", "artifact-medium", [
                "Write a short onboarding email for new contributors.",
                "Draft a welcome note for first-time maintainers.",
                "Create a brief setup message for new project members.",
            ]),
            (160, "exploration_tradeoff", "explore", "generate", "medium", "explore-generate", [
                "Brainstorm three ways to reduce API latency.",
                "Generate several options for making search faster.",
                "List possible approaches for improving upload performance.",
            ]),
            (130, "artifact_generation", "neutral", "generate", "low", "artifact-low", [
                "Write three short agenda bullets.",
                "Create a tiny checklist for the standup.",
                "Draft a one-sentence reminder for the release.",
            ]),
            (160, "exploration_tradeoff", "explore", "generate", "medium", "explore-alternatives", [
                "Generate alternatives for simplifying the onboarding flow.",
                "Brainstorm possible ways to reduce support tickets.",
                "List a few directions for redesigning the settings page.",
            ]),
        ],
    )


def _verify_samples() -> list[Dict[str, Any]]:
    return _rows(
        prefix="verify",
        lane="verify_stance_variants_isolated",
        specs=[
            (140, "verification_review", "neutral", "verify", "medium", "neutral", [
                "Review this migration plan for obvious issues.",
                "Check this rollout plan for missing steps.",
                "Verify this deployment checklist for basic mistakes.",
            ]),
            (140, "verification_review", "challenge", "verify", "high", "challenge-high", [
                "Review this migration plan and push back hard on unsafe assumptions.",
                "Challenge the risky assumptions in this rollout plan.",
                "Audit this launch plan aggressively for failure modes.",
            ]),
            (140, "verification_review", "clarify", "verify", "hold", "clarify-hold", [
                "Review this migration plan, but ask first if the database is unknown.",
                "Check this architecture only after asking for the target database.",
                "Hold the review until you know the traffic and storage assumptions.",
            ]),
            (140, "verification_review", "empathize", "verify", "medium", "empathize", [
                "I'm worried I missed something; review this design gently.",
                "This plan makes me nervous; check it carefully but kindly.",
                "I'm anxious about this release; review the risk without piling on.",
            ]),
        ],
    )


def _explore_samples() -> list[Dict[str, Any]]:
    return _rows(
        prefix="explore",
        lane="explore_operation_variants_isolated",
        specs=[
            (160, "exploration_tradeoff", "explore", "compare", "medium", "compare", [
                "Compare SQLite and Postgres for a personal notes app.",
                "Compare local files and a database for a small writing tool.",
                "Compare using a hosted service versus self-hosting for this app.",
            ]),
            (160, "exploration_tradeoff", "explore", "generate", "medium", "generate", [
                "Brainstorm five storage approaches for a personal notes app.",
                "Generate several product directions for a small notes tool.",
                "List possible architectures for an offline-first notes app.",
            ]),
            (160, "exploration_tradeoff", "explore", "reason", "medium", "reason", [
                "Reason through the tradeoffs before recommending a storage option.",
                "Think through the pros and cons before choosing a stack.",
                "Walk through the tradeoffs before deciding how to store notes.",
            ]),
            (160, "exploration_tradeoff", "reserve", "compare", "hold", "reserve-hold", [
                "Keep both options open and compare them without deciding yet.",
                "Compare these choices, but hold the final recommendation.",
                "Explore the options while reserving judgment until constraints are clearer.",
            ]),
        ],
    )


def build_weakness_samples(plan: Mapping[str, Any]) -> Dict[str, Any]:
    samples = (
        _empathy_samples()
        + _summary_samples()
        + _generate_samples()
        + _verify_samples()
        + _explore_samples()
    )
    return {
        "schema_version": "thought-color-weakness-isolated-samples.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": plan["policy"],
        "targets": plan["targets"],
        "sample_count": len(samples),
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "lane_counts": dict(sorted(Counter(s["lane"] for s in samples).items())),
            "base_counts": dict(
                sorted(Counter(s["expected"]["base_label"] for s in samples).items())
            ),
            "language_counts": dict(sorted(Counter(s["language"] for s in samples).items())),
            "training_allowed_count": sum(
                1 for sample in samples if sample.get("training_allowed")
            ),
            "human_review_required_count": sum(
                1 for sample in samples if sample.get("human_review_required")
            ),
        },
    }


def _pool_for(path: Path, samples) -> ThoughtColorSamplePool:
    return ThoughtColorSamplePool(
        path=path,
        cases=tuple(samples),
        base_catalog=_base_catalog(samples),
    )


def _merge_payloads(adopted: Mapping[str, Any], weakness: Mapping[str, Any]) -> Dict[str, Any]:
    samples = list(adopted["samples"]) + list(weakness["samples"])
    ids = [sample["id"] for sample in samples]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sample ids in adopted+weakness ablation")
    return {
        "schema_version": "thought-color-adopted-plus-weakness-ablation.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "ablation_only": True,
            "adopted_baseline_remains": str(ADOPTED_PATH),
            "weakness_samples_are_isolated": True,
            "mix_with_adopted_set_by_default": False,
        },
        "sources": {
            "adopted_path": str(ADOPTED_PATH),
            "weakness_path": str(WEAKNESS_SAMPLES_PATH),
        },
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "adopted_count": len(adopted["samples"]),
            "weakness_count": len(weakness["samples"]),
            "lane_counts": dict(sorted(Counter(s["lane"] for s in samples).items())),
            "base_counts": dict(
                sorted(Counter(s["expected"]["base_label"] for s in samples).items())
            ),
        },
    }


def _group_deltas(current: Mapping[str, Any], baseline: Mapping[str, Any]) -> Dict[str, Any]:
    deltas = {}
    for group_id, metrics in current["by_group"].items():
        if group_id not in baseline["by_group"]:
            continue
        deltas[group_id] = _delta(metrics, baseline["by_group"][group_id])
    return deltas


def _changed_groups(group_deltas: Mapping[str, Mapping[str, float]]) -> Dict[str, Any]:
    improved = {}
    regressed = {}
    for group_id, deltas in group_deltas.items():
        if any(value > 0 for value in deltas.values()):
            improved[group_id] = deltas
        if any(value < 0 for value in deltas.values()):
            regressed[group_id] = deltas
    return {"improved": improved, "regressed": regressed}


def build_weakness_eval(
    *,
    plan_path: Path = WEAKNESS_PLAN_PATH,
    adopted_path: Path = ADOPTED_PATH,
    weakness_path: Path = WEAKNESS_SAMPLES_PATH,
    ablation_path: Path = ADOPTED_PLUS_WEAKNESS_PATH,
    report_path: Path = WEAKNESS_EVAL_REPORT_PATH,
) -> Dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    adopted_payload = json.loads(adopted_path.read_text(encoding="utf-8"))
    weakness_payload = build_weakness_samples(plan)
    weakness_path.write_text(
        json.dumps(weakness_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    ablation_payload = _merge_payloads(adopted_payload, weakness_payload)
    ablation_path.write_text(
        json.dumps(ablation_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    hand_pool = load_sample_pool()
    adopted = _load_synthetic_samples(adopted_path)
    weakness = _load_synthetic_samples(weakness_path)
    adopted_plus_weakness = tuple(adopted) + tuple(weakness)

    adopted_baseline = _augmented_hand_group_holdout(hand_pool.cases, adopted)
    weakness_only_to_hand = _augmented_hand_group_holdout(hand_pool.cases, weakness)
    adopted_plus = _augmented_hand_group_holdout(
        hand_pool.cases,
        adopted_plus_weakness,
    )
    weakness_only_holdout = _group_holdout(_pool_for(weakness_path, weakness))

    adopted_model = PrototypeThoughtColorModel.train(adopted)
    weakness_model = PrototypeThoughtColorModel.train(weakness)
    adopted_plus_model = PrototypeThoughtColorModel.train(adopted_plus_weakness)

    adopted_to_hand = evaluate_samples(hand_pool.cases, adopted_model)
    weakness_to_hand = evaluate_samples(hand_pool.cases, weakness_model)
    adopted_plus_to_hand = evaluate_samples(hand_pool.cases, adopted_plus_model)

    target_groups = [target["group_id"] for target in plan["targets"]]
    target_deltas = {
        group_id: _delta(
            adopted_plus["by_group"][group_id],
            adopted_baseline["by_group"][group_id],
        )
        for group_id in target_groups
    }
    group_deltas = _group_deltas(adopted_plus, adopted_baseline)
    changed_groups = _changed_groups(group_deltas)

    report = {
        "schema_version": "thought-color-weakness-isolated-eval.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "weakness_samples_are_isolated": True,
            "adopted_baseline_unchanged": True,
            "ablation_only": True,
            "mix_with_adopted_set_by_default": False,
        },
        "paths": {
            "plan": str(plan_path),
            "adopted_baseline": str(adopted_path),
            "weakness_samples": str(weakness_path),
            "adopted_plus_weakness_ablation": str(ablation_path),
        },
        "inputs": {
            "adopted_count": len(adopted),
            "weakness_count": len(weakness),
            "ablation_count": len(adopted_plus_weakness),
            "hand_sample_count": len(hand_pool.cases),
        },
        "weakness_sample_summary": weakness_payload["summary"],
        "adopted_baseline_group_holdout": _summary_metrics(adopted_baseline),
        "weakness_only_group_holdout": _summary_metrics(weakness_only_holdout),
        "weakness_only_to_hand_group_holdout": _summary_metrics(weakness_only_to_hand),
        "adopted_plus_weakness_group_holdout": _summary_metrics(adopted_plus),
        "delta_adopted_plus_vs_adopted_baseline": _delta(
            adopted_plus,
            adopted_baseline,
        ),
        "target_group_deltas": target_deltas,
        "changed_groups": changed_groups,
        "direct_fit_checks": {
            "adopted_to_hand": _summary_metrics(adopted_to_hand),
            "weakness_to_hand": _summary_metrics(weakness_to_hand),
            "adopted_plus_to_hand": _summary_metrics(adopted_plus_to_hand),
        },
        "by_group": {
            "adopted_baseline": adopted_baseline["by_group"],
            "weakness_only_to_hand": weakness_only_to_hand["by_group"],
            "adopted_plus_weakness": adopted_plus["by_group"],
            "delta": group_deltas,
        },
        "weakness_by_group": _by_group_eval(weakness, weakness_model),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def _print_summary(report: Mapping[str, Any]) -> None:
    summary = {
        "paths": report["paths"],
        "inputs": report["inputs"],
        "weakness_sample_summary": report["weakness_sample_summary"],
        "adopted_baseline_group_holdout": report["adopted_baseline_group_holdout"],
        "weakness_only_group_holdout": report["weakness_only_group_holdout"],
        "adopted_plus_weakness_group_holdout": report[
            "adopted_plus_weakness_group_holdout"
        ],
        "delta_adopted_plus_vs_adopted_baseline": report[
            "delta_adopted_plus_vs_adopted_baseline"
        ],
        "target_group_deltas": report["target_group_deltas"],
        "regressed_groups": report["changed_groups"]["regressed"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-path", type=Path, default=WEAKNESS_PLAN_PATH)
    parser.add_argument("--adopted-path", type=Path, default=ADOPTED_PATH)
    args = parser.parse_args(argv)
    report = build_weakness_eval(
        plan_path=args.plan_path,
        adopted_path=args.adopted_path,
    )
    _print_summary(report)


if __name__ == "__main__":
    main()
