import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Mapping, Optional, Sequence


RUNTIME_EVALUATION_FIXTURE_SCHEMA_VERSION = (
    "runtime-evaluation-fixture.v1"
)
RUNTIME_EVALUATION_REPORT_SCHEMA_VERSION = (
    "runtime-evaluation-report.v1"
)
RUBRIC_DIMENSIONS = (
    "correctness",
    "relevance",
    "completeness",
    "assumption_control",
    "clarity",
)
PROCESSING_MODES = ("horizontal", "vertical", "hybrid")
_CANDIDATE_FIELDS = {
    "candidate_id",
    "rubric_scores",
    "latency_ms",
    "dispatch_count",
    "estimated_cost_units",
    "fallback",
}
_FIXTURE_FIELDS = {
    "schema_version",
    "rubric",
    "cost_unit",
    "cases",
    "hybrid_winner_reviews",
}
_RUBRIC_FIELDS = {
    "dimensions",
    "minimum_score",
    "maximum_score",
    "blind",
}


def _finite_number(value: Any, field_name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{field_name} must be a finite number")
    return float(value)


def _validate_rubric(payload: Any) -> None:
    if not isinstance(payload, dict) or set(payload) != _RUBRIC_FIELDS:
        raise ValueError("runtime evaluation rubric must be an object")
    if payload.get("dimensions") != list(RUBRIC_DIMENSIONS):
        raise ValueError("runtime evaluation rubric dimensions do not match")
    if payload.get("minimum_score") != 1:
        raise ValueError("runtime rubric minimum_score must be 1")
    if payload.get("maximum_score") != 5:
        raise ValueError("runtime rubric maximum_score must be 5")
    if payload.get("blind") is not True:
        raise ValueError("runtime evaluation rubric must be blind")


def _candidate_score(candidate: Mapping[str, Any]) -> float:
    return mean(candidate["rubric_scores"].values())


def _validate_candidate(candidate: Any) -> Dict[str, Any]:
    if not isinstance(candidate, dict) or set(candidate) != _CANDIDATE_FIELDS:
        raise ValueError("runtime evaluation candidate fields do not match")
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError("candidate_id must be a non-empty string")
    scores = candidate.get("rubric_scores")
    if not isinstance(scores, dict) or set(scores) != set(RUBRIC_DIMENSIONS):
        raise ValueError("candidate rubric scores do not match dimensions")
    clean_scores = {}
    for dimension in RUBRIC_DIMENSIONS:
        score = _finite_number(
            scores[dimension],
            f"rubric_scores.{dimension}",
        )
        if not 1.0 <= score <= 5.0:
            raise ValueError("runtime rubric scores must be in [1, 5]")
        clean_scores[dimension] = score
    latency_ms = _finite_number(candidate.get("latency_ms"), "latency_ms")
    if latency_ms < 0.0:
        raise ValueError("latency_ms must be non-negative")
    dispatch_count = candidate.get("dispatch_count")
    if (
        isinstance(dispatch_count, bool)
        or not isinstance(dispatch_count, int)
        or dispatch_count <= 0
    ):
        raise ValueError("dispatch_count must be a positive integer")
    cost = _finite_number(
        candidate.get("estimated_cost_units"),
        "estimated_cost_units",
    )
    if cost < 0.0:
        raise ValueError("estimated_cost_units must be non-negative")
    if not isinstance(candidate.get("fallback"), bool):
        raise ValueError("fallback must be boolean")
    return {
        **candidate,
        "rubric_scores": clean_scores,
        "latency_ms": latency_ms,
        "estimated_cost_units": cost,
    }


def evaluate_runtime_fixture(payload: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("runtime evaluation fixture must be an object")
    if set(payload) != _FIXTURE_FIELDS:
        raise ValueError("runtime evaluation fixture fields do not match")
    if (
        payload.get("schema_version")
        != RUNTIME_EVALUATION_FIXTURE_SCHEMA_VERSION
    ):
        raise ValueError("unsupported runtime evaluation fixture schema")
    _validate_rubric(payload.get("rubric"))
    cost_unit = payload.get("cost_unit")
    if not isinstance(cost_unit, str) or not cost_unit:
        raise ValueError("cost_unit must be a non-empty string")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("runtime evaluation requires at least one case")

    by_mode = {mode: [] for mode in PROCESSING_MODES}
    case_results = []
    rubric_agreements = 0
    runtime_agreements = 0
    seen_case_ids = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "case_id",
            "candidates",
            "reveal",
            "human_preferred_candidate_id",
            "runtime_selected_candidate_id",
        }:
            raise ValueError("runtime evaluation case fields do not match")
        case_id = case.get("case_id")
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in seen_case_ids
        ):
            raise ValueError("case_id values must be unique non-empty strings")
        seen_case_ids.add(case_id)
        raw_candidates = case.get("candidates")
        if not isinstance(raw_candidates, list) or len(raw_candidates) != 3:
            raise ValueError("each case must contain exactly three candidates")
        candidates = [_validate_candidate(item) for item in raw_candidates]
        candidate_ids = [item["candidate_id"] for item in candidates]
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("candidate_id values must be unique per case")
        reveal = case.get("reveal")
        if (
            not isinstance(reveal, dict)
            or set(reveal) != set(candidate_ids)
            or set(reveal.values()) != set(PROCESSING_MODES)
        ):
            raise ValueError(
                "case reveal must map candidates to all processing modes"
            )
        human_preferred = case.get("human_preferred_candidate_id")
        runtime_selected = case.get("runtime_selected_candidate_id")
        if human_preferred not in reveal or runtime_selected not in reveal:
            raise ValueError("case selections must reference candidates")

        scored = []
        for candidate in candidates:
            mode = reveal[candidate["candidate_id"]]
            quality_score = _candidate_score(candidate)
            record = {
                **candidate,
                "mode": mode,
                "quality_score": quality_score,
            }
            by_mode[mode].append(record)
            scored.append(record)
        rubric_winner = min(
            scored,
            key=lambda item: (
                -item["quality_score"],
                item["candidate_id"],
            ),
        )["candidate_id"]
        rubric_matches = rubric_winner == human_preferred
        runtime_matches = runtime_selected == human_preferred
        rubric_agreements += int(rubric_matches)
        runtime_agreements += int(runtime_matches)
        case_results.append(
            {
                "case_id": case_id,
                "rubric_winner_candidate_id": rubric_winner,
                "human_preferred_candidate_id": human_preferred,
                "runtime_selected_candidate_id": runtime_selected,
                "rubric_winner_matches_human": rubric_matches,
                "runtime_selection_matches_human": runtime_matches,
            }
        )

    mode_metrics = {}
    for mode, records in by_mode.items():
        if len(records) != len(cases):
            raise ValueError("every case must contain every processing mode")
        mode_metrics[mode] = {
            "case_count": len(records),
            "quality_score_mean": round(
                mean(record["quality_score"] for record in records),
                6,
            ),
            "latency_ms_mean": round(
                mean(record["latency_ms"] for record in records),
                3,
            ),
            "dispatch_count_mean": round(
                mean(record["dispatch_count"] for record in records),
                6,
            ),
            "estimated_cost_units_mean": round(
                mean(
                    record["estimated_cost_units"]
                    for record in records
                ),
                6,
            ),
            "fallback_rate": round(
                mean(int(record["fallback"]) for record in records),
                6,
            ),
        }

    reviews = payload.get("hybrid_winner_reviews")
    if not isinstance(reviews, list) or not reviews:
        raise ValueError("hybrid_winner_reviews must be a non-empty list")
    review_matches = 0
    seen_review_ids = set()
    review_results = []
    for review in reviews:
        if not isinstance(review, dict) or set(review) != {
            "review_id",
            "runtime_winner_candidate_id",
            "human_preferred_candidate_id",
        }:
            raise ValueError("hybrid winner review fields do not match")
        review_id = review.get("review_id")
        runtime_winner = review.get("runtime_winner_candidate_id")
        human_winner = review.get("human_preferred_candidate_id")
        if (
            not isinstance(review_id, str)
            or not review_id
            or review_id in seen_review_ids
            or not isinstance(runtime_winner, str)
            or not runtime_winner
            or not isinstance(human_winner, str)
            or not human_winner
        ):
            raise ValueError("hybrid winner review values are invalid")
        seen_review_ids.add(review_id)
        matches = runtime_winner == human_winner
        review_matches += int(matches)
        review_results.append(
            {
                "review_id": review_id,
                "matches_human": matches,
            }
        )

    horizontal_quality = mode_metrics["horizontal"]["quality_score_mean"]
    hybrid_quality = mode_metrics["hybrid"]["quality_score_mean"]
    return {
        "schema_version": RUNTIME_EVALUATION_REPORT_SCHEMA_VERSION,
        "fixture_schema_version": (
            RUNTIME_EVALUATION_FIXTURE_SCHEMA_VERSION
        ),
        "case_count": len(cases),
        "cost_unit": cost_unit,
        "privacy": {
            "raw_output_stored": False,
            "automatic_learning": False,
            "candidate_mode_hidden_during_scoring": True,
        },
        "mode_metrics": mode_metrics,
        "comparisons": {
            "hybrid_quality_gain_over_horizontal": round(
                hybrid_quality - horizontal_quality,
                6,
            ),
            "rubric_winner_human_agreement": round(
                rubric_agreements / len(cases),
                6,
            ),
            "runtime_selection_human_agreement": round(
                runtime_agreements / len(cases),
                6,
            ),
            "hybrid_stack_winner_human_agreement": round(
                review_matches / len(reviews),
                6,
            ),
        },
        "case_results": case_results,
        "hybrid_winner_review_results": review_results,
        "interpretation": (
            "This report aggregates human-entered blind rubric scores and "
            "operational measurements. The bundled fixture validates the "
            "evaluation contract; it is not independent production evidence."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate blinded VLTE-BPTM runtime measurements"
    )
    parser.add_argument(
        "--input-file",
        required=True,
        type=Path,
        help="Versioned runtime evaluation fixture",
    )
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input_file.read_text(encoding="utf-8"))
        report = evaluate_runtime_fixture(payload)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
