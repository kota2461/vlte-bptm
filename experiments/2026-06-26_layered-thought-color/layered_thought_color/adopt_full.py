"""Freeze the full corrected Thought Color sample set as adopted v0.2."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .paths import DATA_DIR, REPORTS_DIR


SOURCE_FULL_ABLATION_PATH = (
    DATA_DIR / "thought_color_adopted_plus_weakness_summary_corrected_ablation_v0_1.json"
)
SOURCE_FULL_EVAL_REPORT_PATH = (
    REPORTS_DIR / "thought_color_summary_share_correction_eval_v0_1.json"
)
PREVIOUS_ADOPTED_PATH = DATA_DIR / "thought_color_adopted_corrected_v0_1.json"
ADOPTED_FULL_PATH = DATA_DIR / "thought_color_adopted_full_v0_2.json"
ADOPTION_FULL_REPORT_PATH = REPORTS_DIR / "thought_color_adoption_full_v0_2.json"


def _adopt_full(payload: Mapping[str, Any]) -> Dict[str, Any]:
    adopted = copy.deepcopy(payload)
    adopted["schema_version"] = "thought-color-adopted-full.v0.2"
    adopted["created_at"] = datetime.now(timezone.utc).isoformat()
    adopted["adoption"] = {
        "status": "adopted_for_thought_color_experiment",
        "basis": "weakness-isolated 72 samples plus summary-share correction accepted by user",
        "scope": "experiment_only",
        "mainline_replacement": False,
        "previous_adopted_path": str(PREVIOUS_ADOPTED_PATH),
    }
    adopted["policy"] = {
        "experiment_training_allowed": True,
        "mainline_training_allowed": False,
        "human_review_completed_by_user": True,
        "sealed_fixtures_used": False,
        "keep_source_ablation": True,
    }
    for sample in adopted["samples"]:
        sample["pre_full_adoption_status"] = sample.get("adoption_status")
        sample["pre_full_training_allowed"] = sample.get("training_allowed")
        sample["pre_full_human_review_required"] = sample.get("human_review_required")
        sample["adoption_status"] = "adopted_experiment_full_v0_2"
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
        "lane_counts": dict(
            sorted(Counter(s["lane"] for s in adopted["samples"]).items())
        ),
        "base_counts": dict(
            sorted(Counter(s["expected"]["base_label"] for s in adopted["samples"]).items())
        ),
    }
    return adopted


def _final_metrics(eval_report: Mapping[str, Any]) -> Dict[str, Any]:
    original = eval_report["original_hand_eval"]
    display_safe = eval_report["display_safe_hand_eval"]
    return {
        "original_hand_eval": {
            "before_summary_correction": original["before"],
            "adopted_full": original["after"],
            "delta_from_pre_summary_correction": original["delta"],
            "summary_share_after": original["summary_share_after"],
            "regressed_groups_after_summary_correction": original["regressed_groups"],
        },
        "display_safe_shadow_eval": {
            "before_summary_correction": display_safe["before"],
            "adopted_full": display_safe["after"],
            "delta_from_pre_summary_correction": display_safe["delta"],
            "summary_share_after": display_safe["summary_share_after"],
            "regressed_groups_after_summary_correction": display_safe["regressed_groups"],
        },
    }


def build_full_adoption(
    *,
    source_path: Path = SOURCE_FULL_ABLATION_PATH,
    eval_report_path: Path = SOURCE_FULL_EVAL_REPORT_PATH,
    adopted_path: Path = ADOPTED_FULL_PATH,
    report_path: Path = ADOPTION_FULL_REPORT_PATH,
) -> Dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
    adopted = _adopt_full(source)
    adopted_path.write_text(
        json.dumps(adopted, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report = {
        "schema_version": "thought-color-adoption-full.v0.2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": {
            "status": "adopted",
            "scope": "thought_color_experiment_only",
            "reason": (
                "The isolated weakness set and summary-share correction improved "
                "the trial metrics without observed group regressions."
            ),
        },
        "paths": {
            "source_full_ablation": str(source_path),
            "source_eval_report": str(eval_report_path),
            "previous_adopted": str(PREVIOUS_ADOPTED_PATH),
            "adopted_full": str(adopted_path),
        },
        "adopted_summary": adopted["summary"],
        "final_metrics": _final_metrics(eval_report),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-path", type=Path, default=SOURCE_FULL_ABLATION_PATH)
    parser.add_argument("--eval-report-path", type=Path, default=SOURCE_FULL_EVAL_REPORT_PATH)
    args = parser.parse_args(argv)
    report = build_full_adoption(
        source_path=args.source_path,
        eval_report_path=args.eval_report_path,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
