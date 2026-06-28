"""Measure intent-corpus cleaning candidates without mutating training data.

This report is deliberately diagnostic. It answers: "If we quarantine a
suspect group, do the open/non-sealed route metrics improve?" It never edits
the corpus, deployed model, candidate model, or sealed fixtures.
"""

import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import run_core_shadow  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso
from semantic_routing.accumulation_review_store import (  # noqa: E402
    campaign_sha256,
    review_overlay,
)
from semantic_routing.adapter import route  # noqa: E402
from semantic_routing.conversation_accumulation import (  # noqa: E402
    load_conversation_accumulation,
)
from semantic_routing.intent_deployment import (  # noqa: E402
    evaluate_intent_gate,
    evaluate_intent_kfold,
    load_foundation_cases,
    load_hybrid_cases,
)
from semantic_routing.intent_model import IntentModel, load_intent_corpus  # noqa: E402


CORPUS_PATH = ROOT / "data" / "intent_training_corpus_v1.json"
SUSPECT_REVIEW_PATH = ROOT / "build" / "intent_corpus_suspect_review_v1.json"
CAMPAIGN_PATH = ROOT / "data" / "conversation_accumulation_v1.json"
REVIEW_PATH = ROOT / "data" / "conversation_accumulation_reviews_v1.json"
FOUNDATION_FIXTURE = ROOT / "tests" / "fixtures" / "intent_foundation_anchors_v1.json"
HYBRID_FIXTURE = ROOT / "tests" / "fixtures" / "intent_hybrid_regression_v1.json"
OUT_JSON = ROOT / "build" / "intent_data_cleaning_impact_v1.json"
OUT_MD = ROOT / "build" / "intent_data_cleaning_impact_v1.md"

ACTIONABLE_RECOMMENDATIONS = {
    "exclude",
    "exclude_or_negative",
    "exclude_or_relabel_clarify",
}


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _effective_status(case: Any, overlay: Dict[str, Any]) -> str:
    review = overlay.get(case.case_id)
    if isinstance(review, dict):
        return str(review["status"])
    if case.review_status in {"approved", "rejected"}:
        return case.review_status
    return "pending"


def _effective_expected(case: Any, overlay: Dict[str, Any]) -> Dict[str, str]:
    review = overlay.get(case.case_id)
    if isinstance(review, dict) and "expected" in review:
        return dict(review["expected"])
    return case.expected.as_dict()


def _evaluate_campaign(model: IntentModel) -> Dict[str, Any]:
    campaign = load_conversation_accumulation(CAMPAIGN_PATH)
    overlay = review_overlay(REVIEW_PATH, campaign_sha256(CAMPAIGN_PATH))
    semantic_passes = 0
    plan_passes = 0
    end_to_end_passes = 0
    critical_underprocessing = 0
    reviewed_count = 0
    misses: List[Dict[str, Any]] = []
    by_category: Counter[str] = Counter()
    category_failures: Counter[str] = Counter()

    for case in campaign.cases:
        expected = _effective_expected(case, overlay)
        if _effective_status(case, overlay) == "approved":
            reviewed_count += 1
        routed = route(case.input_text, intent_model=model)
        packet = routed.packet
        plan = routed.plan
        shadow = run_core_shadow(case.input_text, packet, plan)
        vertical = shadow.pipeline_state.get("vertical_stack")
        semantic_pass = packet.primary_intent == expected["intent"]
        plan_pass = (
            plan.processing_class == expected["processing_class"]
            and plan.core_mode == expected["core_mode"]
        )
        end_to_end_pass = semantic_pass and plan_pass
        underprocessed = case.critical_underprocessing and not end_to_end_pass

        by_category[case.category] += 1
        if not end_to_end_pass:
            category_failures[case.category] += 1
            misses.append(
                {
                    "id": case.case_id,
                    "category": case.category,
                    "expected": expected,
                    "actual": {
                        "intent": packet.primary_intent,
                        "processing_class": plan.processing_class,
                        "core_mode": plan.core_mode,
                        "decided_by": routed.trace.get("decided_by"),
                        "intent_margin": routed.trace.get("intent_margin"),
                        "vertical_execution_order": (
                            vertical["execution_order"] if vertical else None
                        ),
                    },
                    "critical_underprocessing": underprocessed,
                }
            )

        semantic_passes += semantic_pass
        plan_passes += plan_pass
        end_to_end_passes += end_to_end_pass
        critical_underprocessing += underprocessed

    count = len(campaign.cases)
    return {
        "case_count": count,
        "reviewed_count": reviewed_count,
        "semantic_intent_accuracy": _ratio(semantic_passes, count),
        "processing_plan_accuracy": _ratio(plan_passes, count),
        "end_to_end_route_accuracy": _ratio(end_to_end_passes, count),
        "passed": end_to_end_passes,
        "failed": count - end_to_end_passes,
        "critical_underprocessing": critical_underprocessing,
        "category_failures": dict(sorted(category_failures.items())),
        "misses": misses,
    }


