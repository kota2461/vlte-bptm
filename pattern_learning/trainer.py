import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .database import PatternDatabase
from .tiers import FOUNDATION_TIER, example_tier


MODEL_SCHEMA_VERSION = "pattern-router.model.v1"
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u3040-\u30ff\u3400-\u9fff]+")


def _feature_index(token: str, dimension: int) -> Tuple[int, float]:
    digest = hashlib.blake2b(
        token.encode("utf-8"),
        digest_size=8,
        person=b"ptrn-route-v1",
    ).digest()
    value = int.from_bytes(digest, "big")
    return value % dimension, 1.0 if value & 1 else -1.0


def text_features(text: str, dimension: int) -> Dict[int, float]:
    normalized = re.sub(r"\s+", "", text.casefold())
    tokens = [f"word:{token}" for token in TOKEN_RE.findall(text.casefold())]
    for size in (2, 3, 4):
        tokens.extend(
            f"char{size}:{normalized[index:index + size]}"
            for index in range(max(0, len(normalized) - size + 1))
        )
    counts: Counter[int] = Counter()
    for token in tokens:
        index, sign = _feature_index(token, dimension)
        counts[index] += sign
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {index: value / norm for index, value in counts.items() if value}


@dataclass(frozen=True)
class RouterPrediction:
    route: str
    confidence: float
    scores: Dict[str, float]
    suggested_operators: List[str]
    # Calibration layer (weakness #2). `route` stays the raw argmax so the
    # routing is always observable; `effective_route` is what the abstention
    # policy actually emits — clarify when the prediction is too uncertain.
    effective_route: str = ""
    low_confidence: bool = False
    calibrated_confidence: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "effective_route": self.effective_route or self.route,
            "low_confidence": self.low_confidence,
            "confidence": round(self.confidence, 6),
            "calibrated_confidence": round(self.calibrated_confidence, 6),
            "scores": {
                label: round(score, 6)
                for label, score in sorted(self.scores.items())
            },
            "suggested_operators": self.suggested_operators,
        }


