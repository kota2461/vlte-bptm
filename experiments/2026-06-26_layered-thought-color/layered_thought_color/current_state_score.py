"""Current-state scoring for the Thought Color experiment."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .adoption_score import build_adoption_score
from .paths import REPORTS_DIR
from .sample_eval import build_sample_eval_report
from .sample_harvest import HARVEST_REPORT_PATH, summarize, write_harvest


CURRENT_STATE_SCORE_REPORT = (
    REPORTS_DIR / "thought_color_current_state_score_v0_1.json"
)

CHANNEL_WEIGHTS = {
    "base_accuracy": 0.25,
    "operation_accuracy": 0.20,
    "stance_accuracy": 0.20,
    "intensity_accuracy": 0.20,
    "full_code_accuracy": 0.15,
}


def _round_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def _weighted_channels(metrics: Mapping[str, Any]) -> float:
    return sum(float(metrics[name]) * weight for name, weight in CHANNEL_WEIGHTS.items())


def _load_harvest_report(*, refresh: bool) -> Dict[str, Any]:
    if refresh or not HARVEST_REPORT_PATH.exists():
        return write_harvest()
    return json.loads(HARVEST_REPORT_PATH.read_text(encoding="utf-8"))


def _corpus_readiness_score(harvest: Mapping[str, Any]) -> int:
    source_count = len(harvest["source_counts"])
    base_count = len(harvest["base_counts"])
    quality_flags = sum(harvest.get("quality_flag_counts", {}).values())
    training_allowed = int(harvest["training_allowed_count"])
    quality_score = 1.0 - min(0.30, quality_flags / max(1, training_allowed))

    policy = harvest["policy"]
    hygiene_score = 1.0 if (
        policy["sealed_fixtures_used"] is False
        and policy["raw_router_turn_text_used"] is False
        and policy["review_required_items_are_training_data"] is False
    ) else 0.0

    return _round_score(
        100.0
        * (
            0.30 * min(training_allowed / 220.0, 1.0)
            + 0.20 * min(base_count / 7.0, 1.0)
            + 0.15 * min(source_count / 4.0, 1.0)
            + 0.20 * hygiene_score
            + 0.10 * min(int(harvest["route_gap_count"]) / 10.0, 1.0)
            + 0.05 * quality_score
        )
    )


def build_current_state_score(
    *,
    refresh: bool = False,
    output_path: Path | None = CURRENT_STATE_SCORE_REPORT,
) -> Dict[str, Any]:
    adoption = build_adoption_score(refresh=refresh, output_path=None)
    sample_eval = build_sample_eval_report(output_path=None)
    harvest = _load_harvest_report(refresh=refresh)

    group_holdout = sample_eval["group_holdout"]
    group_holdout_score = _round_score(100.0 * _weighted_channels(group_holdout))
    corpus_readiness = _corpus_readiness_score(harvest)
    adoption_value = int(adoption["scores"]["adoption_value"])
    mainline_replacement = int(adoption["scores"]["mainline_replacement"])
    research_lane = int(adoption["scores"]["research_lane"])

    current_experimental_value = _round_score(
        0.35 * adoption_value
        + 0.30 * corpus_readiness
        + 0.20 * research_lane
        + 0.15 * group_holdout_score
    )
    growth_potential = _round_score(
        0.45 * corpus_readiness
        + 0.25 * research_lane
        + 0.20 * adoption["components"]["channel_score"] * 100.0
        + 0.10 * adoption["components"]["safety_score"] * 100.0
    )
    stability_now = _round_score(
        0.45 * adoption_value
        + 0.35 * group_holdout_score
        + 0.20 * adoption["components"]["safety_score"] * 100.0
    )

    verdict = (
        "dual_lane_growth_candidate"
        if current_experimental_value >= 70 and growth_potential >= 80
        else adoption["verdict"]
    )

    report = {
        "schema_version": "thought-color-current-state-score.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scores": {
            "current_experimental_value": current_experimental_value,
            "growth_potential": growth_potential,
            "stability_now": stability_now,
            "mainline_replacement": mainline_replacement,
            "corpus_readiness": corpus_readiness,
            "group_holdout_generalization": group_holdout_score,
        },
        "verdict": verdict,
        "components": {
            "adoption_value": adoption_value,
            "research_lane": research_lane,
            "mainline_replacement": mainline_replacement,
            "semantic_score": adoption["components"]["semantic_score"],
            "channel_score": adoption["components"]["channel_score"],
            "safety_score": adoption["components"]["safety_score"],
            "group_holdout": {
                key: group_holdout[key]
                for key in (
                    "base_accuracy",
                    "stance_accuracy",
                    "operation_accuracy",
                    "intensity_accuracy",
                    "full_code_accuracy",
                )
            },
            "harvest": {
                "sample_count": harvest["sample_count"],
                "training_allowed_count": harvest["training_allowed_count"],
                "review_required_count": harvest["review_required_count"],
                "route_gap_count": harvest["route_gap_count"],
                "source_counts": harvest["source_counts"],
                "base_counts": harvest["base_counts"],
                "quality_flag_counts": harvest.get("quality_flag_counts", {}),
            },
        },
        "interpretation": [
            "Mainline replacement is still not recommended.",
            "The harvested sample base materially improves the experiment's growth position.",
            "Group-holdout generalization remains the weakest current signal.",
            "Best next step: train on approved harvested samples and keep review_required router items as a separate review queue.",
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
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    report = build_current_state_score(
        refresh=args.refresh,
        output_path=None if args.no_write else CURRENT_STATE_SCORE_REPORT,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