def _train_and_score(
    approved_examples: Sequence[Dict[str, Any]],
    corpus_payload: Dict[str, Any],
    removed_indices: Set[int],
) -> Dict[str, Any]:
    filtered_examples = [
        example
        for index, example in enumerate(corpus_payload["examples"], start=1)
        if index not in removed_indices and example["review_status"] == "approved"
    ]
    model = IntentModel.train(filtered_examples)
    kfold = evaluate_intent_kfold(filtered_examples)
    model.metadata["metrics"] = kfold
    gate = evaluate_intent_gate(
        model,
        load_foundation_cases(FOUNDATION_FIXTURE),
        load_hybrid_cases(HYBRID_FIXTURE),
        current_metrics=None,
    )
    campaign = _evaluate_campaign(model)
    return {
        "approved_examples": len(approved_examples),
        "removed_examples": len(removed_indices),
        "filtered_examples": len(filtered_examples),
        "removed_by_intent": _removed_by_intent(corpus_payload, removed_indices),
        "filtered_by_intent": dict(
            sorted(Counter(e["intent"] for e in filtered_examples).items())
        ),
        "kfold": kfold,
        "gate": {
            "foundation_accuracy": gate["checks"]["foundation_anchors"]["accuracy"],
            "foundation_passed": gate["checks"]["foundation_anchors"]["passed"],
            "hybrid_accuracy": gate["checks"]["hybrid_regression"]["accuracy"],
            "hybrid_passed": gate["checks"]["hybrid_regression"]["passed"],
            "passed": gate["passed"],
        },
        "accumulation_route_eval": campaign,
    }


def _removed_by_intent(
    corpus_payload: Dict[str, Any],
    removed_indices: Iterable[int],
) -> Dict[str, int]:
    return dict(
        sorted(
            Counter(
                corpus_payload["examples"][index - 1]["intent"]
                for index in removed_indices
            ).items()
        )
    )


def _indices_where(rows: Sequence[Dict[str, Any]], predicate: Any) -> Set[int]:
    return {
        int(row["corpus_index"])
        for row in rows
        if predicate(row)
    }