@dataclass
class RouterModel:
    labels: List[str]
    dimension: int
    weights: Dict[str, Dict[int, float]]
    bias: Dict[str, float]
    operator_priors: Dict[str, Dict[str, float]]
    metadata: Dict[str, Any]

    def _score(self, features: Mapping[int, float], label: str) -> float:
        weights = self.weights.get(label, {})
        return self.bias.get(label, 0.0) + sum(
            weights.get(index, 0.0) * value
            for index, value in features.items()
        )

    def predict(self, text: str) -> RouterPrediction:
        features = text_features(text, self.dimension)
        raw_scores = {
            label: self._score(features, label) for label in self.labels
        }
        route = max(self.labels, key=lambda label: (raw_scores[label], label))
        peak = max(raw_scores.values())
        exps = {
            label: math.exp(min(30.0, score - peak))
            for label, score in raw_scores.items()
        }
        total = sum(exps.values()) or 1.0
        confidence = exps[route] / total
        operators = [
            name
            for name, probability in sorted(
                self.operator_priors.get(route, {}).items(),
                key=lambda item: (-item[1], item[0]),
            )
            if probability >= 0.35
        ][:4]
        effective_route, low_confidence, calibrated = self._apply_calibration(
            route, confidence
        )
        return RouterPrediction(
            route=route,
            confidence=confidence,
            scores=raw_scores,
            suggested_operators=operators,
            effective_route=effective_route,
            low_confidence=low_confidence,
            calibrated_confidence=calibrated,
        )

    def _apply_calibration(
        self, route: str, confidence: float
    ) -> Tuple[str, bool, float]:
        """Map a raw prediction through the stored calibration, if any.

        Uncalibrated models (no calibration metadata) pass through unchanged,
        so old model files and tiny test models keep their prior behavior.
        """
        calibration = self.metadata.get("calibration") or {}
        if not calibration:
            return route, False, confidence
        calibrated = confidence
        windows = calibration.get("reliability", [])
        if windows:
            # Equal-frequency bins contain observed min/max values, so adjacent
            # bins can have small numeric gaps. Treat each max as an upper
            # boundary to make the mapping total over the confidence domain.
            calibrated = windows[-1]["accuracy"]
            for window in windows:
                if confidence <= window["max_confidence"]:
                    calibrated = window["accuracy"]
                    break
        threshold = calibration.get("decision_threshold")
        fallback = calibration.get("fallback_route")
        low_confidence = (
            threshold is not None
            and threshold > 0.0
            and confidence <= threshold
            and fallback is not None
            and fallback in self.labels
            and route != fallback
        )
        effective_route = fallback if low_confidence else route
        return effective_route, low_confidence, calibrated

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": MODEL_SCHEMA_VERSION,
            "labels": self.labels,
            "dimension": self.dimension,
            "weights": {
                label: {
                    str(index): round(value, 8)
                    for index, value in sorted(weights.items())
                    if abs(value) >= 1e-9
                }
                for label, weights in self.weights.items()
            },
            "bias": self.bias,
            "operator_priors": self.operator_priors,
            "metadata": self.metadata,
        }

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(self.as_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "RouterModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != MODEL_SCHEMA_VERSION:
            raise ValueError("unsupported router model schema")
        return cls(
            labels=list(payload["labels"]),
            dimension=int(payload["dimension"]),
            weights={
                label: {
                    int(index): float(value)
                    for index, value in weights.items()
                }
                for label, weights in payload["weights"].items()
            },
            bias={
                label: float(value)
                for label, value in payload["bias"].items()
            },
            operator_priors={
                route: {
                    name: float(value) for name, value in priors.items()
                }
                for route, priors in payload["operator_priors"].items()
            },
            metadata=dict(payload["metadata"]),
        )


def _accuracy(
    model: RouterModel,
    examples: Sequence[Dict[str, Any]],
) -> float | None:
    if not examples:
        return None
    correct = sum(
        model.predict(example["input_text"]).route == example["route"]
        for example in examples
    )
    return correct / len(examples)


def _split_examples(
    examples: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for example in examples:
        grouped[example["route"]].append(example)
    train: List[Dict[str, Any]] = []
    validation: List[Dict[str, Any]] = []
    for label_examples in grouped.values():
        ordered = sorted(
            label_examples,
            key=lambda item: hashlib.sha256(
                item["input_text"].encode("utf-8")
            ).hexdigest(),
        )
        if len(ordered) >= 5:
            held_out = max(1, len(ordered) // 5)
            validation.extend(ordered[:held_out])
            train.extend(ordered[held_out:])
        else:
            train.extend(ordered)
    return train, validation


def _train_averaged_weights(
    train_examples: Sequence[Dict[str, Any]],
    labels: Sequence[str],
    dimension: int,
    epochs: int,
    learning_rate: float,
    seed: int,
    foundation_weight: float = 1.0,
) -> Tuple[Dict[str, Dict[int, float]], Dict[str, float]]:
    """Averaged-perceptron fit over a single example set.

    The plain final-weight perceptron is unstable under class imbalance
    because the last few mistakes dominate; averaging smooths that out.
    Factored out so the same routine fits both the held-out *measurement*
    model and the all-data *deployed* model.
    """
    weights: Dict[str, Dict[int, float]] = {
        label: defaultdict(float) for label in labels
    }
    bias = {label: 0.0 for label in labels}
    cumulative_weights: Dict[str, Dict[int, float]] = {
        label: defaultdict(float) for label in labels
    }
    cumulative_bias = {label: 0.0 for label in labels}
    step_counter = 1
    randomizer = random.Random(seed)

    for _epoch in range(epochs):
        shuffled = list(train_examples)
        randomizer.shuffle(shuffled)
        for example in shuffled:
            features = text_features(example["input_text"], dimension)
            scores = {
                label: bias[label]
                + sum(
                    weights[label].get(index, 0.0) * value
                    for index, value in features.items()
                )
                for label in labels
            }
            predicted = max(labels, key=lambda label: (scores[label], label))
            expected = example["route"]
            if predicted != expected:
                quality_weight = max(
                    0.5, min(1.0, example["quality_score"] / 5.0)
                )
                # v0.2.1 tier weighting: OFF by default (1.0 keeps results
                # bit-identical). Foundation protection is the gate's job.
                tier_weight = (
                    foundation_weight
                    if example_tier(example) == FOUNDATION_TIER
                    else 1.0
                )
                step = learning_rate * quality_weight * tier_weight
                for index, value in features.items():
                    weights[expected][index] += step * value
                    weights[predicted][index] -= step * value
                    cumulative_weights[expected][index] += (
                        step_counter * step * value
                    )
                    cumulative_weights[predicted][index] -= (
                        step_counter * step * value
                    )
                bias[expected] += step
                bias[predicted] -= step
                cumulative_bias[expected] += step_counter * step
                cumulative_bias[predicted] -= step_counter * step
            step_counter += 1

    averaged_weights = {
        label: {
            index: value - cumulative_weights[label][index] / step_counter
            for index, value in label_weights.items()
        }
        for label, label_weights in weights.items()
    }
    averaged_bias = {
        label: bias[label] - cumulative_bias[label] / step_counter
        for label in labels
    }
    return averaged_weights, averaged_bias


def _operator_priors(
    examples: Sequence[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    operator_counts: Dict[str, Counter[str]] = defaultdict(Counter)
    route_counts: Counter[str] = Counter()
    for example in examples:
        route_counts[example["route"]] += 1
        operator_counts[example["route"]].update(example["operators"])
    return {
        route: {
            operator: count / route_counts[route]
            for operator, count in counts.items()
        }
        for route, counts in operator_counts.items()
    }


CALIBRATION_FOLDS = 5
CALIBRATION_REPEATS = 5
CALIBRATION_BINS = 6
CALIBRATION_MIN_SAMPLES = 30


def _kfold_points(
    examples: Sequence[Dict[str, Any]],
    labels: Sequence[str],
    dimension: int,
    epochs: int,
    learning_rate: float,
    seed: int,
) -> List[Tuple[bool, float]]:
    """Repeated stratified k-fold (correct?, confidence) pairs.

    A single k-fold is too noisy here: with ~140 samples the worst-confidence
    decile's empirical accuracy swings ~0.35..0.52 purely on fold luck, which
    would make the abstention threshold unstable. Repeating with reshuffled
    folds averages that out. Each pattern is always scored by a model that
    never trained on it, so the pairs stay an honest trust estimate.
    """
    by_route: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for example in examples:
        by_route[example["route"]].append(example)

    points: List[Tuple[bool, float]] = []
    for repeat in range(CALIBRATION_REPEATS):
        randomizer = random.Random(seed + 1009 * (repeat + 1))
        folds: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for route_examples in by_route.values():
            ordered = sorted(
                route_examples,
                key=lambda item: hashlib.sha256(
                    item["input_text"].encode("utf-8")
                ).hexdigest(),
            )
            randomizer.shuffle(ordered)
            for position, example in enumerate(ordered):
                folds[position % CALIBRATION_FOLDS].append(example)
        for fold in range(CALIBRATION_FOLDS):
            held = folds[fold]
            train = [
                example
                for other in range(CALIBRATION_FOLDS)
                if other != fold
                for example in folds[other]
            ]
            if not held or not train:
                continue
            weights, bias = _train_averaged_weights(
                train, labels, dimension, epochs, learning_rate, seed
            )
            fold_model = RouterModel(
                labels=list(labels),
                dimension=dimension,
                weights=weights,
                bias=bias,
                operator_priors={},
                metadata={},
            )
            for example in held:
                prediction = fold_model.predict(example["input_text"])
                points.append(
                    (
                        prediction.route == example["route"],
                        prediction.confidence,
                    )
                )
    return points


def _isotonic_bins(
    accuracies: Sequence[float], counts: Sequence[int]
) -> List[float]:
    """Pool-adjacent-violators isotonic fit -> non-decreasing accuracies.

    Calibrated confidence must rise with raw confidence; a thin noisy tail
    bin (e.g. n=2 at acc 0.5 sitting above 0.9 bins) otherwise produces a
    non-monotonic, misleading mapping. PAVA pools such violators by count.
    """
    blocks: List[List[float]] = []  # [weighted_sum, weight, bin_span]
    for accuracy, count in zip(accuracies, counts):
        blocks.append([accuracy * count, float(count), 1.0])
        while len(blocks) >= 2 and (
            blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]
        ):
            right = blocks.pop()
            left = blocks.pop()
            blocks.append(
                [
                    left[0] + right[0],
                    left[1] + right[1],
                    left[2] + right[2],
                ]
            )
    fitted: List[float] = []
    for weighted_sum, weight, span in blocks:
        fitted.extend([weighted_sum / weight] * int(span))
    return fitted


def _calibrate(
    examples: Sequence[Dict[str, Any]],
    labels: Sequence[str],
    dimension: int,
    epochs: int,
    learning_rate: float,
    seed: int,
) -> Dict[str, Any] | None:
    """Honest reliability table + a stable abstention threshold.

    The threshold is the top of the highest confidence bin whose empirical
    accuracy is still below 0.5. This identifies a candidate abstention region
    where the raw router is more likely wrong than right. Whether clarification
    is actually safer requires separate human or cost-based evaluation.
    Bin-based (not point-argmax) so it is robust to fold noise; recomputed every
    train so it tracks the data.
    """
    if len(examples) < CALIBRATION_MIN_SAMPLES:
        return None

    points = _kfold_points(
        examples, labels, dimension, epochs, learning_rate, seed
    )
    if not points:
        return None

    ordered_points = sorted(points, key=lambda item: item[1])
    total = len(ordered_points)
    bin_size = max(1, total // CALIBRATION_BINS)
    # Equal-frequency bins; a trailing remainder smaller than half a bin is
    # folded into the last bin so it does not form a noisy micro-bin.
    bounds = list(range(0, total, bin_size))
    if len(bounds) > 1 and total - bounds[-1] < bin_size / 2:
        bounds.pop()
    chunks = [
        ordered_points[start:(bounds[i + 1] if i + 1 < len(bounds) else total)]
        for i, start in enumerate(bounds)
    ]
    empirical = [
        sum(1 for correct, _ in chunk if correct) / len(chunk)
        for chunk in chunks
    ]
    calibrated = _isotonic_bins(empirical, [len(chunk) for chunk in chunks])
    reliability: List[Dict[str, float]] = [
        {
            "min_confidence": round(chunk[0][1], 6),
            "max_confidence": round(chunk[-1][1], 6),
            "accuracy": round(fit, 6),
            "empirical_accuracy": round(emp, 6),
            "count": len(chunk),
        }
        for chunk, emp, fit in zip(chunks, empirical, calibrated)
    ]

    # Abstain through the top of any below-0.5 (calibrated) confidence bin.
    threshold = 0.0
    for window in reliability:
        if window["accuracy"] < 0.5:
            threshold = max(threshold, window["max_confidence"])
    abstained = [correct for correct, conf in ordered_points if conf <= threshold]
    retained = [correct for correct, conf in ordered_points if conf > threshold]
    abstained_correct = sum(1 for correct in abstained if correct)
    abstained_wrong = len(abstained) - abstained_correct
    retained_correct = sum(1 for correct in retained if correct)
    selective_accuracy = (
        retained_correct / len(retained) if retained else None
    )

    return {
        "method": (
            "repeated stratified k-fold; histogram reliability; "
            "abstain through the top of any sub-0.5-accuracy confidence bin"
        ),
        "signal": "softmax_confidence",
        "folds": CALIBRATION_FOLDS,
        "repeats": CALIBRATION_REPEATS,
        "points": total,
        "kfold_accuracy": round(
            sum(1 for correct, _ in ordered_points if correct) / total, 6
        ),
        "decision_threshold": round(threshold, 6),
        "abstention_diagnostics": {
            "abstained_count": len(abstained),
            "abstention_rate": round(len(abstained) / total, 6),
            "coverage": round(len(retained) / total, 6),
            "selective_accuracy": (
                round(selective_accuracy, 6)
                if selective_accuracy is not None
                else None
            ),
            "abstained_raw_correct": abstained_correct,
            "abstained_raw_wrong": abstained_wrong,
            "interpretation": (
                "Abstention is a safety action, not a corrected route label. "
                "Its usefulness requires separate human or cost-based review."
            ),
        },
        "fallback_route": "clarify" if "clarify" in labels else None,
        "reliability": reliability,
    }


def train_router(
    database: PatternDatabase,
    output_path: str | Path,
    epochs: int = 24,
    dimension: int = 2048,
    learning_rate: float = 0.35,
    seed: int = 17,
    foundation_weight: float = 1.0,
) -> Dict[str, Any]:
    examples = database.training_examples()
    if len(examples) < 2:
        raise ValueError("at least two approved patterns are required")
    labels = sorted({example["route"] for example in examples})
    if len(labels) < 2:
        raise ValueError("approved patterns must cover at least two routes")

    train, validation = _split_examples(examples)
    operator_priors = _operator_priors(examples)

    # Measurement model: fit on the train split only so the validation
    # accuracy is an honest held-out estimate (never trains on validation).
    measurement_weights, measurement_bias = _train_averaged_weights(
        train, labels, dimension, epochs, learning_rate, seed,
        foundation_weight=foundation_weight,
    )
    measurement_model = RouterModel(
        labels=labels,
        dimension=dimension,
        weights=measurement_weights,
        bias=measurement_bias,
        operator_priors=operator_priors,
        metadata={},
    )
    metrics = {
        "training_accuracy": _accuracy(measurement_model, train),
        "validation_accuracy": _accuracy(measurement_model, validation),
        "validation_count": len(validation),
    }

    # Honest abstention calibration over all data (k-fold; never trains on
    # what it scores). Recomputed each run so the threshold tracks the data.
    calibration = _calibrate(
        examples, labels, dimension, epochs, learning_rate, seed
    )

    # Deployed model: fit on ALL approved patterns. With a small corpus,
    # holding 20% out of the shipped model wastes scarce signal; we measure
    # on the split above but deploy a model that has seen everything.
    deployed_weights, deployed_bias = _train_averaged_weights(
        examples, labels, dimension, epochs, learning_rate, seed,
        foundation_weight=foundation_weight,
    )
    metadata: Dict[str, Any] = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(examples),
        "training_count": len(train),
        "validation_count": len(validation),
        "epochs": epochs,
        "learning_rate": learning_rate,
        "seed": seed,
        "algorithm": "averaged_perceptron",
        "foundation_weight": foundation_weight,
        "source": "human-approved Pattern DB entries only",
        "deployed_on": "all_approved_patterns",
        "measurement_split": "train/validation holdout (metrics only)",
        "confidence_calibrated": calibration is not None,
    }
    if calibration is not None:
        metadata["calibration"] = calibration
    model = RouterModel(
        labels=labels,
        dimension=dimension,
        weights=deployed_weights,
        bias=deployed_bias,
        operator_priors=operator_priors,
        metadata=metadata,
    )
    metrics["deployed_self_accuracy"] = _accuracy(model, examples)
    if calibration is not None:
        metrics["kfold_accuracy"] = calibration["kfold_accuracy"]
        metrics["decision_threshold"] = calibration["decision_threshold"]
    model.metadata["metrics"] = metrics
    model.save(output_path)
    database.record_training_run(
        model_path=str(Path(output_path).resolve()),
        sample_count=len(examples),
        labels=labels,
        metrics=metrics,
        parameters={
            "epochs": epochs,
            "dimension": dimension,
            "learning_rate": learning_rate,
            "seed": seed,
            "foundation_weight": foundation_weight,
        },
    )
    return {
        "model_path": str(Path(output_path).resolve()),
        "sample_count": len(examples),
        "labels": labels,
        "metrics": metrics,
    }
