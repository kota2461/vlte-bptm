"""Provisional evaluation using review-required synthetic samples.

This is intentionally a trial: synthetic samples remain review-required and are
not promoted to training data by this module.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .code import ThoughtColorCode
from .paths import DATA_DIR, REPORTS_DIR
from .sample_eval import (
    PrototypeThoughtColorModel,
    _group_holdout,
    evaluate_samples,
)
from .sample_pool import (
    DEFAULT_SAMPLE_POOL_PATH,
    ThoughtColorSample,
    ThoughtColorSamplePool,
    load_sample_pool,
)


SYNTHETIC_CANDIDATES_PATH = DATA_DIR / "thought_color_synthetic_candidates_v0_1.json"
SYNTHETIC_TRIAL_REPORT_PATH = REPORTS_DIR / "thought_color_synthetic_trial_v0_1.json"


def _load_synthetic_samples(path: Path) -> tuple[ThoughtColorSample, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    samples = []
    for raw in payload["samples"]:
        expected = raw["expected"]
        samples.append(
            ThoughtColorSample(
                case_id=raw["id"],
                lane=raw["lane"],
                group_id=raw["group_id"],
                language=raw["language"],
                input_text=raw["input"],
                expected=ThoughtColorCode.from_labels(
                    base_id=expected["base_id"],
                    stance=expected["stance"],
                    operation=expected["operation"],
                    intensity=expected["intensity"],
                ),
                base_label=expected["base_label"],
                collision_policy=raw["collision_policy"],
                judgment_questions=tuple(raw["judgment_questions"]),
            )
        )
    return tuple(samples)


def _base_catalog(samples: Sequence[ThoughtColorSample]) -> Dict[int, str]:
    catalog: Dict[int, str] = {}
    for sample in samples:
        catalog[sample.expected.base_id] = sample.base_label
    return dict(sorted(catalog.items()))


def _summary_metrics(result: Mapping[str, Any]) -> Dict[str, Any]:
    keys = (
        "case_count",
        "group_count",
        "base_accuracy",
        "stance_accuracy",
        "operation_accuracy",
        "intensity_accuracy",
        "full_code_accuracy",
    )
    return {key: result[key] for key in keys if key in result}


def _by_group_eval(
    samples: Sequence[ThoughtColorSample],
    model: PrototypeThoughtColorModel,
) -> Dict[str, Any]:
    groups: Dict[str, list[ThoughtColorSample]] = defaultdict(list)
    for sample in samples:
        groups[sample.group_id].append(sample)
    by_group = {}
    aggregate = Counter()
    for group_id, group_samples in sorted(groups.items()):
        result = evaluate_samples(group_samples, model)
        by_group[group_id] = _summary_metrics(result)
        for key in (
            "base_accuracy",
            "stance_accuracy",
            "operation_accuracy",
            "intensity_accuracy",
            "full_code_accuracy",
        ):
            aggregate[key] += result[key] * result["case_count"]
        aggregate["case_count"] += result["case_count"]
    total = aggregate["case_count"]
    return {
        "case_count": total,
        "group_count": len(groups),
        "base_accuracy": round(aggregate["base_accuracy"] / total, 6),
        "stance_accuracy": round(aggregate["stance_accuracy"] / total, 6),
        "operation_accuracy": round(aggregate["operation_accuracy"] / total, 6),
        "intensity_accuracy": round(aggregate["intensity_accuracy"] / total, 6),
        "full_code_accuracy": round(aggregate["full_code_accuracy"] / total, 6),
        "by_group": by_group,
    }


def _augmented_hand_group_holdout(
    hand_samples: Sequence[ThoughtColorSample],
    synthetic_samples: Sequence[ThoughtColorSample],
) -> Dict[str, Any]:
    group_ids = sorted({sample.group_id for sample in hand_samples})
    by_group = {}
    aggregate = Counter()
    all_errors = []
    for group_id in group_ids:
        train = list(synthetic_samples) + [
            sample for sample in hand_samples if sample.group_id != group_id
        ]
        held = [sample for sample in hand_samples if sample.group_id == group_id]
        model = PrototypeThoughtColorModel.train(train)
        result = evaluate_samples(held, model)
        by_group[group_id] = _summary_metrics(result)
        for key in (
            "base_accuracy",
            "stance_accuracy",
            "operation_accuracy",
            "intensity_accuracy",
            "full_code_accuracy",
        ):
            aggregate[key] += result[key] * result["case_count"]
        aggregate["case_count"] += result["case_count"]
        all_errors.extend(result["errors"])
    total = aggregate["case_count"]
    return {
        "case_count": total,
        "group_count": len(group_ids),
        "base_accuracy": round(aggregate["base_accuracy"] / total, 6),
        "stance_accuracy": round(aggregate["stance_accuracy"] / total, 6),
        "operation_accuracy": round(aggregate["operation_accuracy"] / total, 6),
        "intensity_accuracy": round(aggregate["intensity_accuracy"] / total, 6),
        "full_code_accuracy": round(aggregate["full_code_accuracy"] / total, 6),
        "by_group": by_group,
        "errors": all_errors,
    }

def _pool_for(path: Path, samples: Sequence[ThoughtColorSample]) -> ThoughtColorSamplePool:
    return ThoughtColorSamplePool(
        path=path,
        cases=tuple(samples),
        base_catalog=_base_catalog(samples),
    )


def _delta(current: Mapping[str, Any], baseline: Mapping[str, Any]) -> Dict[str, float]:
    return {
        key: round(float(current[key]) - float(baseline[key]), 6)
        for key in (
            "base_accuracy",
            "stance_accuracy",
            "operation_accuracy",
            "intensity_accuracy",
            "full_code_accuracy",
        )
        if key in current and key in baseline
    }


def build_synthetic_trial_report(
    *,
    synthetic_path: Path = SYNTHETIC_CANDIDATES_PATH,
    hand_sample_path: Path = DEFAULT_SAMPLE_POOL_PATH,
    output_path: Path | None = SYNTHETIC_TRIAL_REPORT_PATH,
) -> Dict[str, Any]:
    synthetic = _load_synthetic_samples(synthetic_path)
    hand_pool = load_sample_pool(hand_sample_path)
    combined = tuple(hand_pool.cases) + synthetic

    hand_holdout = _group_holdout(hand_pool)
    synthetic_holdout = _group_holdout(_pool_for(synthetic_path, synthetic))
    combined_holdout = _group_holdout(_pool_for(synthetic_path, combined))
    synthetic_augmented_hand_holdout = _augmented_hand_group_holdout(
        hand_pool.cases,
        synthetic,
    )

    synthetic_model = PrototypeThoughtColorModel.train(synthetic)
    hand_model = PrototypeThoughtColorModel.train(hand_pool.cases)
    combined_model = PrototypeThoughtColorModel.train(combined)

    synthetic_to_hand = evaluate_samples(hand_pool.cases, synthetic_model)
    combined_to_hand = evaluate_samples(hand_pool.cases, combined_model)
    hand_to_synthetic = evaluate_samples(synthetic, hand_model)

    synthetic_to_hand_by_group = _by_group_eval(hand_pool.cases, synthetic_model)
    combined_to_hand_by_group = _by_group_eval(hand_pool.cases, combined_model)

    report = {
        "schema_version": "thought-color-synthetic-trial.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "synthetic_samples_are_training_data": False,
            "trial_treats_synthetic_as_provisional_training": True,
            "human_review_required_before_real_training": True,
        },
        "inputs": {
            "synthetic_path": str(synthetic_path),
            "hand_sample_path": str(hand_sample_path),
            "synthetic_count": len(synthetic),
            "hand_sample_count": len(hand_pool.cases),
            "combined_count": len(combined),
        },
        "baseline_hand_group_holdout": _summary_metrics(hand_holdout),
        "synthetic_only_group_holdout": _summary_metrics(synthetic_holdout),
        "combined_group_holdout": _summary_metrics(combined_holdout),
        "synthetic_augmented_hand_group_holdout": _summary_metrics(
            synthetic_augmented_hand_holdout
        ),
        "synthetic_train_to_hand_eval": _summary_metrics(synthetic_to_hand),
        "combined_train_to_hand_eval": _summary_metrics(combined_to_hand),
        "hand_train_to_synthetic_eval": _summary_metrics(hand_to_synthetic),
        "delta_vs_hand_group_holdout": {
            "synthetic_only_group_holdout": _delta(synthetic_holdout, hand_holdout),
            "combined_group_holdout": _delta(combined_holdout, hand_holdout),
            "synthetic_augmented_hand_group_holdout": _delta(
                synthetic_augmented_hand_holdout,
                hand_holdout,
            ),
            "synthetic_train_to_hand_eval": _delta(synthetic_to_hand, hand_holdout),
            "combined_train_to_hand_eval": _delta(combined_to_hand, hand_holdout),
        },
        "hand_group_changes": {
            "baseline_hand_group_holdout": {
                "case_count": hand_holdout["case_count"],
                "group_count": hand_holdout["group_count"],
                "by_group": hand_holdout["by_group"],
            },
            "synthetic_augmented_hand_group_holdout": {
                "case_count": synthetic_augmented_hand_holdout["case_count"],
                "group_count": synthetic_augmented_hand_holdout["group_count"],
                "by_group": synthetic_augmented_hand_holdout["by_group"],
            },
            "synthetic_train_to_hand": synthetic_to_hand_by_group,
            "combined_train_to_hand": combined_to_hand_by_group,
        },
        "synthetic_group_holdout_by_lane": synthetic_holdout.get("by_group", {}),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return report


def _print_summary(report: Mapping[str, Any]) -> None:
    summary = {
        "output": str(SYNTHETIC_TRIAL_REPORT_PATH),
        "inputs": report["inputs"],
        "baseline_hand_group_holdout": report["baseline_hand_group_holdout"],
        "synthetic_only_group_holdout": report["synthetic_only_group_holdout"],
        "combined_group_holdout": report["combined_group_holdout"],
        "synthetic_augmented_hand_group_holdout": report[
            "synthetic_augmented_hand_group_holdout"
        ],
        "synthetic_train_to_hand_eval": report["synthetic_train_to_hand_eval"],
        "combined_train_to_hand_eval": report["combined_train_to_hand_eval"],
        "delta_vs_hand_group_holdout": report["delta_vs_hand_group_holdout"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic-path", type=Path, default=SYNTHETIC_CANDIDATES_PATH)
    parser.add_argument("--hand-sample-path", type=Path, default=DEFAULT_SAMPLE_POOL_PATH)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    report = build_synthetic_trial_report(
        synthetic_path=args.synthetic_path,
        hand_sample_path=args.hand_sample_path,
        output_path=None if args.no_write else SYNTHETIC_TRIAL_REPORT_PATH,
    )
    _print_summary(report)


if __name__ == "__main__":
    main()



