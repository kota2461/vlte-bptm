"""Evaluate the open accumulation campaign without reading active sealed v2."""

import json
import hashlib
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import (
    ADAPTER_VERSION,
    DEFAULT_INTENT_MODEL_PATH,
    route,
    run_core_shadow,
)
from semantic_routing.reproducibility import reproducible_now
from semantic_routing.accumulation_review_store import (
    campaign_sha256,
    review_overlay,
)
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)


CAMPAIGN_PATH = ROOT / "data" / "conversation_accumulation_v1.json"
REVIEW_PATH = ROOT / "data" / "conversation_accumulation_reviews_v1.json"
BENCHMARK_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
OUTPUT_PATH = ROOT / "build" / "conversation_accumulation_v1_report.json"


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main() -> None:
    campaign = load_conversation_accumulation(CAMPAIGN_PATH)
    # Overlay human review decisions (UI writes here). The source campaign
    # file stays immutable; approvals and corrected expecteds come from the
    # SHA-bound review log, so a UI approval moves the gate and a corrected
    # `expected` becomes the measurement target.
    overlay = review_overlay(REVIEW_PATH, campaign_sha256(CAMPAIGN_PATH))

    def effective_status(case) -> str:
        review = overlay.get(case.case_id)
        if isinstance(review, dict):
            return str(review["status"])
        return (
            "approved"
            if case.review_status == "approved"
            else "rejected"
            if case.review_status == "rejected"
            else "pending"
        )

    def effective_expected(case):
        review = overlay.get(case.case_id)
        if isinstance(review, dict) and "expected" in review:
            return review["expected"]
        return case.expected.as_dict()

    now = reproducible_now()
    deadline = datetime.fromisoformat(campaign.deadline_at).astimezone(
        timezone.utc
    )
    category_counts = Counter(case.category for case in campaign.cases)
    reviewed_count = sum(
        effective_status(case) == "approved" for case in campaign.cases
    )
    rejected_count = sum(
        effective_status(case) == "rejected" for case in campaign.cases
    )
    semantic_passes = 0
    plan_passes = 0
    end_to_end_passes = 0
    critical_underprocessing = 0
    results = []

    for case in campaign.cases:
        expected = effective_expected(case)
        routed = route(case.input_text)
        packet = routed.packet
        plan = routed.plan
        shadow = run_core_shadow(case.input_text, packet, plan)
        semantic_pass = packet.primary_intent == expected["intent"]
        plan_pass = (
            plan.processing_class == expected["processing_class"]
            and plan.core_mode == expected["core_mode"]
        )
        end_to_end_pass = semantic_pass and plan_pass
        underprocessed = (
            case.critical_underprocessing and not end_to_end_pass
        )
        semantic_passes += semantic_pass
        plan_passes += plan_pass
        end_to_end_passes += end_to_end_pass
        critical_underprocessing += underprocessed
        vertical = shadow.pipeline_state.get("vertical_stack")
        results.append(
            {
                "id": case.case_id,
                "batch": case.batch,
                "category": case.category,
                "review_status": effective_status(case),
                "expected": expected,
                "actual": {
                    "intent": packet.primary_intent,
                    "processing_class": plan.processing_class,
                    "core_mode": plan.core_mode,
                    "operations": list(packet.operations),
                    "confidence": packet.confidence,
                    "reason_codes": list(plan.reason_codes),
                    "decided_by": routed.trace.get("decided_by"),
                    "intent_margin": routed.trace.get("intent_margin"),
                    "vertical_execution_order": (
                        vertical["execution_order"] if vertical else None
                    ),
                },
                "checks": {
                    "semantic_intent": semantic_pass,
                    "processing_plan": plan_pass,
                    "end_to_end": end_to_end_pass,
                    "critical_underprocessing": underprocessed,
                },
            }
        )

    case_count = len(campaign.cases)
    accuracy = _ratio(end_to_end_passes, case_count)
    target_reached = case_count >= campaign.target_case_count
    deadline_reached = now >= deadline
    coverage = {
        category: {
            "count": category_counts[category],
            "required": required,
            "met": category_counts[category] >= required,
        }
        for category, required in campaign.required_categories.items()
    }
    coverage_met = all(item["met"] for item in coverage.values())
    review_gate_met = reviewed_count >= campaign.policy.min_reviewed_cases
    accuracy_gate_met = (
        accuracy >= campaign.policy.min_end_to_end_accuracy
    )
    critical_gate_met = (
        critical_underprocessing
        <= campaign.policy.max_critical_underprocessing
    )
    collection_stop_reached = target_reached or deadline_reached
    eligible = (
        collection_stop_reached
        and coverage_met
        and review_gate_met
        and accuracy_gate_met
        and critical_gate_met
    )

    visible_benchmark = json.loads(
        BENCHMARK_PATH.read_text(encoding="utf-8")
    )
    visible_texts = {
        case["input"]
        for case in visible_benchmark["cases"]
        if case["split"] in {"train", "validation"}
    }
    overlap = sorted(
        visible_texts & {case.input_text for case in campaign.cases}
    )

    report = {
        "schema_version": "conversation-accumulation-report.v1",
        "generated_at": now.isoformat(),
        "campaign_id": campaign.campaign_id,
        "candidate": campaign.candidate.as_dict(),
        "evaluation_adapter": {
            "entrypoint": "semantic_routing.route",
            "version": ADAPTER_VERSION,
            "intent_model_path": str(
                DEFAULT_INTENT_MODEL_PATH.relative_to(ROOT)
            ),
            "intent_model_sha256": _sha256(DEFAULT_INTENT_MODEL_PATH),
        },
        "active_sealed_v2_read": False,
        "collection": {
            "status": campaign.status,
            "case_count": case_count,
            "target_case_count": campaign.target_case_count,
            "target_reached": target_reached,
            "deadline_at": campaign.deadline_at,
            "deadline_reached": deadline_reached,
            "collection_stop_reached": collection_stop_reached,
            "reviewed_count": reviewed_count,
            "rejected_count": rejected_count,
            "required_reviewed_count": (
                campaign.policy.min_reviewed_cases
            ),
            "coverage": coverage,
            "coverage_met": coverage_met,
        },
        "measurements": {
            "semantic_intent_accuracy": _ratio(
                semantic_passes,
                case_count,
            ),
            "processing_plan_accuracy": _ratio(
                plan_passes,
                case_count,
            ),
            "end_to_end_route_accuracy": accuracy,
            "passed": end_to_end_passes,
            "failed": case_count - end_to_end_passes,
            "critical_underprocessing": critical_underprocessing,
        },
        "gates": {
            "review_gate_met": review_gate_met,
            "accuracy_gate_met": accuracy_gate_met,
            "critical_underprocessing_gate_met": critical_gate_met,
            "visible_benchmark_overlap_count": len(overlap),
            "visible_benchmark_overlap": overlap,
            "eligible_for_sealed_v2_measurement": eligible,
        },
        "results": results,
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
