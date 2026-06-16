from typing import Any, Dict, Sequence

from .trainer import RouterModel


def evaluate_router(
    model: RouterModel,
    cases: Sequence[Dict[str, str]],
) -> Dict[str, Any]:
    """Evaluate raw routing and abstention behavior as separate quantities."""

    if not cases:
        raise ValueError("at least one evaluation case is required")

    labels = sorted(
        set(model.labels)
        | {case["route"] for case in cases}
    )
    confusion = {
        expected: {predicted: 0 for predicted in labels}
        for expected in labels
    }
    raw_correct = 0
    effective_correct = 0
    retained_correct = 0
    retained_count = 0
    abstained_count = 0
    misses = []

    for case in cases:
        expected = case["route"]
        prediction = model.predict(case["input"])
        confusion[expected][prediction.route] += 1
        is_raw_correct = prediction.route == expected
        raw_correct += is_raw_correct
        effective_correct += prediction.effective_route == expected
        if prediction.low_confidence:
            abstained_count += 1
        else:
            retained_count += 1
            retained_correct += is_raw_correct
        if not is_raw_correct:
            misses.append(
                {
                    "name": case.get("name", ""),
                    "expected": expected,
                    "predicted": prediction.route,
                    "effective_route": prediction.effective_route,
                    "confidence": round(prediction.confidence, 6),
                    "input": case["input"],
                }
            )

    per_route: Dict[str, Dict[str, float | int]] = {}
    for label in labels:
        true_positive = confusion[label][label]
        support = sum(confusion[label].values())
        predicted_count = sum(confusion[expected][label] for expected in labels)
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / support if support else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        per_route[label] = {
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "support": support,
        }

    count = len(cases)
    supported_f1 = [
        metrics["f1"]
        for metrics in per_route.values()
        if metrics["support"] > 0
    ]
    return {
        "case_count": count,
        "raw_accuracy": round(raw_correct / count, 6),
        # This is reported for observability only. Falling back to clarify is
        # a safety action and must not be described as a corrected label.
        "effective_label_accuracy": round(effective_correct / count, 6),
        "abstention_rate": round(abstained_count / count, 6),
        "coverage": round(retained_count / count, 6),
        "selective_accuracy": (
            round(retained_correct / retained_count, 6)
            if retained_count
            else None
        ),
        "macro_f1": round(sum(supported_f1) / len(supported_f1), 6),
        "per_route": per_route,
        "confusion": confusion,
        "misses": misses,
    }
