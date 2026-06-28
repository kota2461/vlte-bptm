"""Experimental channel model for Thought Color Code v0.1."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence, Tuple

from .code import (
    INTENSITY_LABELS,
    OPERATION_LABELS,
    STANCE_LABELS,
    ThoughtColorCode,
)
from .paths import ensure_repo_on_path

ensure_repo_on_path()

from pattern_learning.trainer import text_features  # noqa: E402
from semantic_routing.benchmark import ExpectedSemantics, PLMBenchmarkCase  # noqa: E402
from semantic_routing.semantic_packet import (  # noqa: E402
    AdapterInfo,
    EvidenceSpan,
    InformationState,
    IntentCandidate,
    RiskSignal,
    SemanticConstraints,
    SemanticPacket,
    request_digest,
)


INTENT_BASE = {
    "respond": 0,
    "explain": 1,
    "clarify": 2,
    "build": 3,
    "verify": 4,
    "summarize": 5,
    "explore": 6,
}
BASE_INTENT = {value: key for key, value in INTENT_BASE.items()}

OPERATION_CHANNEL_BY_INTENT = {
    "respond": "respond",
    "explain": "reason",
    "clarify": "route",
    "build": "generate",
    "verify": "verify",
    "summarize": "remember",
    "explore": "compare",
}
INTENT_BY_OPERATION_CHANNEL = {
    "respond": "respond",
    "reason": "explain",
    "route": "clarify",
    "generate": "build",
    "verify": "verify",
    "remember": "summarize",
    "compare": "explore",
    "reserve": "respond",
}
RISK_TO_INTENSITY = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "hold",
}
INTENSITY_TO_RISK = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "hold": "critical",
}


def expected_to_code(expected: ExpectedSemantics) -> ThoughtColorCode:
    """Map approved semantic labels into the layered code space."""

    if expected.missing_required_information:
        stance = "clarify"
    elif expected.requires_current_information:
        stance = "reserve"
    elif expected.contains_unverified_claims:
        stance = "challenge"
    elif expected.multiple_intents:
        stance = "explore"
    else:
        stance = "neutral"

    return ThoughtColorCode.from_labels(
        base_id=INTENT_BASE[expected.primary_intent],
        stance=stance,
        operation=OPERATION_CHANNEL_BY_INTENT[expected.primary_intent],
        intensity=RISK_TO_INTENSITY[expected.risk_level],
    )


def _dot(left: Mapping[int, float], right: Mapping[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(index, 0.0) for index, value in left.items())


def _normalize(features: Mapping[int, float]) -> Dict[int, float]:
    norm = math.sqrt(sum(value * value for value in features.values())) or 1.0
    return {index: value / norm for index, value in features.items() if value}


@dataclass(frozen=True)
class CentroidClassifier:
    labels: Tuple[int, ...]
    dimension: int
    centroids: Mapping[int, Mapping[int, float]]
    default_label: int

    @classmethod
    def train(
        cls,
        examples: Sequence[Tuple[str, int]],
        *,
        dimension: int = 2048,
    ) -> "CentroidClassifier":
        if not examples:
            raise ValueError("at least one training example is required")
        sums: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        counts: Counter[int] = Counter()
        for text, label in examples:
            counts[label] += 1
            for index, value in text_features(text, dimension).items():
                sums[label][index] += value
        centroids = {
            label: _normalize(
                {
                    index: value / counts[label]
                    for index, value in features.items()
                }
            )
            for label, features in sums.items()
        }
        labels = tuple(sorted(counts))
        default_label = counts.most_common(1)[0][0]
        return cls(
            labels=labels,
            dimension=dimension,
            centroids=centroids,
            default_label=default_label,
        )

    def predict(self, text: str) -> int:
        features = text_features(text, self.dimension)
        if not self.centroids:
            return self.default_label
        return max(
            self.labels,
            key=lambda label: (
                _dot(features, self.centroids[label]),
                -label,
            ),
        )


@dataclass(frozen=True)
class TrainingPrototype:
    code: ThoughtColorCode
    expected: ExpectedSemantics


@dataclass(frozen=True)
class LayeredThoughtColorExtractor:
    """Predicts ThoughtColor channels and decodes them to SemanticPacket."""

    base_model: CentroidClassifier
    stance_model: CentroidClassifier
    operation_model: CentroidClassifier
    intensity_model: CentroidClassifier
    prototypes: Tuple[TrainingPrototype, ...]

    @classmethod
    def train(
        cls,
        cases: Sequence[PLMBenchmarkCase],
        *,
        dimension: int = 2048,
    ) -> "LayeredThoughtColorExtractor":
        if not cases:
            raise ValueError("at least one training case is required")
        rows = [(case.input_text, expected_to_code(case.expected)) for case in cases]
        return cls(
            base_model=CentroidClassifier.train(
                [(text, code.base_id) for text, code in rows],
                dimension=dimension,
            ),
            stance_model=CentroidClassifier.train(
                [(text, code.stance) for text, code in rows],
                dimension=dimension,
            ),
            operation_model=CentroidClassifier.train(
                [(text, code.operation) for text, code in rows],
                dimension=dimension,
            ),
            intensity_model=CentroidClassifier.train(
                [(text, code.intensity) for text, code in rows],
                dimension=dimension,
            ),
            prototypes=tuple(
                TrainingPrototype(code=code, expected=case.expected)
                for case, (_, code) in zip(cases, rows)
            ),
        )

    def predict_code(self, text: str) -> ThoughtColorCode:
        return ThoughtColorCode(
            base_id=self.base_model.predict(text),
            stance=self.stance_model.predict(text),
            operation=self.operation_model.predict(text),
            intensity=self.intensity_model.predict(text),
        )

    def _prototype_for(self, code: ThoughtColorCode) -> ExpectedSemantics:
        same_base = [
            item
            for item in self.prototypes
            if item.code.base_id == code.base_id
        ]
        candidates = same_base or list(self.prototypes)

        def distance(item: TrainingPrototype) -> Tuple[int, int, int, int]:
            other = item.code
            return (
                int(other.stance != code.stance)
                + int(other.operation != code.operation)
                + int(other.intensity != code.intensity),
                int(other.stance != code.stance),
                int(other.operation != code.operation),
                int(other.intensity != code.intensity),
            )

        return min(candidates, key=distance).expected

    def extract_packet(self, text: str) -> SemanticPacket:
        code = self.predict_code(text)
        prototype = self._prototype_for(code)
        primary_intent = BASE_INTENT.get(code.base_id, prototype.primary_intent)
        operation_label = OPERATION_LABELS[code.operation]
        operation = INTENT_BY_OPERATION_CHANNEL.get(
            operation_label,
            primary_intent,
        )
        stance_label = STANCE_LABELS[code.stance]
        intensity_label = INTENSITY_LABELS[code.intensity]
        risk_level = INTENSITY_TO_RISK[intensity_label]
        risk_flags = (
            prototype.risk_flags
            if prototype.risk_level == risk_level
            else ()
        )
        end = min(len(text), 1)
        evidence = (
            (EvidenceSpan("thought_color_prediction", 0, end),)
            if end
            else ()
        )
        return SemanticPacket(
            request_digest=request_digest(text),
            adapter=AdapterInfo(
                kind="pattern_model",
                version=ThoughtColorCode.SCHEMA_VERSION,
            ),
            language="und",
            intent_candidates=(
                IntentCandidate(intent=primary_intent, confidence=1.0),
            ),
            operations=(operation,),
            information_state=InformationState(
                missing_required_information=stance_label == "clarify",
                contains_unverified_claims=stance_label == "challenge",
                requires_current_information=stance_label == "reserve",
                multiple_intents=stance_label == "explore",
            ),
            constraints=SemanticConstraints(
                response_length=prototype.response_length,
                formats=prototype.formats,
                must=prototype.must,
                must_not=prototype.must_not,
            ),
            risk=RiskSignal(level=risk_level, flags=risk_flags),
            evidence=evidence,
            unknowns=prototype.unknowns,
            conflicts=prototype.conflicts,
            confidence=1.0,
        )

    def extractor(self):
        return self.extract_packet

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "thought-color-channel-model.v0.1",
            "base_labels": list(self.base_model.labels),
            "stance_labels": list(self.stance_model.labels),
            "operation_labels": list(self.operation_model.labels),
            "intensity_labels": list(self.intensity_model.labels),
            "prototype_count": len(self.prototypes),
        }


def evaluate_channel_predictions(
    cases: Sequence[PLMBenchmarkCase],
    model: LayeredThoughtColorExtractor,
) -> Dict[str, Any]:
    if not cases:
        raise ValueError("at least one case is required")
    counts = Counter()
    errors = []
    for case in cases:
        expected = expected_to_code(case.expected)
        predicted = model.predict_code(case.input_text)
        counts["total"] += 1
        counts["base"] += predicted.base_id == expected.base_id
        counts["stance"] += predicted.stance == expected.stance
        counts["operation"] += predicted.operation == expected.operation
        counts["intensity"] += predicted.intensity == expected.intensity
        counts["full"] += predicted.channel_tuple() == expected.channel_tuple()
        if predicted.channel_tuple() != expected.channel_tuple():
            errors.append(
                {
                    "id": case.case_id,
                    "expected": expected.as_dict()["labels"]
                    | {"base_id": expected.base_id},
                    "predicted": predicted.as_dict()["labels"]
                    | {"base_id": predicted.base_id},
                }
            )

    total = counts["total"]
    return {
        "schema_version": "thought-color-channel-evaluation.v0.1",
        "case_count": total,
        "base_accuracy": round(counts["base"] / total, 6),
        "stance_accuracy": round(counts["stance"] / total, 6),
        "operation_accuracy": round(counts["operation"] / total, 6),
        "intensity_accuracy": round(counts["intensity"] / total, 6),
        "full_code_accuracy": round(counts["full"] / total, 6),
        "errors": errors,
    }


