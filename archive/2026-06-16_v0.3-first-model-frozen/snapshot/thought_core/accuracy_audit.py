import argparse
import json
import math
import sqlite3
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from pattern_learning.trainer import RouterModel

from .pipeline import process


RESPONSE_ACCURACY_AUDIT_SCHEMA_VERSION = "response-accuracy-audit.v1"
DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def wilson_interval(
    successes: int,
    count: int,
    confidence: float = 0.95,
) -> Dict[str, float]:
    if (
        isinstance(successes, bool)
        or isinstance(count, bool)
        or not isinstance(successes, int)
        or not isinstance(count, int)
        or count <= 0
        or not 0 <= successes <= count
    ):
        raise ValueError("Wilson interval requires 0 <= successes <= count")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    z = NormalDist().inv_cdf((1.0 + confidence) / 2.0)
    rate = successes / count
    denominator = 1.0 + z * z / count
    center = (rate + z * z / (2.0 * count)) / denominator
    half = (
        z
        * math.sqrt(
            rate * (1.0 - rate) / count
            + z * z / (4.0 * count * count)
        )
        / denominator
    )
    return {
        "confidence": confidence,
        "lower": round(max(0.0, center - half), 6),
        "upper": round(min(1.0, center + half), 6),
    }


def _classification_metrics(
    cases: Sequence[Mapping[str, Any]],
    predict: Callable[[str], str],
) -> Dict[str, Any]:
    if not cases:
        raise ValueError("accuracy audit requires at least one case")
    expected_labels = [
        case.get("route", case.get("expected_mode")) for case in cases
    ]
    if any(not isinstance(label, str) or not label for label in expected_labels):
        raise ValueError("accuracy audit cases require an expected route")
    labels = sorted(set(expected_labels))
    confusion = {
        expected: {predicted: 0 for predicted in labels}
        for expected in labels
    }
    correct = 0
    misses = []
    for case, expected in zip(cases, expected_labels):
        text = case.get("input")
        if not isinstance(text, str):
            raise ValueError("accuracy audit cases require string input")
        predicted = predict(text)
        if predicted not in confusion[expected]:
            for row in confusion.values():
                row.setdefault(predicted, 0)
        confusion[expected][predicted] += 1
        if predicted == expected:
            correct += 1
        else:
            misses.append(
                {
                    "name": case.get("name", ""),
                    "expected": expected,
                    "predicted": predicted,
                }
            )
    per_route = {}
    supported_f1 = []
    recalls = []
    all_predicted_labels = sorted(
        set(labels)
        | {
            predicted
            for row in confusion.values()
            for predicted in row
        }
    )
    for label in labels:
        true_positive = confusion[label].get(label, 0)
        support = sum(confusion[label].values())
        predicted_count = sum(
            confusion[expected].get(label, 0) for expected in labels
        )
        precision = (
            true_positive / predicted_count if predicted_count else 0.0
        )
        recall = true_positive / support if support else 0.0
        f1 = (
            2.0 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        per_route[label] = {
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "support": support,
        }
        supported_f1.append(f1)
        recalls.append(recall)
    count = len(cases)
    return {
        "case_count": count,
        "correct_count": correct,
        "accuracy": round(correct / count, 6),
        "accuracy_interval": wilson_interval(correct, count),
        "macro_f1": round(sum(supported_f1) / len(supported_f1), 6),
        "balanced_accuracy": round(sum(recalls) / len(recalls), 6),
        "per_route": per_route,
        "confusion": {
            expected: {
                predicted: confusion[expected].get(predicted, 0)
                for predicted in all_predicted_labels
            }
            for expected in labels
        },
        "misses": misses,
    }


def _training_overlap(
    database_path: Path,
    cases: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    if not database_path.is_file():
        return {
            "database_available": False,
            "exact_match_count": None,
            "exact_match_rate": None,
            "matched_case_names": [],
        }
    uri = f"{database_path.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        matches = []
        for case in cases:
            row = connection.execute(
                "SELECT route FROM patterns WHERE input_text = ?",
                (case["input"],),
            ).fetchone()
            if row is not None:
                matches.append(
                    {
                        "name": case.get("name", ""),
                        "expected": case.get(
                            "route",
                            case.get("expected_mode"),
                        ),
                        "training_route": row[0],
                    }
                )
        count = len(cases)
        return {
            "database_available": True,
            "exact_match_count": len(matches),
            "exact_match_rate": round(len(matches) / count, 6),
            "matched_case_names": [
                match["name"] for match in matches
            ],
        }
    finally:
        connection.close()


def _non_overlap_metrics(
    database_path: Path,
    cases: Sequence[Mapping[str, Any]],
    predict: Callable[[str], str],
) -> Optional[Dict[str, Any]]:
    if not database_path.is_file():
        return None
    uri = f"{database_path.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        remaining = [
            case
            for case in cases
            if connection.execute(
                "SELECT 1 FROM patterns WHERE input_text = ?",
                (case["input"],),
            ).fetchone()
            is None
        ]
    finally:
        connection.close()
    return _classification_metrics(remaining, predict) if remaining else None


def _abstention_metrics(
    model: RouterModel,
    cases: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    retained = 0
    retained_correct = 0
    abstained = 0
    for case in cases:
        expected = case.get("route", case.get("expected_mode"))
        prediction = model.predict(case["input"])
        if prediction.low_confidence:
            abstained += 1
        else:
            retained += 1
            retained_correct += int(prediction.route == expected)
    count = len(cases)
    return {
        "coverage": round(retained / count, 6),
        "abstention_rate": round(abstained / count, 6),
        "selective_accuracy": (
            round(retained_correct / retained, 6) if retained else None
        ),
    }


def build_response_accuracy_audit(
    *,
    router_fixture_path: Path,
    core_fixture_path: Path,
    model_path: Path,
    database_path: Path,
) -> Dict[str, Any]:
    router_cases = json.loads(
        router_fixture_path.read_text(encoding="utf-8")
    )
    core_cases = json.loads(core_fixture_path.read_text(encoding="utf-8"))
    if not isinstance(router_cases, list) or not isinstance(core_cases, list):
        raise ValueError("accuracy audit fixtures must contain arrays")
    model = RouterModel.load(model_path)
    raw_predict = lambda text: model.predict(text).route
    effective_predict = lambda text: model.predict(text).effective_route
    core_predict = lambda text: process(text).as_dict()["llm_order"]["mode"]

    router_boundary_raw = _classification_metrics(
        router_cases,
        raw_predict,
    )
    router_boundary_effective = _classification_metrics(
        router_cases,
        effective_predict,
    )
    router_on_core = _classification_metrics(core_cases, raw_predict)
    core_acceptance = _classification_metrics(core_cases, core_predict)
    core_on_router = _classification_metrics(router_cases, core_predict)
    router_overlap = _training_overlap(database_path, router_cases)
    core_overlap = _training_overlap(database_path, core_cases)
    model_metrics = model.metadata.get("metrics", {})
    validation_accuracy = model_metrics.get("validation_accuracy")
    validation_count = model_metrics.get("validation_count")
    validation_correct = (
        round(validation_accuracy * validation_count)
        if isinstance(validation_accuracy, (int, float))
        and isinstance(validation_count, int)
        and validation_count > 0
        else None
    )

    return {
        "schema_version": RESPONSE_ACCURACY_AUDIT_SCHEMA_VERSION,
        "scope": {
            "routing_accuracy": True,
            "semantic_answer_correctness": False,
            "reason": (
                "The repository contains route labels and human-entered "
                "reference scores, but no independent raw-answer study."
            ),
        },
        "core_router": {
            "acceptance_regression": core_acceptance,
            "cross_boundary_fixture": core_on_router,
            "acceptance_training_overlap": core_overlap,
        },
        "pattern_router": {
            "boundary_regression_raw": router_boundary_raw,
            "boundary_regression_effective": router_boundary_effective,
            "boundary_abstention": _abstention_metrics(
                model,
                router_cases,
            ),
            "cross_core_fixture_raw": router_on_core,
            "boundary_training_overlap": router_overlap,
            "boundary_non_overlap_raw": _non_overlap_metrics(
                database_path,
                router_cases,
                raw_predict,
            ),
            "core_fixture_non_overlap_raw": _non_overlap_metrics(
                database_path,
                core_cases,
                raw_predict,
            ),
            "measurement_holdout": {
                "case_count": validation_count,
                "accuracy": validation_accuracy,
                "accuracy_interval": (
                    wilson_interval(
                        validation_correct,
                        validation_count,
                    )
                    if validation_correct is not None
                    else None
                ),
                "grouped_by_template_or_source": False,
            },
            "repeated_kfold": {
                "unique_pattern_count": model.metadata.get("sample_count"),
                "accuracy": model_metrics.get("kfold_accuracy"),
                "independent_prediction_count": (
                    model.metadata.get("sample_count")
                ),
                "note": (
                    "Repeated predictions are not independent samples and "
                    "are not used to narrow a confidence interval."
                ),
            },
        },
        "semantic_response_quality": {
            "independent_case_count": 0,
            "status": "not_established",
            "v1_5_reference_case_count": 4,
            "v1_5_reference_is_production_evidence": False,
        },
        "conclusion": {
            "production_response_accuracy_established": False,
            "honest_summary": (
                "Fixed regression accuracy is high, but cross-fixture route "
                "accuracy is inconsistent and semantic answer accuracy has "
                "not been independently measured."
            ),
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit current VLTE-BPTM routing and response evidence"
    )
    parser.add_argument(
        "--router-fixture",
        type=Path,
        default=DEFAULT_ROOT / "tests/fixtures/pattern_router_cases_v1.json",
    )
    parser.add_argument(
        "--core-fixture",
        type=Path,
        default=DEFAULT_ROOT / "tests/fixtures/v1_0a_cases.json",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_ROOT / "build/pattern_router_model.json",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_ROOT / "data/pattern_lab.db",
    )
    args = parser.parse_args(argv)
    try:
        report = build_response_accuracy_audit(
            router_fixture_path=args.router_fixture,
            core_fixture_path=args.core_fixture,
            model_path=args.model,
            database_path=args.database,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
