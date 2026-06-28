"""Learned intent model for the v0.3 hybrid adapter (first deployable model).

A self-contained averaged-perceptron classifier over the 7 adapter intents
(respond/explain/build/verify/summarize/explore/clarify). It is the learned
half of the hybrid: the deterministic markers stay the first pass, and this
model is consulted only on marker no-match, gated by its confidence margin
(see the hybrid merge / `docs/SEMANTIC_ADAPTER_v0_3_design.md` §11).

Features reuse the Pattern Router's `text_features` (hashed char 2/3/4-grams
+ word tokens) — the proven, deterministic, dependency-free encoding. The
averaged perceptron is inlined here so this module owns its own training
(it does not depend on Router-private helpers). Deterministic (fixed seed),
JSON-serialisable, observable.

Discipline: trained ONLY on human-approved, intent-labelled examples; never
on the measurement campaign.
"""

import hashlib
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from pattern_learning.trainer import text_features
from .semantic_packet import INTENTS


INTENT_MODEL_SCHEMA_VERSION = "intent-model.v1"
DEFAULT_DIMENSION = 2048
DEFAULT_EPOCHS = 24
DEFAULT_LEARNING_RATE = 0.35
DEFAULT_SEED = 17
INTENT_CORPUS_QUARANTINE_SCHEMA_VERSION = "intent-corpus-quarantine.v1"


@dataclass(frozen=True)
class IntentPrediction:
    intent: str
    margin: float          # top1 - top2 (confidence for the gate)
    scores: Dict[str, float]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "margin": round(self.margin, 6),
            "scores": {k: round(v, 6) for k, v in sorted(self.scores.items())},
        }


def _averaged_perceptron(
    examples: Sequence[Tuple[str, str]],
    labels: Sequence[str],
    dimension: int,
    epochs: int,
    learning_rate: float,
    seed: int,
) -> Tuple[Dict[str, Dict[int, float]], Dict[str, float]]:
    weights: Dict[str, Dict[int, float]] = {l: defaultdict(float) for l in labels}
    bias = {l: 0.0 for l in labels}
    cum_w: Dict[str, Dict[int, float]] = {l: defaultdict(float) for l in labels}
    cum_b = {l: 0.0 for l in labels}
    step = 1
    rng = random.Random(seed)
    feats_cache = {text: text_features(text, dimension) for text, _ in examples}

    for _ in range(epochs):
        order = list(examples)
        rng.shuffle(order)
        for text, gold in order:
            feats = feats_cache[text]
            scores = {
                l: bias[l] + sum(weights[l].get(i, 0.0) * v
                                 for i, v in feats.items())
                for l in labels
            }
            pred = max(labels, key=lambda l: (scores[l], l))
            if pred != gold:
                for i, v in feats.items():
                    weights[gold][i] += learning_rate * v
                    weights[pred][i] -= learning_rate * v
                    cum_w[gold][i] += step * learning_rate * v
                    cum_w[pred][i] -= step * learning_rate * v
                bias[gold] += learning_rate
                bias[pred] -= learning_rate
                cum_b[gold] += step * learning_rate
                cum_b[pred] -= step * learning_rate
            step += 1

    avg_w = {
        l: {i: w - cum_w[l][i] / step for i, w in wl.items() if w or cum_w[l][i]}
        for l, wl in weights.items()
    }
    avg_b = {l: bias[l] - cum_b[l] / step for l in labels}
    return avg_w, avg_b


