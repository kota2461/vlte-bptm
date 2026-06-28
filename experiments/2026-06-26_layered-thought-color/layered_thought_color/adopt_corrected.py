"""Freeze the corrected Thought Color sample set as the adopted experiment set."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .paths import DATA_DIR, REPORTS_DIR


CORRECTED_CANDIDATES_PATH = DATA_DIR / "thought_color_corrected_candidates_v0_1.json"
CORRECTED_TRIAL_REPORT_PATH = REPORTS_DIR / "thought_color_corrected_trial_v0_1.json"
ADOPTED_CORRECTED_PATH = DATA_DIR / "thought_color_adopted_corrected_v0_1.json"
ADOPTION_FREEZE_REPORT_PATH = REPORTS_DIR / "thought_color_adoption_freeze_v0_1.json"
WEAKNESS_ISOLATED_PLAN_PATH = DATA_DIR / "thought_color_weakness_isolated_plan_v0_1.json"
WEAKNESS_ISOLATED_SAMPLES_PATH = DATA_DIR / "thought_color_weakness_isolated_samples_v0_1.json"


LOW_GROUP_FULL_THRESHOLD = 0.5
LOW_GROUP_BASE_THRESHOLD = 0.5


def _adopt_samples(payload: Mapping[str, Any]) -> Dict[str, Any]:
    adopted = copy.deepcopy(payload)
    adopted["schema_version"] = "thought-color-adopted-corrected.v0.1"
    adopted["created_at"] = datetime.now(timezone.utc).isoformat()
    adopted["adoption"] = {
        "status": "adopted_for_thought_color_experiment",
        "basis": "regression-cleared corrected trial accepted by user",
        "scope": "experiment_only",
        "mainline_replacement": False,
    }
    adopted["policy"] = {
        "experiment_training_allowed": True,
        "mainline_training_allowed": False,
        "human_review_completed_by_user": True,
        "sealed_fixtures_used": False,
        "keep_candidate_sources": True,
    }
    for sample in adopted["samples"]:
        sample["pre_adoption_status"] = sample.get("adoption_status")
        sample["pre_adoption_training_allowed"] = sample.get("training_allowed")
        sample["pre_adoption_human_review_required"] = sample.get(
            "human_review_required"
        )
        sample["adoption_status"] = "adopted_experiment_corrected_v0_1"
        sample["training_allowed"] = True
        sample["human_review_required"] = False
        sample["adoption_scope"] = "thought_color_experiment_only"
    adopted["summary"] = {
        **adopted.get("summary", {}),
        "sample_count": len(adopted["samples"]),
        "training_allowed_count": sum(
            1 for sample in adopted["samples"] if sample.get("training_allowed")
        ),
        "human_review_required_count": sum(
            1 for sample in adopted["samples"] if sample.get("human_review_required")
        ),
        "adoption_status_counts": dict(
            sorted(Counter(s["adoption_status"] for s in adopted["samples"]).items())
        ),
    }
    return adopted


def _low_groups(trial_report: Mapping[str, Any]) -> list[Dict[str, Any]]:
    by_group = trial_report["hand_group_changes"][
        "synthetic_augmented_hand_group_holdout"
    ]["by_group"]
    targets = []
    for group_id, metrics in sorted(
        by_group.items(),
        key=lambda item: (
            item[1]["full_code_accuracy"],
            item[1]["base_accuracy"],
            item[0],
        ),
    ):
        is_low = (
            metrics["full_code_accuracy"] < LOW_GROUP_FULL_THRESHOLD
            or metrics["base_accuracy"] < LOW_GROUP_BASE_THRESHOLD
        )
        if not is_low:
            continue
        targets.append(
            {
                "group_id": group_id,
                "metrics": {
                    key: metrics[key]
                    for key in (
                        "case_count",
                        "base_accuracy",
                        "stance_accuracy",
                        "operation_accuracy",
                        "intensity_accuracy",
                        "full_code_accuracy",
                    )
                },
                "reason": "remaining isolated weakness; do not mix into adopted set by default",
            }
        )
    return targets


def _recommended_budget(group_id: str) -> int:
    return {
        "empathy_across_bases": 20,
        "summary_share_variants": 16,
        "verify_stance_variants": 12,
        "explore_operation_variants": 12,
        "generate_across_bases": 12,
    }.get(group_id, 8)


def _weakness_plan(trial_report: Mapping[str, Any]) -> Dict[str, Any]:
    targets = _low_groups(trial_report)
    return {
        "schema_version": "thought-color-weakness-isolated-plan.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "mix_with_adopted_set_by_default": False,
            "evaluate_as_separate_ablation": True,
            "adopted_baseline_path": str(ADOPTED_CORRECTED_PATH),
            "report_delta_against_adopted_baseline": True,
        },
        "purpose": (
            "Keep remaining weakness work isolated so later additions do not hide "
            "negative deltas against the adopted corrected set."
        ),
        "targets": [
            {
                **target,
                "recommended_sample_budget": _recommended_budget(target["group_id"]),
            }
            for target in targets
        ],
        "target_count": len(targets),
        "recommended_total_sample_budget": sum(
            _recommended_budget(target["group_id"]) for target in targets
        ),
    }


def _empty_weakness_samples(plan: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "thought-color-weakness-isolated-samples.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": plan["policy"],
        "targets": plan["targets"],
        "samples": [],
        "sample_count": 0,
    }


def build_adoption_freeze(
    *,
    corrected_path: Path = CORRECTED_CANDIDATES_PATH,
    trial_report_path: Path = CORRECTED_TRIAL_REPORT_PATH,
    adopted_path: Path = ADOPTED_CORRECTED_PATH,
    freeze_report_path: Path = ADOPTION_FREEZE_REPORT_PATH,
    weakness_plan_path: Path = WEAKNESS_ISOLATED_PLAN_PATH,
    weakness_samples_path: Path = WEAKNESS_ISOLATED_SAMPLES_PATH,
) -> Dict[str, Any]:
    corrected = json.loads(corrected_path.read_text(encoding="utf-8"))
    trial_report = json.loads(trial_report_path.read_text(encoding="utf-8"))
    adopted = _adopt_samples(corrected)
    weakness_plan = _weakness_plan(trial_report)
    weakness_samples = _empty_weakness_samples(weakness_plan)

    adopted_path.write_text(
        json.dumps(adopted, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    weakness_plan_path.write_text(
        json.dumps(weakness_plan, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    weakness_samples_path.write_text(
        json.dumps(weakness_samples, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    freeze_report = {
        "schema_version": "thought-color-adoption-freeze.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": {
            "status": "adopted",
            "scope": "thought_color_experiment_only",
            "reason": "corrective samples removed the observed regression in the requested groups",
        },
        "paths": {
            "source_corrected_candidates": str(corrected_path),
            "source_corrected_trial_report": str(trial_report_path),
            "adopted_corrected": str(adopted_path),
            "weakness_isolated_plan": str(weakness_plan_path),
            "weakness_isolated_samples": str(weakness_samples_path),
        },
        "adopted_summary": adopted["summary"],
        "adopted_trial_key_metrics": {
            "baseline_hand_group_holdout": trial_report[
                "baseline_hand_group_holdout"
            ],
            "adopted_corrected_group_holdout": trial_report[
                "synthetic_augmented_hand_group_holdout"
            ],
            "delta_vs_baseline": trial_report["delta_vs_hand_group_holdout"][
                "synthetic_augmented_hand_group_holdout"
            ],
        },
        "isolated_weakness_plan": {
            "target_count": weakness_plan["target_count"],
            "recommended_total_sample_budget": weakness_plan[
                "recommended_total_sample_budget"
            ],
            "targets": weakness_plan["targets"],
        },
    }
    freeze_report_path.write_text(
        json.dumps(freeze_report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return freeze_report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corrected-path", type=Path, default=CORRECTED_CANDIDATES_PATH)
    args = parser.parse_args(argv)
    report = build_adoption_freeze(corrected_path=args.corrected_path)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
