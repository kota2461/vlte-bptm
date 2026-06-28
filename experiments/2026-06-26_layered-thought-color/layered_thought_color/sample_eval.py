"""Evaluate models on the dedicated Thought Color sample pool."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from .code import ThoughtColorCode
from .paths import REPORTS_DIR
from .sample_pool import (
    DEFAULT_SAMPLE_POOL_PATH,
    ThoughtColorSample,
    ThoughtColorSamplePool,
    load_sample_pool,
)

from .paths import ensure_repo_on_path

ensure_repo_on_path()

from pattern_learning.trainer import text_features  # noqa: E402


SAMPLE_EVAL_REPORT = REPORTS_DIR / "thought_color_sample_pool_eval_v0_1.json"


def _dot(left: Mapping[int, float], right: Mapping[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(index, 0.0) for index, value in left.items())


def _normalize(features: Mapping[int, float]) -> Dict[int, float]:
    norm = math.sqrt(sum(value * value for value in features.values())) or 1.0
    return {index: value / norm for index, value in features.items() if value}


@dataclass(frozen=True)
class PrototypeExample:
    case_id: str
    features: Mapping[int, float]
    code: ThoughtColorCode


@dataclass(frozen=True)
class PrototypeThoughtColorModel:
    """Tiny prototype model for the dedicated sample pool."""

    examples: Tuple[PrototypeExample, ...]
    dimension: int = 2048

    @classmethod
    def train(
        cls,
        samples: Sequence[ThoughtColorSample],
        *,
        dimension: int = 2048,
    ) -> "PrototypeThoughtColorModel":
        if not samples:
            raise ValueError("at least one sample is required")
        return cls(
            examples=tuple(
                PrototypeExample(
                    case_id=sample.case_id,
                    features=_normalize(text_features(sample.input_text, dimension)),
                    code=sample.expected,
                )
                for sample in samples
            ),
            dimension=dimension,
        )

    def predict(self, text: str) -> ThoughtColorCode:
        features = _normalize(text_features(text, self.dimension))
        return max(
            self.examples,
            key=lambda example: (_dot(features, example.features), example.case_id),
        ).code


def _ratio(count: int, total: int) -> float:
    return round(count / total, 6) if total else 0.0


def evaluate_samples(
    samples: Sequence[ThoughtColorSample],
    model: PrototypeThoughtColorModel,
) -> Dict[str, Any]:
    counts = Counter()
    errors = []
    by_lane: Dict[str, Counter[str]] = defaultdict(Counter)
    for sample in samples:
        expected = sample.expected
        predicted = model.predict(sample.input_text)
        counts["total"] += 1
        lane = by_lane[sample.lane]
        lane["total"] += 1
        for name, matched in (
            ("base", predicted.base_id == expected.base_id),
            ("stance", predicted.stance == expected.stance),
            ("operation", predicted.operation == expected.operation),
            ("intensity", predicted.intensity == expected.intensity),
            ("full", predicted.channel_tuple() == expected.channel_tuple()),
        ):
            counts[name] += matched
            lane[name] += matched
        if predicted.channel_tuple() != expected.channel_tuple():
            errors.append(
                {
                    "id": sample.case_id,
                    "lane": sample.lane,
                    "group_id": sample.group_id,
                    "expected": {
                        "base_id": expected.base_id,
                        "stance": expected.label_tuple()[1],
                        "operation": expected.label_tuple()[2],
                        "intensity": expected.label_tuple()[3],
                    },
                    "predicted": {
                        "base_id": predicted.base_id,
                        "stance": predicted.label_tuple()[1],
                        "operation": predicted.label_tuple()[2],
                        "intensity": predicted.label_tuple()[3],
                    },
                }
            )

    total = counts["total"]
    lane_metrics = {}
    for lane, lane_counts in sorted(by_lane.items()):
        lane_total = lane_counts["total"]
        lane_metrics[lane] = {
            "case_count": lane_total,
            "base_accuracy": _ratio(lane_counts["base"], lane_total),
            "stance_accuracy": _ratio(lane_counts["stance"], lane_total),
            "operation_accuracy": _ratio(lane_counts["operation"], lane_total),
            "intensity_accuracy": _ratio(lane_counts["intensity"], lane_total),
            "full_code_accuracy": _ratio(lane_counts["full"], lane_total),
        }

    return {
        "schema_version": "thought-color-sample-evaluation.v0.1",
        "case_count": total,
        "base_accuracy": _ratio(counts["base"], total),
        "stance_accuracy": _ratio(counts["stance"], total),
        "operation_accuracy": _ratio(counts["operation"], total),
        "intensity_accuracy": _ratio(counts["intensity"], total),
        "full_code_accuracy": _ratio(counts["full"], total),
        "by_lane": lane_metrics,
        "errors": errors,
    }


def _group_holdout(pool: ThoughtColorSamplePool) -> Dict[str, Any]:
    group_ids = sorted({sample.group_id for sample in pool.cases})
    all_errors = []
    aggregate = Counter()
    by_group = {}
    for group_id in group_ids:
        train = [sample for sample in pool.cases if sample.group_id != group_id]
        held = [sample for sample in pool.cases if sample.group_id == group_id]
        model = PrototypeThoughtColorModel.train(train)
        result = evaluate_samples(held, model)
        for key in (
            "base_accuracy",
            "stance_accuracy",
            "operation_accuracy",
            "intensity_accuracy",
            "full_code_accuracy",
        ):
            aggregate[key] += result[key] * result["case_count"]
        aggregate["case_count"] += result["case_count"]
        by_group[group_id] = {
            key: value
            for key, value in result.items()
            if key not in {"errors", "by_lane", "schema_version"}
        }
        all_errors.extend(result["errors"])

    total = aggregate["case_count"]
    return {
        "schema_version": "thought-color-sample-group-holdout.v0.1",
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


def build_sample_eval_report(
    *,
    sample_path: Path = DEFAULT_SAMPLE_POOL_PATH,
    output_path: Path | None = SAMPLE_EVAL_REPORT,
) -> Dict[str, Any]:
    pool = load_sample_pool(sample_path)
    all_fit_model = PrototypeThoughtColorModel.train(pool.cases)
    report = {
        "schema_version": "thought-color-sample-pool-eval-report.v0.1",
        "sample_pool": pool.summary(),
        "model": {
            "kind": "prototype_1nn",
            "dimension": all_fit_model.dimension,
            "note": (
                "All-fit is a label/sanity check. Group holdout is the "
                "generalization check across sample groups."
            ),
        },
        "all_fit": evaluate_samples(pool.cases, all_fit_model),
        "group_holdout": _group_holdout(pool),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return report


def _summary(report: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": report["schema_version"],
        "case_count": report["sample_pool"]["case_count"],
        "all_fit": {
            key: value
            for key, value in report["all_fit"].items()
            if key.endswith("_accuracy") or key == "case_count"
        },
        "group_holdout": {
            key: value
            for key, value in report["group_holdout"].items()
            if key.endswith("_accuracy") or key in {"case_count", "group_count"}
        },
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-path", type=Path, default=DEFAULT_SAMPLE_POOL_PATH)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    report = build_sample_eval_report(
        sample_path=args.sample_path,
        output_path=None if args.no_write else SAMPLE_EVAL_REPORT,
    )
    print(json.dumps(_summary(report), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

