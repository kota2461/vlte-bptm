"""Compare the main adapter with the Thought Color experiment."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Sequence

from .data import copy_visible_benchmark, sha256_file
from .model import LayeredThoughtColorExtractor, evaluate_channel_predictions
from .paths import (
    COMPARISON_REPORT,
    SOURCE_BENCHMARK,
    VISIBLE_BENCHMARK_COPY,
    ensure_repo_on_path,
)

ensure_repo_on_path()

from semantic_routing import evaluate_plm_extractor, load_plm_benchmark, route  # noqa: E402


METRICS = (
    "valid_packet_rate",
    "intent_accuracy",
    "intent_macro_f1",
    "critical_signal_recall",
    "constraint_exact_match",
    "operation_exact_match",
    "risk_exact_match",
    "evidence_offset_validity",
)


def _metric_delta(
    experiment: Dict[str, Any],
    main: Dict[str, Any],
) -> Dict[str, float]:
    return {
        metric: round(experiment[metric] - main[metric], 6)
        for metric in METRICS
    }


def _load_benchmark(data_source: str):
    if data_source == "copy":
        if not VISIBLE_BENCHMARK_COPY.exists():
            copy_visible_benchmark()
        return load_plm_benchmark(VISIBLE_BENCHMARK_COPY), VISIBLE_BENCHMARK_COPY
    if data_source == "live":
        return load_plm_benchmark(SOURCE_BENCHMARK), SOURCE_BENCHMARK
    raise ValueError(f"unknown data source: {data_source}")


def build_report(
    *,
    data_source: str = "copy",
    output_path: Path | None = COMPARISON_REPORT,
) -> Dict[str, Any]:
    benchmark, benchmark_path = _load_benchmark(data_source)
    train_cases = benchmark.cases_for_splits(("train",))
    validation_cases = benchmark.cases_for_splits(("validation",))
    visible_cases = benchmark.cases_for_splits(("train", "validation"))
    model = LayeredThoughtColorExtractor.train(train_cases)

    def main_packet(text: str):
        return route(text).packet

    report = {
        "schema_version": "thought-color-performance-comparison.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "source": data_source,
            "benchmark_path": str(benchmark_path),
            "benchmark_sha256": sha256_file(benchmark_path),
            "train_count": len(train_cases),
            "validation_count": len(validation_cases),
            "visible_count": len(visible_cases),
            "sealed_cases_used_for_training": False,
            "sealed_cases_used_for_evaluation": False,
        },
        "experiment_model": model.as_dict(),
        "measurements": {},
    }

    for split_name, cases in (
        ("train", train_cases),
        ("validation", validation_cases),
        ("visible", visible_cases),
    ):
        main_eval = evaluate_plm_extractor(cases, main_packet)
        experiment_eval = evaluate_plm_extractor(cases, model.extractor())
        report["measurements"][split_name] = {
            "main_adapter": main_eval,
            "thought_color": experiment_eval,
            "thought_color_minus_main": _metric_delta(
                experiment_eval,
                main_eval,
            ),
            "thought_color_channels": evaluate_channel_predictions(
                cases,
                model,
            ),
        }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return report


def _summary(report: Dict[str, Any]) -> Dict[str, Any]:
    validation = report["measurements"]["validation"]
    return {
        "schema_version": report["schema_version"],
        "data": report["data"],
        "validation": {
            "main_adapter": {
                metric: validation["main_adapter"][metric]
                for metric in METRICS
            },
            "thought_color": {
                metric: validation["thought_color"][metric]
                for metric in METRICS
            },
            "thought_color_minus_main": validation[
                "thought_color_minus_main"
            ],
            "thought_color_channels": {
                key: value
                for key, value in validation[
                    "thought_color_channels"
                ].items()
                if key != "errors"
            },
        },
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-source",
        choices=("copy", "live"),
        default="copy",
        help="Use the experiment copy or the root benchmark directly.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help=(
            "Print a report without writing "
            "reports/thought_color_comparison_v0_1.json."
        ),
    )
    args = parser.parse_args(argv)

    report = build_report(
        data_source=args.data_source,
        output_path=None if args.no_write else COMPARISON_REPORT,
    )
    print(json.dumps(_summary(report), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

