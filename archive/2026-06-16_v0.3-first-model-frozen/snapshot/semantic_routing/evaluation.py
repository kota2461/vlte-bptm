"""Evaluation for Pattern Language Model adapters."""

from collections import Counter
from typing import Any, Callable, Dict, Sequence

from .benchmark import PLMBenchmarkCase
from .semantic_packet import INTENTS, SemanticPacket


Extractor = Callable[[str], SemanticPacket]
CRITICAL_SIGNALS = (
    "missing_required_information",
    "contains_unverified_claims",
    "requires_current_information",
    "multiple_intents",
)


def _safe_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def evaluate_plm_extractor(
    cases: Sequence[PLMBenchmarkCase],
    extractor: Extractor,
) -> Dict[str, Any]:
    if not cases:
        raise ValueError("at least one PLM benchmark case is required")

    confusion = {
        expected: {predicted: 0 for predicted in INTENTS}
        for expected in INTENTS
    }
    signal_tp = Counter()
    signal_fn = Counter()
    constraint_exact = 0
    operation_exact = 0
    risk_exact = 0
    evidence_valid = 0
    evidence_total = 0
    valid_packets = 0
    errors = []

    for case in cases:
        try:
            packet = extractor(case.input_text)
        except Exception as error:
            errors.append(
                {
                    "id": case.case_id,
                    "kind": "adapter_error",
                    "detail": str(error),
                }
            )
            continue
        valid_packets += 1
        expected = case.expected
        confusion[expected.primary_intent][packet.primary_intent] += 1

        predicted_state = packet.information_state.as_dict()
        expected_state = expected.as_dict()["information_state"]
        for signal in CRITICAL_SIGNALS:
            if expected_state[signal]:
                if predicted_state[signal]:
                    signal_tp[signal] += 1
                else:
                    signal_fn[signal] += 1

        predicted_constraints = packet.constraints.as_dict()
        expected_constraints = expected.as_dict()["constraints"]
        predicted_risk = packet.risk.as_dict()
        expected_risk = expected.as_dict()["risk"]
        constraint_exact += predicted_constraints == expected_constraints
        operation_exact += tuple(packet.operations) == expected.operations
        risk_exact += predicted_risk == expected_risk

        for span in packet.evidence:
            evidence_total += 1
            if 0 <= span.start < span.end <= len(case.input_text):
                evidence_valid += 1

        mismatch_fields = []
        if packet.primary_intent != expected.primary_intent:
            mismatch_fields.append("primary_intent")
        if predicted_state != expected_state:
            mismatch_fields.append("information_state")
        if predicted_constraints != expected_constraints:
            mismatch_fields.append("constraints")
        if predicted_risk != expected_risk:
            mismatch_fields.append("risk")
        if tuple(packet.operations) != expected.operations:
            mismatch_fields.append("operations")
        if mismatch_fields:
            errors.append(
                {
                    "id": case.case_id,
                    "kind": "mismatch",
                    "fields": mismatch_fields,
                    "expected_intent": expected.primary_intent,
                    "predicted_intent": packet.primary_intent,
                }
            )

    per_intent = {}
    f1_values = []
    correct = 0
    for intent in INTENTS:
        tp = confusion[intent][intent]
        correct += tp
        support = sum(confusion[intent].values())
        predicted_count = sum(
            confusion[expected][intent] for expected in INTENTS
        )
        precision = _safe_ratio(tp, predicted_count)
        recall = _safe_ratio(tp, support)
        f1 = (
            round(2 * precision * recall / (precision + recall), 6)
            if precision + recall
            else 0.0
        )
        if support:
            f1_values.append(f1)
        per_intent[intent] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    signal_metrics = {}
    total_signal_tp = 0
    total_signal_expected = 0
    for signal in CRITICAL_SIGNALS:
        tp = signal_tp[signal]
        expected_count = tp + signal_fn[signal]
        total_signal_tp += tp
        total_signal_expected += expected_count
        signal_metrics[signal] = {
            "recall": _safe_ratio(tp, expected_count),
            "support": expected_count,
        }

    count = len(cases)
    return {
        "schema_version": "pattern-language-evaluation.v1",
        "case_count": count,
        "valid_packet_rate": _safe_ratio(valid_packets, count),
        "intent_accuracy": _safe_ratio(correct, count),
        "intent_macro_f1": round(
            sum(f1_values) / len(f1_values),
            6,
        ),
        "per_intent": per_intent,
        "critical_signal_recall": _safe_ratio(
            total_signal_tp,
            total_signal_expected,
        ),
        "critical_signals": signal_metrics,
        "constraint_exact_match": _safe_ratio(constraint_exact, count),
        "operation_exact_match": _safe_ratio(operation_exact, count),
        "risk_exact_match": _safe_ratio(risk_exact, count),
        "evidence_offset_validity": _safe_ratio(
            evidence_valid,
            evidence_total,
        )
        if evidence_total
        else 1.0,
        "confusion": confusion,
        "errors": errors,
    }
