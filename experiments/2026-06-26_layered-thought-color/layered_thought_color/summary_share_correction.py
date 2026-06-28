"""Create and evaluate summary-share stance corrections.

This keeps the accepted 281-sample baseline untouched. It evaluates a separate
ablation that adds the 72 weakness samples plus summary-share stance anchors.
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
from .sample_pool import load_sample_pool
from .synthetic_trial import (
    _augmented_hand_group_holdout,
    _delta,
    _load_synthetic_samples,
    _summary_metrics,
)


SOURCE_ABLATION_PATH = DATA_DIR / "thought_color_adopted_plus_weakness_ablation_v0_1.json"
SUMMARY_CORRECTION_PATH = DATA_DIR / "thought_color_summary_share_stance_correction_v0_1.json"
SUMMARY_CORRECTED_ABLATION_PATH = (
    DATA_DIR / "thought_color_adopted_plus_weakness_summary_corrected_ablation_v0_1.json"
)
DISPLAY_SAFE_HAND_POOL_PATH = DATA_DIR / "thought_color_sample_pool_display_safe_v0_1.json"
SUMMARY_CORRECTION_REPORT_PATH = REPORTS_DIR / "thought_color_summary_share_correction_eval_v0_1.json"


DISPLAY_SAFE_REPLACEMENTS = {
    "tc-v01-004": "Review this design gently without being too harsh.",
    "tc-v01-008": "Break these tasks into clear owner-ready sections.",
    "tc-v01-012": "Compare the options while keeping the final decision reserved.",
    "tc-v01-015": "Write three short ideas from the meeting.",
    "tc-v01-016": "Brainstorm a few simple alternatives for reducing latency.",
    "tc-v01-017": "Summarize this log briefly.",
    "tc-v01-019": "Compress the whole discussion into one dense paragraph.",
    "tc-v01-026": "Review this design, but the core requirement is still unclear.",
    "tc-v01-031": "I am overwhelmed, so help me catch my breath and explain it clearly.",
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sample(
    *,
    sample_id: str,
    group_id: str,
    text: str,
    stance: str,
    intensity: str,
    note: str,
) -> Dict[str, Any]:
    return {
        "id": sample_id,
        "lane": "summary_share_stance_correction",
        "group_id": group_id,
        "language": "en",
        "input": text,
        "expected": {
            "base_id": 150,
            "base_label": "summary_compression",
            "stance": stance,
            "operation": "remember",
            "intensity": intensity,
        },
        "collision_policy": "share_base_split_modifier",
        "judgment_questions": [
            "Should this stay in summary_compression?",
            "Is the stance neutral summary or clarify-before-summary?",
        ],
        "generation_note": note,
        "near_miss": {
            "wrong_base_label": "clarification_gate",
            "wrong_modifier": "neutral_or_clarify",
            "why_wrong": "The user still wants a summary; the modifier captures uncertainty.",
        },
        "input_sha256": _sha256(text),
        "adoption_status": "summary_share_correction_review_required",
        "training_allowed": False,
        "human_review_required": True,
        "source_kind": "codex_summary_share_stance_correction",
    }


def build_summary_corrections() -> Dict[str, Any]:
    rows = [
        ("neutral-low", "neutral", "low", [
            "Summarize this log briefly.",
            "Give me the short gist of this thread.",
            "Make a very brief recap of these notes.",
            "Compress this update into the main point only.",
        ]),
        ("neutral-medium", "neutral", "medium", [
            "Summarize the meeting notes in bullets.",
            "Recap the meeting notes clearly by topic.",
            "Condense these notes into a useful summary.",
            "Summarize the decisions and action items.",
        ]),
        ("neutral-high", "neutral", "high", [
            "Compress the whole discussion into one dense paragraph.",
            "Summarize this long transcript thoroughly but compactly.",
            "Extract every major point from this long meeting log.",
            "Create a complete but compressed executive summary.",
        ]),
        ("clarify-medium", "clarify", "medium", [
            "Recap the decisions, not every detail.",
            "Summarize only the decisions and ask if any item is ambiguous.",
            "Recap the confirmed decisions and flag unclear items for follow-up.",
            "Summarize the notes, but ask what to do with unresolved points.",
            "Condense the meeting into decisions only; ask if side topics should be excluded.",
            "Summarize the confirmed points and ask about uncertain decisions.",
            "Recap the outcomes, but check whether draft ideas should be omitted.",
            "Summarize what was decided and ask which unclear items need context.",
        ]),
    ]
    samples = []
    count = 1
    for suffix, stance, intensity, texts in rows:
        for text in texts:
            samples.append(
                _sample(
                    sample_id=f"tc-correct-summary-share-stance-{count:02d}",
                    group_id=f"correct-summary-share-{suffix}",
                    text=text,
                    stance=stance,
                    intensity=intensity,
                    note="Corrects summary_share neutral/clarify stance separation.",
                )
            )
            count += 1
    return {
        "schema_version": "thought-color-summary-share-stance-correction.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "ablation_only": True,
            "mix_with_adopted_set_by_default": False,
            "human_review_required_before_training": True,
        },
        "target": "summary_share_variants",
        "sample_count": len(samples),
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "lane_counts": dict(sorted(Counter(s["lane"] for s in samples).items())),
            "stance_counts": dict(
                sorted(Counter(s["expected"]["stance"] for s in samples).items())
            ),
            "intensity_counts": dict(
                sorted(Counter(s["expected"]["intensity"] for s in samples).items())
            ),
            "training_allowed_count": 0,
            "human_review_required_count": len(samples),
        },
    }


def build_display_safe_hand_pool(
    *,
    output_path: Path = DISPLAY_SAFE_HAND_POOL_PATH,
) -> Dict[str, Any]:
    pool_path = DATA_DIR / "thought_color_sample_pool_v0_1.json"
    payload = json.loads(pool_path.read_text(encoding="utf-8"))
    copied = copy.deepcopy(payload)
    replaced = []
    for case in copied["cases"]:
        case_id = case["id"]
        if case_id not in DISPLAY_SAFE_REPLACEMENTS:
            continue
        case["input"] = DISPLAY_SAFE_REPLACEMENTS[case_id]
        replaced.append(case_id)
    output_path.write_text(
        json.dumps(copied, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(pool_path),
        "output": str(output_path),
        "replaced_case_ids": replaced,
        "note": "Shadow pool for evaluation only; original sample pool is unchanged.",
    }

def _merge(
    source: Mapping[str, Any],
    correction: Mapping[str, Any],
) -> Dict[str, Any]:
    samples = list(source["samples"]) + list(correction["samples"])
    ids = [sample["id"] for sample in samples]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sample ids in summary-share corrected ablation")
    return {
        "schema_version": "thought-color-summary-share-corrected-ablation.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "ablation_only": True,
            "mix_with_adopted_set_by_default": False,
            "source_ablation_remains": str(SOURCE_ABLATION_PATH),
        },
        "sources": {
            "source_ablation": str(SOURCE_ABLATION_PATH),
            "summary_correction": str(SUMMARY_CORRECTION_PATH),
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
        },
    }


def _evaluate_pair(
    *,
    hand_sample_path: Path,
    before_samples,
    after_samples,
) -> Dict[str, Any]:
    hand_pool = load_sample_pool(hand_sample_path)
    before = _augmented_hand_group_holdout(hand_pool.cases, before_samples)
    after = _augmented_hand_group_holdout(hand_pool.cases, after_samples)
    return {
        "hand_sample_path": str(hand_sample_path),
        "before": _summary_metrics(before),
        "after": _summary_metrics(after),
        "delta": _delta(after, before),
        "summary_share_before": before["by_group"]["summary_share_variants"],
        "summary_share_after": after["by_group"]["summary_share_variants"],
        "summary_share_delta": _delta(
            after["by_group"]["summary_share_variants"],
            before["by_group"]["summary_share_variants"],
        ),
        "regressed_groups": {
            group_id: _delta(after["by_group"][group_id], metrics)
            for group_id, metrics in before["by_group"].items()
            if any(
                value < 0
                for value in _delta(after["by_group"][group_id], metrics).values()
            )
        },
    }


def build_summary_share_correction_eval(
    *,
    source_path: Path = SOURCE_ABLATION_PATH,
    correction_path: Path = SUMMARY_CORRECTION_PATH,
    corrected_path: Path = SUMMARY_CORRECTED_ABLATION_PATH,
    display_safe_hand_path: Path = DISPLAY_SAFE_HAND_POOL_PATH,
    report_path: Path = SUMMARY_CORRECTION_REPORT_PATH,
) -> Dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    correction = build_summary_corrections()
    correction_path.write_text(
        json.dumps(correction, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    corrected = _merge(source, correction)
    corrected_path.write_text(
        json.dumps(corrected, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    shadow_meta = build_display_safe_hand_pool(output_path=display_safe_hand_path)

    before_samples = _load_synthetic_samples(source_path)
    after_samples = _load_synthetic_samples(corrected_path)
    original_eval = _evaluate_pair(
        hand_sample_path=DATA_DIR / "thought_color_sample_pool_v0_1.json",
        before_samples=before_samples,
        after_samples=after_samples,
    )
    display_safe_eval = _evaluate_pair(
        hand_sample_path=display_safe_hand_path,
        before_samples=before_samples,
        after_samples=after_samples,
    )
    report = {
        "schema_version": "thought-color-summary-share-correction-eval.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "ablation_only": True,
            "adopted_baseline_unchanged": True,
            "mix_with_adopted_set_by_default": False,
        },
        "paths": {
            "source_ablation": str(source_path),
            "summary_correction": str(correction_path),
            "corrected_ablation": str(corrected_path),
            "display_safe_hand_pool": str(display_safe_hand_path),
        },
        "correction_summary": correction["summary"],
        "display_safe_hand_pool": shadow_meta,
        "original_hand_eval": original_eval,
        "display_safe_hand_eval": display_safe_eval,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def _print_summary(report: Mapping[str, Any]) -> None:
    summary = {
        "paths": report["paths"],
        "correction_summary": report["correction_summary"],
        "original_summary_share_delta": report["original_hand_eval"][
            "summary_share_delta"
        ],
        "original_overall_delta": report["original_hand_eval"]["delta"],
        "display_safe_summary_share_delta": report["display_safe_hand_eval"][
            "summary_share_delta"
        ],
        "display_safe_overall_delta": report["display_safe_hand_eval"]["delta"],
        "original_regressed_groups": report["original_hand_eval"]["regressed_groups"],
        "display_safe_regressed_groups": report["display_safe_hand_eval"][
            "regressed_groups"
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-path", type=Path, default=SOURCE_ABLATION_PATH)
    args = parser.parse_args(argv)
    report = build_summary_share_correction_eval(source_path=args.source_path)
    _print_summary(report)


if __name__ == "__main__":
    main()

