"""Build a display-safe synthetic set plus targeted gap samples.

The original 175 synthetic candidates are preserved. This module creates a
trial-only augmented set:

* Japanese/display-sensitive rows are regenerated as English-only examples.
* Missing-context, supportive-processing, and intensity anchors are added.
* The result is evaluated as provisional synthetic data, not adopted training.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .paths import DATA_DIR, REPORTS_DIR
from .synthetic_trial import (
    SYNTHETIC_CANDIDATES_PATH,
    build_synthetic_trial_report,
)


DISPLAY_SAFE_PATH = DATA_DIR / "thought_color_synthetic_display_safe_v0_1.json"
TARGETED_GAP_PATH = DATA_DIR / "thought_color_targeted_gap_samples_v0_1.json"
AUGMENTED_CANDIDATES_PATH = DATA_DIR / "thought_color_augmented_candidates_v0_1.json"
AUGMENTED_TRIAL_REPORT_PATH = REPORTS_DIR / "thought_color_augmented_trial_v0_1.json"
AUGMENTED_SUMMARY_PATH = REPORTS_DIR / "thought_color_augmented_summary_v0_1.json"

MOJIBAKE_MARKS = (
    "縺",
    "繧",
    "譁",
    "譌",
    "菴",
    "螟",
    "髢",
    "隕",
    "謇",
    "蜿",
    "荳",
    "豁",
    "�",
    "",
)

BASE_DEFAULT_OPERATION = {
    "direct_answer": "respond",
    "mechanism_explanation": "reason",
    "clarification_gate": "route",
    "artifact_generation": "generate",
    "verification_review": "verify",
    "summary_compression": "remember",
    "exploration_tradeoff": "compare",
    "supportive_processing": "route",
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _has_mojibake(text: str) -> bool:
    return any(mark in text for mark in MOJIBAKE_MARKS)


def _english_replacement(sample: Mapping[str, Any], index: int) -> str:
    expected = sample["expected"]
    base = expected["base_label"]
    stance = expected["stance"]
    operation = expected["operation"]
    intensity = expected["intensity"]
    prefix = {
        "direct_answer": "Answer this directly",
        "mechanism_explanation": "Explain the mechanism",
        "clarification_gate": "Ask what details are missing",
        "artifact_generation": "Draft the requested artifact",
        "verification_review": "Check this carefully",
        "summary_compression": "Summarize the material",
        "exploration_tradeoff": "Compare the options",
        "supportive_processing": "Help me steady this and choose a next step",
    }[base]
    stance_phrase = {
        "neutral": "without adding extra tone",
        "affirm": "and confirm the useful part",
        "negate": "and reject the false premise",
        "explore": "while keeping alternatives open",
        "clarify": "but ask the key missing question first",
        "empathize": "while acknowledging that this is stressful",
        "challenge": "and push back on unsafe assumptions",
        "reserve": "but avoid overclaiming",
    }[stance]
    operation_phrase = {
        "respond": "as a concise response",
        "reason": "by explaining the reason",
        "compare": "by comparing the tradeoffs",
        "verify": "by checking the claim",
        "generate": "by creating a usable draft",
        "remember": "by preserving only the key points",
        "route": "by deciding what information is needed next",
        "reserve": "by holding the answer until the missing part is known",
    }[operation]
    intensity_phrase = {
        "low": "Keep it brief.",
        "medium": "Use normal detail.",
        "high": "Treat it as important and be thorough.",
        "hold": "Pause if the required context is missing.",
    }[intensity]
    return (
        f"{prefix} {stance_phrase}, {operation_phrase}. "
        f"{intensity_phrase} Example {index + 1}."
    )


def _repair_display_safe(payload: Mapping[str, Any]) -> Dict[str, Any]:
    repaired = copy.deepcopy(payload)
    changed = 0
    mojibake_detected = 0
    for index, sample in enumerate(repaired["samples"]):
        text_blob = " ".join(
            str(sample.get(key, "")) for key in ("input", "generation_note")
        )
        is_display_sensitive = sample.get("language") == "ja"
        is_mojibake = _has_mojibake(text_blob)
        mojibake_detected += int(is_mojibake)
        if not (is_display_sensitive or is_mojibake):
            continue
        sample["original_language"] = sample.get("language")
        sample["original_input_sha256"] = sample.get("input_sha256")
        sample["input"] = _english_replacement(sample, index)
        sample["input_sha256"] = _sha256(sample["input"])
        sample["language"] = "en"
        sample["display_safe_repair"] = {
            "kind": "english_regeneration_for_display_stability",
            "reason": "ja_or_mojibake_sensitive_input",
            "original_language": sample["original_language"],
        }
        sample["human_review_required"] = True
        sample["training_allowed"] = False
        changed += 1
    repaired["schema_version"] = "thought-color-synthetic-display-safe.v0.1"
    repaired["created_at"] = datetime.now(timezone.utc).isoformat()
    repaired["display_safe_repair_meta"] = {
        "source_schema_version": payload.get("schema_version"),
        "source_count": len(payload.get("samples", [])),
        "mojibake_detected_count": mojibake_detected,
        "english_regenerated_count": changed,
        "note": (
            "Unicode payload was valid on readback; English regeneration is used "
            "for display-stable provisional testing."
        ),
    }
    return repaired


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
    collision_policy: str,
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
        "collision_policy": collision_policy,
        "judgment_questions": [
            "Does the base family match the user's primary goal?",
            "Do the modifier channels explain the routing decision?",
        ],
        "generation_note": note,
        "near_miss": {
            "wrong_base_label": "nearest_neighbor_by_surface_text",
            "wrong_modifier": "nearest_modifier_by_surface_text",
            "why_wrong": "The target label is chosen by routing role, not surface wording alone.",
        },
        "input_sha256": _sha256(text),
        "adoption_status": "targeted_review_required",
        "training_allowed": False,
        "human_review_required": True,
        "source_kind": "codex_targeted_gap_contrast",
    }


def _missing_context_samples() -> list[Dict[str, Any]]:
    rows = [
        (160, "exploration_tradeoff", "clarify", "compare", "hold", [
            "Which database should I use if you do not know my traffic, budget, or team skills yet?",
            "Compare SQL and NoSQL, but first ask me for the missing workload details.",
            "I want to choose a database; pause until you know the scale and constraints.",
            "Before recommending a database, ask what data shape and latency I need.",
            "Help me pick between two storage options, but hold the answer until requirements are clear.",
        ]),
        (130, "artifact_generation", "clarify", "route", "hold", [
            "I need a migration plan, but the source database is still undecided.",
            "Draft the rollout plan only after asking which database and downtime window we have.",
            "Make a migration checklist, but pause because I have not chosen the target database.",
            "I want an implementation plan; first route me through the missing requirements.",
            "Create the deployment plan after asking for the unknown environment details.",
        ]),
        (140, "verification_review", "clarify", "verify", "hold", [
            "Review this architecture, but ask for the performance target before judging it.",
            "Check this design only after you know the database and traffic assumptions.",
            "Verify the plan, but hold the verdict because the key constraint is missing.",
            "Review the migration proposal and ask what data volume it must handle first.",
            "Audit this checklist, but pause if the compliance requirement is not specified.",
        ]),
        (120, "clarification_gate", "clarify", "route", "medium", [
            "Ask me what information you need before answering my architecture question.",
            "Before you answer, list the missing details you need from me.",
            "Do not solve it yet; ask the clarifying questions that decide the route.",
            "Help me figure out what context I forgot to provide.",
            "Start by asking which constraints matter before giving advice.",
        ]),
    ]
    samples = []
    count = 1
    for base_id, base_label, stance, operation, intensity, texts in rows:
        for text in texts:
            samples.append(
                _sample(
                    sample_id=f"tc-target-missing-context-{count:02d}",
                    lane="missing_context",
                    group_id=f"target-missing-{base_label}-{operation}-{intensity}",
                    text=text,
                    base_id=base_id,
                    base_label=base_label,
                    stance=stance,
                    operation=operation,
                    intensity=intensity,
                    collision_policy="share_base_split_modifier",
                    note="Targeted anchor for missing-context routing.",
                )
            )
            count += 1
    return samples


def _supportive_processing_samples() -> list[Dict[str, Any]]:
    rows = [
        ("route", [
            "I'm frustrated and stuck; help me choose the next practical step.",
            "This is overwhelming, so steady me first and then route me to the next action.",
            "I feel lost; help me decide what to try next without making it bigger.",
            "I'm upset and need a calm next-step plan.",
            "This failed again; help me pick one next move.",
        ]),
        ("reason", [
            "I'm overwhelmed; first acknowledge it, then explain why this keeps happening.",
            "This mistake hurt; help me understand the cause without piling on.",
            "I'm discouraged and need a gentle explanation of what went wrong.",
            "Explain why my approach failed, but keep the tone supportive.",
            "I need to understand the failure while staying calm enough to continue.",
        ]),
        ("remember", [
            "That feedback stung; summarize the useful parts gently.",
            "I feel bad about these notes; condense them kindly into what matters.",
            "Summarize the criticism in a way I can actually process.",
            "This review was harsh; preserve the key lessons without the sting.",
            "Help me remember the actionable points from this painful feedback.",
        ]),
        ("generate", [
            "I'm anxious about replying; draft a calm response I can edit.",
            "Help me write a short message that acknowledges the issue without panic.",
            "I'm stressed; create a simple plan I can follow today.",
            "Draft a gentle apology and next-step note for this situation.",
            "Create a small recovery checklist that feels manageable.",
        ]),
    ]
    samples = []
    count = 1
    for operation, texts in rows:
        for text in texts:
            samples.append(
                _sample(
                    sample_id=f"tc-target-supportive-processing-{count:02d}",
                    lane="supportive_modifier",
                    group_id=f"target-supportive-processing-{operation}",
                    text=text,
                    base_id=170,
                    base_label="supportive_processing",
                    stance="empathize",
                    operation=operation,
                    intensity="medium",
                    collision_policy="share_modifier",
                    note="Targeted anchor for supportive processing as its own base.",
                )
            )
            count += 1
    return samples


def _intensity_samples() -> list[Dict[str, Any]]:
    base_rows = [
        (100, "direct_answer", "respond", "Answer the question"),
        (110, "mechanism_explanation", "reason", "Explain the mechanism"),
        (120, "clarification_gate", "route", "Ask the needed question"),
        (130, "artifact_generation", "generate", "Draft the artifact"),
        (140, "verification_review", "verify", "Check the claim"),
        (150, "summary_compression", "remember", "Summarize the notes"),
        (160, "exploration_tradeoff", "compare", "Compare the options"),
    ]
    intensity_text = {
        "low": "briefly in one or two sentences",
        "medium": "with normal useful detail",
        "high": "thoroughly because the stakes are high",
        "hold": "but pause if required context is missing",
    }
    samples = []
    count = 1
    for base_id, base_label, operation, verb in base_rows:
        for intensity, phrase in intensity_text.items():
            stance = "clarify" if intensity == "hold" and base_label in {
                "clarification_gate",
                "artifact_generation",
                "verification_review",
                "exploration_tradeoff",
            } else "neutral"
            samples.append(
                _sample(
                    sample_id=f"tc-target-intensity-{count:02d}",
                    lane="intensity_anchor",
                    group_id=f"target-intensity-{base_label}",
                    text=f"{verb} {phrase}.",
                    base_id=base_id,
                    base_label=base_label,
                    stance=stance,
                    operation=operation,
                    intensity=intensity,
                    collision_policy="share_base_split_modifier",
                    note="Targeted anchor for intensity separation.",
                )
            )
            count += 1
    return samples


def build_targeted_samples() -> Dict[str, Any]:
    samples = (
        _missing_context_samples()
        + _supportive_processing_samples()
        + _intensity_samples()
    )
    return {
        "schema_version": "thought-color-targeted-gap-samples.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "synthetic_samples_are_training_data": False,
            "human_review_required_before_training": True,
            "sealed_fixtures_used": False,
        },
        "targets": {
            "missing_context": 20,
            "supportive_processing": 20,
            "intensity": 28,
        },
        "samples": samples,
    }


def _merge_payloads(
    display_safe: Mapping[str, Any],
    targeted: Mapping[str, Any],
) -> Dict[str, Any]:
    samples = list(display_safe["samples"]) + list(targeted["samples"])
    ids = [sample["id"] for sample in samples]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sample ids in augmented set")
    return {
        "schema_version": "thought-color-augmented-candidates.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "synthetic_samples_are_training_data": False,
            "trial_treats_synthetic_as_provisional_training": True,
            "human_review_required_before_real_training": True,
            "sealed_fixtures_used": False,
        },
        "sources": {
            "display_safe_path": str(DISPLAY_SAFE_PATH),
            "targeted_gap_path": str(TARGETED_GAP_PATH),
        },
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "display_safe_count": len(display_safe["samples"]),
            "targeted_count": len(targeted["samples"]),
            "lane_counts": dict(sorted(Counter(s["lane"] for s in samples).items())),
            "base_counts": dict(
                sorted(Counter(s["expected"]["base_label"] for s in samples).items())
            ),
            "language_counts": dict(sorted(Counter(s["language"] for s in samples).items())),
        },
    }


def build_augmented_assets(
    *,
    source_path: Path = SYNTHETIC_CANDIDATES_PATH,
    display_safe_path: Path = DISPLAY_SAFE_PATH,
    targeted_path: Path = TARGETED_GAP_PATH,
    augmented_path: Path = AUGMENTED_CANDIDATES_PATH,
    trial_report_path: Path = AUGMENTED_TRIAL_REPORT_PATH,
    summary_path: Path = AUGMENTED_SUMMARY_PATH,
) -> Dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    display_safe = _repair_display_safe(source)
    targeted = build_targeted_samples()
    augmented = _merge_payloads(display_safe, targeted)

    display_safe_path.write_text(
        json.dumps(display_safe, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    targeted_path.write_text(
        json.dumps(targeted, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    augmented_path.write_text(
        json.dumps(augmented, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    trial = build_synthetic_trial_report(
        synthetic_path=augmented_path,
        output_path=trial_report_path,
    )
    summary = {
        "schema_version": "thought-color-augmented-summary.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paths": {
            "display_safe": str(display_safe_path),
            "targeted": str(targeted_path),
            "augmented": str(augmented_path),
            "trial_report": str(trial_report_path),
        },
        "display_safe_repair_meta": display_safe["display_safe_repair_meta"],
        "targeted_counts": targeted["targets"],
        "augmented_summary": augmented["summary"],
        "trial_key_metrics": {
            "baseline_hand_group_holdout": trial["baseline_hand_group_holdout"],
            "synthetic_augmented_hand_group_holdout": trial[
                "synthetic_augmented_hand_group_holdout"
            ],
            "delta_vs_hand_group_holdout": trial["delta_vs_hand_group_holdout"][
                "synthetic_augmented_hand_group_holdout"
            ],
        },
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-path", type=Path, default=SYNTHETIC_CANDIDATES_PATH)
    args = parser.parse_args(argv)
    summary = build_augmented_assets(source_path=args.source_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