def _scenario_specs(suspect_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    specs = [
        {
            "name": "high_priority_actionable",
            "description": (
                "Rows already flagged as exclude/exclude_or_negative/"
                "exclude_or_relabel_clarify."
            ),
            "proposed_action": "quarantine_for_review",
            "indices": _indices_where(
                suspect_rows,
                lambda row: row["recommendation"] in ACTIONABLE_RECOMMENDATIONS,
            ),
        },
        {
            "name": "exclude_or_negative",
            "description": "Weak/ack rows better stored as negative or guard memory.",
            "proposed_action": "move_to_negative_or_failure_memory",
            "indices": _indices_where(
                suspect_rows,
                lambda row: row["recommendation"] == "exclude_or_negative",
            ),
        },
        {
            "name": "exclude_or_relabel_clarify",
            "description": "Bare path/URL rows likely mislabeled as a direct intent.",
            "proposed_action": "quarantine_or_relabel",
            "indices": _indices_where(
                suspect_rows,
                lambda row: row["recommendation"] == "exclude_or_relabel_clarify",
            ),
        },
        {
            "name": "bare_path_or_url",
            "description": "Rows with a path/URL but no clear directive marker.",
            "proposed_action": "quarantine_or_relabel",
            "indices": _indices_where(
                suspect_rows,
                lambda row: "bare_path_or_url" in row["flags"],
            ),
        },
        {
            "name": "weak_question_respond_verify",
            "description": "Short weak questions carrying respond/verify labels.",
            "proposed_action": "quarantine_or_negative",
            "indices": _indices_where(
                suspect_rows,
                lambda row: (
                    "weak_question_suffix" in row["flags"]
                    and row["intent"] in {"respond", "verify"}
                ),
            ),
        },
        {
            "name": "very_short_control",
            "description": (
                "Very short rows are a control group; many are legitimate anchors."
            ),
            "proposed_action": "do_not_bulk_remove",
            "indices": _indices_where(
                suspect_rows,
                lambda row: "very_short_le_8" in row["flags"],
            ),
        },
        {
            "name": "all_suspects_diagnostic",
            "description": "All suspect rows removed; broad diagnostic only.",
            "proposed_action": "diagnostic_only_do_not_adopt_as_a_bulk_delete",
            "indices": {int(row["corpus_index"]) for row in suspect_rows},
        },
    ]
    return [spec for spec in specs if spec["indices"]]


def _delta_metrics(candidate: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    candidate_campaign = candidate["accumulation_route_eval"]
    baseline_campaign = baseline["accumulation_route_eval"]
    return {
        "kfold_accuracy": round(
            candidate["kfold"]["kfold_accuracy"]
            - baseline["kfold"]["kfold_accuracy"],
            6,
        ),
        "kfold_macro_accuracy": round(
            candidate["kfold"]["kfold_macro_accuracy"]
            - baseline["kfold"]["kfold_macro_accuracy"],
            6,
        ),
        "accumulation_end_to_end_accuracy": round(
            candidate_campaign["end_to_end_route_accuracy"]
            - baseline_campaign["end_to_end_route_accuracy"],
            6,
        ),
        "accumulation_failed": (
            candidate_campaign["failed"] - baseline_campaign["failed"]
        ),
        "critical_underprocessing": (
            candidate_campaign["critical_underprocessing"]
            - baseline_campaign["critical_underprocessing"]
        ),
    }


def _evidence_label(
    *,
    scenario_name: str,
    scored: Dict[str, Any],
    deltas: Dict[str, Any],
) -> str:
    if not scored["gate"]["passed"]:
        return "reject_gate_regression"
    if scenario_name == "all_suspects_diagnostic":
        return "diagnostic_only_too_broad"
    if scenario_name == "very_short_control":
        return "control_group_review_only"
    if (
        deltas["accumulation_end_to_end_accuracy"] > 0
        and deltas["critical_underprocessing"] <= 0
        and deltas["kfold_accuracy"] >= -0.01
    ):
        return "adoptable_quarantine_candidate"
    if (
        deltas["accumulation_end_to_end_accuracy"] == 0
        and deltas["critical_underprocessing"] <= 0
        and deltas["kfold_accuracy"] >= 0
    ):
        return "neutral_but_safe_review_candidate"
    return "needs_more_evidence_before_removal"


def _summarize_scenario(
    spec: Dict[str, Any],
    scored: Dict[str, Any],
    baseline: Dict[str, Any],
) -> Dict[str, Any]:
    deltas = _delta_metrics(scored, baseline)
    return {
        "name": spec["name"],
        "description": spec["description"],
        "proposed_action": spec.get("proposed_action", "row_level_review"),
        "removed_indices": sorted(spec["indices"]),
        "removed_count": len(spec["indices"]),
        "removed_by_intent": scored["removed_by_intent"],
        "gate": scored["gate"],
        "kfold": scored["kfold"],
        "accumulation_route_eval": {
            key: scored["accumulation_route_eval"][key]
            for key in (
                "case_count",
                "reviewed_count",
                "semantic_intent_accuracy",
                "processing_plan_accuracy",
                "end_to_end_route_accuracy",
                "passed",
                "failed",
                "critical_underprocessing",
                "category_failures",
            )
        },
        "delta_vs_baseline": deltas,
        "evidence_label": _evidence_label(
            scenario_name=spec["name"],
            scored=scored,
            deltas=deltas,
        ),
    }


def _individual_high_priority_specs(
    suspect_rows: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows = [
        row
        for row in suspect_rows
        if row["recommendation"] in ACTIONABLE_RECOMMENDATIONS
    ]
    specs = []
    for row in rows:
        specs.append(
            {
                "name": f"single_corpus_{row['corpus_index']}",
                "description": row["recommendation"],
                "row": row,
                "indices": {int(row["corpus_index"])},
            }
        )
    return specs


def _short_text(text: str, limit: int = 96) -> str:
    single = " ".join(text.split())
    return single if len(single) <= limit else single[: limit - 1] + "..."


def _write_markdown(report: Dict[str, Any]) -> None:
    lines = [
        "# Intent Data Cleaning Impact v1",
        "",
        "Diagnostic only. No corpus, deployed model, candidate model, or sealed "
        "fixture is modified.",
        "",
        "## Summary",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- baseline examples: {report['baseline']['filtered_examples']}",
        f"- suspect rows: {report['suspect_review']['suspect_count']}",
        f"- high-priority rows: {report['suspect_review']['high_priority_count']}",
        f"- sealed fixtures used: {report['policy']['sealed_fixtures_used']}",
        "",
        "## Scenario Ablations",
        "",
        "| scenario | action | removed | gate | kfold delta | route delta | failed delta | label |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for scenario in report["scenario_ablations"]:
        delta = scenario["delta_vs_baseline"]
        gate = "pass" if scenario["gate"]["passed"] else "fail"
        lines.append(
            "| "
            f"{scenario['name']} | "
            f"{scenario['proposed_action']} | "
            f"{scenario['removed_count']} | "
            f"{gate} | "
            f"{delta['kfold_accuracy']:+.6f} | "
            f"{delta['accumulation_end_to_end_accuracy']:+.6f} | "
            f"{delta['accumulation_failed']:+d} | "
            f"{scenario['evidence_label']} |"
        )

    lines.extend(
        [
            "",
            "## Individual High-Priority Rows",
            "",
            "| corpus index | recommendation | intent | kfold delta | route delta | failed delta | label | input |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in report["individual_high_priority"]:
        row = item["row"]
        delta = item["delta_vs_baseline"]
        lines.append(
            "| "
            f"{row['corpus_index']} | "
            f"{row['recommendation']} | "
            f"{row['intent']} | "
            f"{delta['kfold_accuracy']:+.6f} | "
            f"{delta['accumulation_end_to_end_accuracy']:+.6f} | "
            f"{delta['accumulation_failed']:+d} | "
            f"{item['evidence_label']} | "
            f"{_short_text(row['input']).replace('|', '&#124;')} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Rule",
            "",
            "- `adoptable_quarantine_candidate`: good removal candidate, but still "
            "review before changing corpus.",
            "- `neutral_but_safe_review_candidate`: safe-looking but not yet proven "
            "valuable.",
            "- `needs_more_evidence_before_removal`: keep or relabel until more "
            "non-sealed evidence arrives.",
            "- `diagnostic_only_too_broad`: useful for estimating damage, not for "
            "bulk deletion.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    if not SUSPECT_REVIEW_PATH.exists():
        raise FileNotFoundError(
            "run build/review_intent_corpus_suspects.py before impact analysis"
        )

    corpus_payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    approved_examples = load_intent_corpus(CORPUS_PATH)
    suspect_review = json.loads(SUSPECT_REVIEW_PATH.read_text(encoding="utf-8"))
    suspect_rows = list(suspect_review["all_suspects"])

    baseline = _train_and_score(approved_examples, corpus_payload, set())
    scenario_ablations = []
    for spec in _scenario_specs(suspect_rows):
        scored = _train_and_score(approved_examples, corpus_payload, spec["indices"])
        scenario_ablations.append(_summarize_scenario(spec, scored, baseline))

    individual_high_priority = []
    for spec in _individual_high_priority_specs(suspect_rows):
        scored = _train_and_score(approved_examples, corpus_payload, spec["indices"])
        summarized = _summarize_scenario(spec, scored, baseline)
        summarized["row"] = {
            key: spec["row"][key]
            for key in (
                "corpus_index",
                "input",
                "intent",
                "source",
                "flags",
                "recommendation",
            )
        }
        individual_high_priority.append(summarized)

    report = {
        "schema_version": "intent-data-cleaning-impact.v1",
        "generated_at": reproducible_now_iso(),
        "policy": {
            "diagnostic_only": True,
            "sealed_fixtures_used": False,
            "writes_training_corpus": False,
            "writes_deployed_model": False,
            "writes_candidate_model": False,
            "same_batch_tuning": False,
            "recommended_workflow": (
                "quarantine or relabel candidates only after human review "
                "and non-sealed ablation evidence"
            ),
        },
        "inputs": {
            "corpus": str(CORPUS_PATH.relative_to(ROOT)),
            "suspect_review": str(SUSPECT_REVIEW_PATH.relative_to(ROOT)),
            "conversation_accumulation": str(CAMPAIGN_PATH.relative_to(ROOT)),
            "conversation_reviews": str(REVIEW_PATH.relative_to(ROOT)),
            "foundation_fixture": str(FOUNDATION_FIXTURE.relative_to(ROOT)),
            "hybrid_fixture": str(HYBRID_FIXTURE.relative_to(ROOT)),
        },
        "suspect_review": {
            "suspect_count": suspect_review["summary"]["suspect_count"],
            "high_priority_count": suspect_review["summary"][
                "high_priority_review_count"
            ],
            "by_recommendation": suspect_review["summary"]["by_recommendation"],
            "by_flag": suspect_review["summary"]["by_flag"],
        },
        "baseline": {
            "filtered_examples": baseline["filtered_examples"],
            "filtered_by_intent": baseline["filtered_by_intent"],
            "gate": baseline["gate"],
            "kfold": baseline["kfold"],
            "accumulation_route_eval": {
                key: baseline["accumulation_route_eval"][key]
                for key in (
                    "case_count",
                    "reviewed_count",
                    "semantic_intent_accuracy",
                    "processing_plan_accuracy",
                    "end_to_end_route_accuracy",
                    "passed",
                    "failed",
                    "critical_underprocessing",
                    "category_failures",
                )
            },
        },
        "scenario_ablations": scenario_ablations,
        "individual_high_priority": individual_high_priority,
    }

    OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_markdown(report)

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "baseline": {
                    "kfold": report["baseline"]["kfold"]["kfold_accuracy"],
                    "route": report["baseline"]["accumulation_route_eval"][
                        "end_to_end_route_accuracy"
                    ],
                    "failed": report["baseline"]["accumulation_route_eval"][
                        "failed"
                    ],
                },
                "scenarios": [
                    {
                        "name": item["name"],
                        "removed": item["removed_count"],
                        "route_delta": item["delta_vs_baseline"][
                            "accumulation_end_to_end_accuracy"
                        ],
                        "failed_delta": item["delta_vs_baseline"][
                            "accumulation_failed"
                        ],
                        "label": item["evidence_label"],
                    }
                    for item in report["scenario_ablations"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
