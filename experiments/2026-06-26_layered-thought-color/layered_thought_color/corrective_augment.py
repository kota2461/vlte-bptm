"""Add corrective samples for two regressions found after targeted augmentation."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .paths import DATA_DIR, REPORTS_DIR
from .synthetic_trial import build_synthetic_trial_report


SOURCE_AUGMENTED_PATH = DATA_DIR / "thought_color_augmented_candidates_v0_1.json"
CORRECTION_SAMPLES_PATH = DATA_DIR / "thought_color_correction_samples_v0_1.json"
CORRECTED_CANDIDATES_PATH = DATA_DIR / "thought_color_corrected_candidates_v0_1.json"
CORRECTED_TRIAL_REPORT_PATH = REPORTS_DIR / "thought_color_corrected_trial_v0_1.json"
CORRECTED_SUMMARY_PATH = REPORTS_DIR / "thought_color_corrected_summary_v0_1.json"


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
    operation: str,
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
            "stance": "neutral",
            "operation": operation,
            "intensity": "medium",
        },
        "collision_policy": "split_base_share_modifier",
        "judgment_questions": [
            "Does the base reflect the user's actual requested action?",
            "Should this remain neutral medium rather than inherit empathy or hold?",
        ],
        "generation_note": note,
        "near_miss": {
            "wrong_base_label": "surface_neighbor",
            "wrong_modifier": "empathize_or_hold",
            "why_wrong": (
                "The wording is ordinary task routing, not emotional support or "
                "missing-context hold."
            ),
        },
        "input_sha256": _sha256(text),
        "adoption_status": "corrective_review_required",
        "training_allowed": False,
        "human_review_required": True,
        "source_kind": "codex_corrective_contrast",
    }


def _code_request_split_samples() -> list[Dict[str, Any]]:
    rows = [
        (140, "verification_review", "verify", [
            "Check this function for off-by-one bugs.",
            "Review this code and point out any unsafe edge cases.",
            "Inspect this parser for logic errors.",
            "Find bugs in this helper without rewriting it.",
            "Verify whether this code handles empty input correctly.",
            "Audit this snippet for mistakes.",
        ]),
        (110, "mechanism_explanation", "reason", [
            "Explain why this loop becomes slow on large inputs.",
            "Tell me why this function times out.",
            "Explain the cause of this memory spike in the code.",
            "Why does this query get slower after adding more rows?",
            "Explain why this recursion is inefficient.",
            "Describe why this implementation behaves slowly.",
        ]),
        (130, "artifact_generation", "generate", [
            "Rewrite this repeated code as a helper function.",
            "Refactor this snippet into a small reusable utility.",
            "Turn this inline logic into a named helper.",
            "Create a cleaner version of this function.",
            "Convert this code block into a reusable method.",
            "Write a compact helper that replaces this duplicate logic.",
        ]),
    ]
    samples = []
    count = 1
    for base_id, base_label, operation, texts in rows:
        for text in texts:
            samples.append(
                _sample(
                    sample_id=f"tc-correct-code-request-split-{count:02d}",
                    lane="code_request_split_correction",
                    group_id=f"correct-code-request-split-{base_label}",
                    text=text,
                    base_id=base_id,
                    base_label=base_label,
                    operation=operation,
                    note="Corrects code wording split: review vs explain vs rewrite.",
                )
            )
            count += 1
    return samples


def _build_operation_variant_samples() -> list[Dict[str, Any]]:
    rows = [
        ("generate", [
            "Draft a release checklist for a small web app.",
            "Create a launch checklist for a simple dashboard.",
            "Write a deploy checklist for a weekend project.",
            "Make a concise release checklist for a browser tool.",
            "Create a pre-launch checklist for a tiny SaaS app.",
        ]),
        ("verify", [
            "Create a release checklist that is specifically focused on verification gates.",
            "Draft a launch checklist centered on test, review, and rollback checks.",
            "Make a deploy checklist that only tracks validation steps.",
            "Write a release checklist for checking readiness, not for assigning tasks.",
            "Create a checklist of verification gates for shipping a web app.",
        ]),
        ("remember", [
            "Turn recurring deploy notes into a reusable release template.",
            "Convert these repeated launch notes into a saved checklist template.",
            "Preserve these deployment notes as a reusable template.",
            "Organize repeated release notes into a standard template.",
            "Make these recurring deploy reminders into a reusable checklist format.",
        ]),
        ("route", [
            "Break the release work into owner-ready sections.",
            "Split this launch checklist by responsible role.",
            "Route these deploy tasks into frontend, backend, and QA buckets.",
            "Divide the release checklist so each team knows its part.",
            "Organize the web app launch tasks by owner before drafting details.",
        ]),
    ]
    samples = []
    count = 1
    for operation, texts in rows:
        for text in texts:
            samples.append(
                _sample(
                    sample_id=f"tc-correct-build-operation-variants-{count:02d}",
                    lane="build_operation_variants_correction",
                    group_id=f"correct-build-operation-{operation}",
                    text=text,
                    base_id=130,
                    base_label="artifact_generation",
                    operation=operation,
                    note=(
                        "Corrects artifact_generation base with operation split "
                        "inside the same base family."
                    ),
                )
            )
            count += 1
    return samples


def build_correction_samples() -> Dict[str, Any]:
    samples = _code_request_split_samples() + _build_operation_variant_samples()
    return {
        "schema_version": "thought-color-correction-samples.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "synthetic_samples_are_training_data": False,
            "human_review_required_before_training": True,
            "sealed_fixtures_used": False,
        },
        "targets": {
            "code_request_split": 18,
            "build_operation_variants": 20,
        },
        "samples": samples,
    }


def _merge(
    source: Mapping[str, Any],
    correction: Mapping[str, Any],
) -> Dict[str, Any]:
    samples = list(source["samples"]) + list(correction["samples"])
    ids = [sample["id"] for sample in samples]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sample ids in corrected set")
    return {
        "schema_version": "thought-color-corrected-candidates.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "synthetic_samples_are_training_data": False,
            "trial_treats_synthetic_as_provisional_training": True,
            "human_review_required_before_real_training": True,
            "sealed_fixtures_used": False,
        },
        "sources": {
            "source_augmented_path": str(SOURCE_AUGMENTED_PATH),
            "correction_samples_path": str(CORRECTION_SAMPLES_PATH),
        },
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "source_count": len(source["samples"]),
            "correction_count": len(correction["samples"]),
            "lane_counts": dict(sorted(Counter(s["lane"] for s in samples).items())),
            "base_counts": dict(
                sorted(Counter(s["expected"]["base_label"] for s in samples).items())
            ),
            "language_counts": dict(
                sorted(Counter(s["language"] for s in samples).items())
            ),
        },
    }


def build_corrected_assets(
    *,
    source_path: Path = SOURCE_AUGMENTED_PATH,
    correction_path: Path = CORRECTION_SAMPLES_PATH,
    corrected_path: Path = CORRECTED_CANDIDATES_PATH,
    trial_report_path: Path = CORRECTED_TRIAL_REPORT_PATH,
    summary_path: Path = CORRECTED_SUMMARY_PATH,
) -> Dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    correction = build_correction_samples()
    corrected = _merge(source, correction)
    correction_path.write_text(
        json.dumps(correction, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    corrected_path.write_text(
        json.dumps(corrected, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    trial = build_synthetic_trial_report(
        synthetic_path=corrected_path,
        output_path=trial_report_path,
    )
    summary = {
        "schema_version": "thought-color-corrected-summary.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paths": {
            "correction_samples": str(correction_path),
            "corrected_candidates": str(corrected_path),
            "trial_report": str(trial_report_path),
        },
        "corrected_summary": corrected["summary"],
        "correction_targets": correction["targets"],
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
    parser.add_argument("--source-path", type=Path, default=SOURCE_AUGMENTED_PATH)
    args = parser.parse_args(argv)
    summary = build_corrected_assets(source_path=args.source_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
