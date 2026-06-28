"""Probe training without the 47 suspect corpus examples.

Diagnostic only: does not modify the deployed model, the candidate file, the
training corpus, or any sealed fixture.
"""

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import run_core_shadow
from semantic_routing.reproducibility import reproducible_now_iso
from semantic_routing.accumulation_review_store import (
    campaign_sha256,
    review_overlay,
)
from semantic_routing.adapter import route
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)
from semantic_routing.intent_deployment import (
    evaluate_intent_gate,
    evaluate_intent_kfold,
    load_foundation_cases,
    load_hybrid_cases,
)
from semantic_routing.intent_model import IntentModel, load_intent_corpus


CORPUS_PATH = ROOT / "data" / "intent_training_corpus_v1.json"
SUSPECT_REVIEW_PATH = ROOT / "build" / "intent_corpus_suspect_review_v1.json"
CAMPAIGN_PATH = ROOT / "data" / "conversation_accumulation_v1.json"
REVIEW_PATH = ROOT / "data" / "conversation_accumulation_reviews_v1.json"
FOUNDATION_FIXTURE = ROOT / "tests" / "fixtures" / "intent_foundation_anchors_v1.json"
HYBRID_FIXTURE = ROOT / "tests" / "fixtures" / "intent_hybrid_regression_v1.json"
OUT = ROOT / "build" / "probe_without_suspect_corpus_v1.json"


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _effective_status(case, overlay: dict) -> str:
    review = overlay.get(case.case_id)
    if isinstance(review, dict):
        return str(review["status"])
    if case.review_status == "approved":
        return "approved"
    if case.review_status == "rejected":
        return "rejected"
    return "pending"


def _effective_expected(case, overlay: dict) -> dict:
    review = overlay.get(case.case_id)
    if isinstance(review, dict) and "expected" in review:
        return review["expected"]
    return case.expected.as_dict()


def _evaluate_campaign(model: IntentModel) -> dict:
    campaign = load_conversation_accumulation(CAMPAIGN_PATH)
    overlay = review_overlay(REVIEW_PATH, campaign_sha256(CAMPAIGN_PATH))
    semantic_passes = 0
    plan_passes = 0
    end_to_end_passes = 0
    critical_underprocessing = 0
    reviewed_count = 0
    results = []
    for case in campaign.cases:
        expected = _effective_expected(case, overlay)
        if _effective_status(case, overlay) == "approved":
            reviewed_count += 1
        routed = route(case.input_text, intent_model=model)
        packet = routed.packet
        plan = routed.plan
        shadow = run_core_shadow(case.input_text, packet, plan)
        semantic_pass = packet.primary_intent == expected["intent"]
        plan_pass = (
            plan.processing_class == expected["processing_class"]
            and plan.core_mode == expected["core_mode"]
        )
        end_to_end_pass = semantic_pass and plan_pass
        underprocessed = case.critical_underprocessing and not end_to_end_pass
        semantic_passes += semantic_pass
        plan_passes += plan_pass
        end_to_end_passes += end_to_end_pass
        critical_underprocessing += underprocessed
        vertical = shadow.pipeline_state.get("vertical_stack")
        if not end_to_end_pass:
            results.append(
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
        "misses": results,
    }


def main() -> None:
    suspect = json.loads(SUSPECT_REVIEW_PATH.read_text(encoding="utf-8"))
    suspect_indices = {
        row["corpus_index"]
        for row in suspect["all_suspects"]
    }
    corpus_payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    full_examples = load_intent_corpus(CORPUS_PATH)
    filtered_examples = [
        example
        for index, example in enumerate(corpus_payload["examples"], start=1)
        if index not in suspect_indices and example["review_status"] == "approved"
    ]
    model = IntentModel.train(filtered_examples)
    metrics = evaluate_intent_kfold(filtered_examples)
    model.metadata["metrics"] = metrics
    model.metadata["trained_at"] = reproducible_now_iso()
    model.metadata["probe"] = "without_47_suspect_examples"

    gate = evaluate_intent_gate(
        model,
        load_foundation_cases(FOUNDATION_FIXTURE),
        load_hybrid_cases(HYBRID_FIXTURE),
        current_metrics=None,
    )
    campaign = _evaluate_campaign(model)

    report = {
        "schema_version": "intent-corpus-suspect-ablation-probe.v1",
        "generated_at": reproducible_now_iso(),
        "mutation": "exclude_all_47_suspect_examples_from_training_only",
        "writes_deployed_model": False,
        "active_sealed_v2_read": False,
        "training": {
            "full_approved_examples": len(full_examples),
            "removed_examples": len(suspect_indices),
            "filtered_examples": len(filtered_examples),
            "removed_by_intent": dict(
                sorted(
                    Counter(
                        corpus_payload["examples"][index - 1]["intent"]
                        for index in suspect_indices
                    ).items()
                )
            ),
            "filtered_by_intent": dict(
                sorted(Counter(e["intent"] for e in filtered_examples).items())
            ),
            "kfold": metrics,
        },
        "gate": {
            "foundation_anchors": gate["checks"]["foundation_anchors"],
            "hybrid_regression": gate["checks"]["hybrid_regression"],
            "contract_passed": gate["contract_passed"],
            "passed": gate["passed"],
        },
        "accumulation_route_eval": campaign,
    }
    OUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(
        {
            "training": report["training"],
            "gate_passed": report["gate"]["passed"],
            "accumulation": {
                key: campaign[key]
                for key in (
                    "passed",
                    "failed",
                    "end_to_end_route_accuracy",
                    "critical_underprocessing",
                )
            },
        },
        ensure_ascii=False,
        indent=2,
    ))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