@dataclass
class IntentModel:
    labels: List[str]
    dimension: int
    weights: Dict[str, Dict[int, float]]
    bias: Dict[str, float]
    metadata: Dict[str, Any]

    @classmethod
    def train(
        cls,
        examples: Sequence[Mapping[str, str]],
        *,
        dimension: int = DEFAULT_DIMENSION,
        epochs: int = DEFAULT_EPOCHS,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        seed: int = DEFAULT_SEED,
    ) -> "IntentModel":
        pairs = [(e["input"], e["intent"]) for e in examples]
        if len(pairs) < 2:
            raise ValueError("at least two training examples are required")
        unknown = sorted({i for _, i in pairs} - set(INTENTS))
        if unknown:
            raise ValueError(f"unknown intent label: {unknown[0]}")
        labels = sorted({i for _, i in pairs})
        if len(labels) < 2:
            raise ValueError("training data must cover at least two intents")
        weights, bias = _averaged_perceptron(
            pairs, labels, dimension, epochs, learning_rate, seed
        )
        return cls(
            labels=labels,
            dimension=dimension,
            weights=weights,
            bias=bias,
            metadata={
                "schema_version": INTENT_MODEL_SCHEMA_VERSION,
                "algorithm": "averaged_perceptron",
                "sample_count": len(pairs),
                "epochs": epochs,
                "learning_rate": learning_rate,
                "seed": seed,
                "source": "human-approved intent corpus only",
            },
        )

    def predict(self, text: str) -> IntentPrediction:
        feats = text_features(text, self.dimension)
        scores = {
            label: self.bias.get(label, 0.0)
            + sum(self.weights.get(label, {}).get(i, 0.0) * v
                  for i, v in feats.items())
            for label in self.labels
        }
        ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        top_intent, top_score = ordered[0]
        margin = top_score - ordered[1][1] if len(ordered) > 1 else top_score
        return IntentPrediction(intent=top_intent, margin=margin, scores=scores)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": INTENT_MODEL_SCHEMA_VERSION,
            "labels": self.labels,
            "dimension": self.dimension,
            "weights": {
                label: {str(i): round(w, 8) for i, w in sorted(wl.items())
                        if abs(w) >= 1e-9}
                for label, wl in self.weights.items()
            },
            "bias": self.bias,
            "metadata": self.metadata,
        }

    def save(self, path: str | Path) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(self.as_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "IntentModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != INTENT_MODEL_SCHEMA_VERSION:
            raise ValueError("unsupported intent model schema")
        return cls(
            labels=list(payload["labels"]),
            dimension=int(payload["dimension"]),
            weights={
                label: {int(i): float(w) for i, w in wl.items()}
                for label, wl in payload["weights"].items()
            },
            bias={label: float(v) for label, v in payload["bias"].items()},
            metadata=dict(payload["metadata"]),
        )


def _active_quarantine_payload(path: Path) -> Dict[str, Any] | None:
    quarantine_path = path.with_name("intent_training_corpus_quarantine_v1.json")
    if not quarantine_path.exists():
        return None
    payload = json.loads(quarantine_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != INTENT_CORPUS_QUARANTINE_SCHEMA_VERSION:
        raise ValueError("unsupported intent corpus quarantine schema")
    if payload.get("status") != "active":
        return None
    return payload


def _active_quarantine_indices(path: Path) -> set[int]:
    payload = _active_quarantine_payload(path)
    if payload is None:
        return set()
    indices: set[int] = set()
    for entry in payload.get("entries", []):
        index = entry.get("corpus_index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 1:
            raise ValueError("quarantine entry corpus_index must be positive int")
        indices.add(index)
    return indices


def _verify_quarantine_entries(
    payload: Mapping[str, Any] | None,
    examples: Sequence[Mapping[str, Any]],
) -> None:
    if payload is None:
        return
    for entry in payload.get("entries", []):
        index = int(entry["corpus_index"])
        if index > len(examples):
            raise ValueError("quarantine entry corpus_index is out of range")
        example = examples[index - 1]
        expected_hash = entry.get("input_sha256")
        actual_hash = hashlib.sha256(
            str(example["input"]).encode("utf-8")
        ).hexdigest()
        if expected_hash != actual_hash:
            raise ValueError(
                f"quarantine entry hash mismatch at corpus_index {index}"
            )


def load_intent_corpus(path: str | Path) -> List[Dict[str, Any]]:
    """Load approved, non-quarantined examples from an intent corpus."""

    corpus_path = Path(path)
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "intent-training-corpus.v1":
        raise ValueError("unsupported intent training corpus schema")
    quarantine_payload = _active_quarantine_payload(corpus_path)
    quarantined_indices = _active_quarantine_indices(corpus_path)
    _verify_quarantine_entries(quarantine_payload, payload["examples"])
    return [
        e
        for index, e in enumerate(payload["examples"], start=1)
        if e["review_status"] == "approved" and index not in quarantined_indices
    ]
