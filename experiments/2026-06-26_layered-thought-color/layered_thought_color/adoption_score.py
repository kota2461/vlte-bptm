"""Adoption-value scoring for Thought Color Code v0.1."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .compare import build_report
from .paths import COMPARISON_REPORT, REPORTS_DIR


ADOPTION_SCORE_REPORT = REPORTS_DIR / "thought_color_adoption_score_v0_1.json"

SEMANTIC_METRICS = (
    "intent_accuracy",
    "intent_macro_f1",
    "critical_signal_recall",
    "constraint_exact_match",
    "operation_exact_match",
    "risk_exact_match",
)

CHANNEL_WEIGHTS = {
    "base_accuracy": 0.25,
    "operation_accuracy": 0.20,
    "stance_accuracy": 0.20,
    "intensity_accuracy": 0.20,
    "full_code_accuracy": 0.15,
}


def _mean(values: Sequence[float]) -> float:
    items = tuple(values)
    return sum(items) / len(items) if items else 0.0


def _round_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def _load_or_build_comparison(
    *,
    refresh: bool,
    comparison_path: Path = COMPARISON_REPORT,
) -> Dict[str, Any]:
    if refresh or not comparison_path.exists():
        return build_report(output_path=comparison_path)
    return json.loads(comparison_path.read_text(encoding="utf-8"))


def _semantic_score(validation: Mapping[str, Any]) -> float:
    thought_color = validation["thought_color"]
    return _mean(float(thought_color[metric]) for metric in SEMANTIC_METRICS)


def _channel_score(validation: Mapping[str, Any]) -> float:
    channels = validation["thought_color_channels"]
    return sum(
        float(channels[metric]) * weight
        for metric, weight in CHANNEL_WEIGHTS.items()
    )


def _safety_score(report: Mapping[str, Any]) -> float:
    data = report["data"]
    if (
        data["sealed_cases_used_for_training"]
        or data["sealed_cases_used_for_evaluation"]
    ):
        return 0.0
    validation = report["measurements"]["validation"]["thought_color"]
    if validation["valid_packet_rate"] < 1.0:
        return 0.5
    return 1.0


def _verdict(adoption_score: int, replacement_score: int) -> str:
    if replacement_score >= 80 and adoption_score >= 80:
        return "mainline_candidate"
    if adoption_score >= 65:
        return "experimental_auxiliary_candidate"
    if adoption_score >= 50:
        return "research_only"
    return "do_not_adopt_yet"


def build_adoption_score(
    *,
    refresh: bool = False,
    output_path: Path | None = ADOPTION_SCORE_REPORT,
) -> Dict[str, Any]:
    comparison = _load_or_build_comparison(refresh=refresh)
    validation = comparison["measurements"]["validation"]
    semantic = _semantic_score(validation)
    channel = _channel_score(validation)
    safety = _safety_score(comparison)
    design_fit = 0.80

    adoption_value = _round_score(
        100.0
        * (
            0.50 * semantic
            + 0.25 * channel
            + 0.15 * safety
            + 0.10 * design_fit
        )
    )
    mainline_replacement = _round_score(
        100.0 * (0.80 * semantic + 0.10 * channel + 0.10 * safety)
    )
    research_lane = _round_score(
        100.0
        * (
            0.40 * semantic
            + 0.30 * channel
            + 0.20 * safety
            + 0.10 * design_fit
        )
    )

    report = {
        "schema_version": "thought-color-adoption-score.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "comparison_report": str(COMPARISON_REPORT),
        "scores": {
            "adoption_value": adoption_value,
            "mainline_replacement": mainline_replacement,
            "research_lane": research_lane,
        },
        "verdict": _verdict(adoption_value, mainline_replacement),
        "components": {
            "semantic_score": round(semantic, 6),
            "channel_score": round(channel, 6),
            "safety_score": round(safety, 6),
            "design_fit_score": round(design_fit, 6),
        },
        "rubric": {
            "adoption_value": {
                "semantic_metrics": 0.50,
                "channel_metrics": 0.25,
                "data_safety": 0.15,
                "design_fit": 0.10,
            },
            "mainline_replacement": {
                "semantic_metrics": 0.80,
                "channel_metrics": 0.10,
                "data_safety": 0.10,
            },
            "research_lane": {
                "semantic_metrics": 0.40,
                "channel_metrics": 0.30,
                "data_safety": 0.20,
                "design_fit": 0.10,
            },
        },
        "thresholds": {
            "mainline_candidate": {
                "adoption_value": 80,
                "mainline_replacement": 80,
            },
            "experimental_auxiliary_candidate": {
                "adoption_value": 65,
            },
        },
        "recommendation": [
            "Do not replace the main adapter.",
            "Keep Thought Color as an auxiliary experimental feature lane.",
            "Prioritize base and operation channel improvement before main integration.",
            "Re-score after base_accuracy and operation_accuracy both exceed 0.75 on validation.",
        ],
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Rebuild the comparison report before scoring.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print without writing the adoption score report.",
    )
    args = parser.parse_args(argv)
    report = build_adoption_score(
        refresh=args.refresh,
        output_path=None if args.no_write else ADOPTION_SCORE_REPORT,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


