import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import NormalDist, mean, stdev
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .accuracy_audit import wilson_interval
from .runtime_evaluation import PROCESSING_MODES, RUBRIC_DIMENSIONS


INDEPENDENT_STUDY_POLICY_SCHEMA_VERSION = (
    "independent-runtime-study-policy.v1"
)
INDEPENDENT_STUDY_SCHEMA_VERSION = "independent-runtime-study.v1"
INDEPENDENT_STUDY_REPORT_SCHEMA_VERSION = (
    "independent-runtime-study-report.v1"
)
RUNTIME_SELECTION_POLICY_SCHEMA_VERSION = "runtime-selection-policy.v1"
DEFAULT_INDEPENDENT_STUDY_POLICY_PATH = (
    Path(__file__).resolve().parent / "config" / "independent_study.json"
)
DEFAULT_RUNTIME_SELECTION_POLICY_PATH = (
    Path(__file__).resolve().parent
    / "config"
    / "runtime_selection_policy.json"
)
_EVIDENCE_ORIGINS = {
    "synthetic_contract_fixture",
    "independent_blind_collection",
}
_POLICY_FIELDS = {
    "schema_version",
    "minimum_reviewers_per_case",
    "minimum_cases_per_input_class_for_policy",
    "confidence_level",
    "bootstrap_iterations",
    "target_proportion_margin",
    "minimum_quality_gain",
    "maximum_cost_multiplier",
    "maximum_latency_multiplier",
    "retention_days",
    "consent_required",
    "store_raw_input",
    "store_raw_output",
    "automatic_learning",
    "review_gate_required",
    "default_mode",
}
_STUDY_FIELDS = {
    "schema_version",
    "study_id",
    "evidence_origin",
    "collected_at_utc",
    "policy_schema_version",
    "privacy",
    "reviewers",
    "cases",
}
_PRIVACY_FIELDS = {
    "consent_obtained",
    "raw_input_stored",
    "raw_output_stored",
    "automatic_learning",
    "retention_days",
}
_REVIEWER_FIELDS = {
    "reviewer_id",
    "independent_from_generation",
    "consented",
}
_CASE_FIELDS = {
    "case_id",
    "input_class",
    "candidates",
    "reveal",
    "runtime_selected_mode",
    "reviews",
}
_CANDIDATE_FIELDS = {
    "candidate_id",
    "latency_ms",
    "dispatch_count",
    "estimated_cost_units",
    "fallback",
}
_REVIEW_FIELDS = {
    "reviewer_id",
    "preferred_candidate_id",
    "candidate_scores",
}
_SELECTION_POLICY_FIELDS = {
    "schema_version",
    "status",
    "default_mode",
    "automatic_activation",
    "review_gate_required",
    "evidence_report_schema_version",
    "class_modes",
    "approved_by",
    "approved_at_utc",
}


@dataclass(frozen=True)
class IndependentStudyPolicy:
    minimum_reviewers_per_case: int
    minimum_cases_per_input_class_for_policy: int
    confidence_level: float
    bootstrap_iterations: int
    target_proportion_margin: float
    minimum_quality_gain: float
    maximum_cost_multiplier: float
    maximum_latency_multiplier: float
    retention_days: int
    consent_required: bool
    store_raw_input: bool
    store_raw_output: bool
    automatic_learning: bool
    review_gate_required: bool
    default_mode: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": INDEPENDENT_STUDY_POLICY_SCHEMA_VERSION,
            "minimum_reviewers_per_case": self.minimum_reviewers_per_case,
            "minimum_cases_per_input_class_for_policy": (
                self.minimum_cases_per_input_class_for_policy
            ),
            "confidence_level": self.confidence_level,
            "bootstrap_iterations": self.bootstrap_iterations,
            "target_proportion_margin": self.target_proportion_margin,
            "minimum_quality_gain": self.minimum_quality_gain,
            "maximum_cost_multiplier": self.maximum_cost_multiplier,
            "maximum_latency_multiplier": self.maximum_latency_multiplier,
            "retention_days": self.retention_days,
            "consent_required": self.consent_required,
            "store_raw_input": self.store_raw_input,
            "store_raw_output": self.store_raw_output,
            "automatic_learning": self.automatic_learning,
            "review_gate_required": self.review_gate_required,
            "default_mode": self.default_mode,
        }


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _finite(value: Any, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def load_independent_study_policy(
    path: Optional[Path] = None,
) -> IndependentStudyPolicy:
    config_path = path or DEFAULT_INDEPENDENT_STUDY_POLICY_PATH
    payload: Any = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != _POLICY_FIELDS:
        raise ValueError("independent study policy fields do not match")
    if (
        payload.get("schema_version")
        != INDEPENDENT_STUDY_POLICY_SCHEMA_VERSION
    ):
        raise ValueError("unsupported independent study policy schema")
    minimum_reviewers = _positive_int(
        payload.get("minimum_reviewers_per_case"),
        "minimum_reviewers_per_case",
    )
    if minimum_reviewers < 2:
        raise ValueError("minimum_reviewers_per_case must be at least 2")
    minimum_cases = _positive_int(
        payload.get("minimum_cases_per_input_class_for_policy"),
        "minimum_cases_per_input_class_for_policy",
    )
    confidence = _finite(payload.get("confidence_level"), "confidence_level")
    if not 0.5 < confidence < 1.0:
        raise ValueError("confidence_level must be in (0.5, 1)")
    iterations = _positive_int(
        payload.get("bootstrap_iterations"),
        "bootstrap_iterations",
    )
    if not 200 <= iterations <= 100000:
        raise ValueError("bootstrap_iterations must be in [200, 100000]")
    proportion_margin = _finite(
        payload.get("target_proportion_margin"),
        "target_proportion_margin",
    )
    if not 0.0 < proportion_margin < 0.5:
        raise ValueError("target_proportion_margin must be in (0, 0.5)")
    minimum_gain = _finite(
        payload.get("minimum_quality_gain"),
        "minimum_quality_gain",
    )
    if not 0.0 <= minimum_gain <= 4.0:
        raise ValueError("minimum_quality_gain must be in [0, 4]")
    maximum_cost = _finite(
        payload.get("maximum_cost_multiplier"),
        "maximum_cost_multiplier",
    )
    maximum_latency = _finite(
        payload.get("maximum_latency_multiplier"),
        "maximum_latency_multiplier",
    )
    if maximum_cost < 1.0 or maximum_latency < 1.0:
        raise ValueError("operational multipliers must be at least 1")
    retention_days = _positive_int(
        payload.get("retention_days"),
        "retention_days",
    )
    for field, required in (
        ("consent_required", True),
        ("store_raw_input", False),
        ("store_raw_output", False),
        ("automatic_learning", False),
        ("review_gate_required", True),
    ):
        if payload.get(field) is not required:
            raise ValueError(f"{field} must be {str(required).lower()}")
    if payload.get("default_mode") not in PROCESSING_MODES:
        raise ValueError("default_mode must be a processing mode")
    return IndependentStudyPolicy(
        minimum_reviewers_per_case=minimum_reviewers,
        minimum_cases_per_input_class_for_policy=minimum_cases,
        confidence_level=confidence,
        bootstrap_iterations=iterations,
        target_proportion_margin=proportion_margin,
        minimum_quality_gain=minimum_gain,
        maximum_cost_multiplier=maximum_cost,
        maximum_latency_multiplier=maximum_latency,
        retention_days=retention_days,
        consent_required=True,
        store_raw_input=False,
        store_raw_output=False,
        automatic_learning=False,
        review_gate_required=True,
        default_mode=payload["default_mode"],
    )


DEFAULT_INDEPENDENT_STUDY_POLICY = load_independent_study_policy()


def load_runtime_selection_policy(
    path: Optional[Path] = None,
) -> Dict[str, Any]:
    config_path = path or DEFAULT_RUNTIME_SELECTION_POLICY_PATH
    payload: Any = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != (
        _SELECTION_POLICY_FIELDS
    ):
        raise ValueError("runtime selection policy fields do not match")
    if payload.get("schema_version") != RUNTIME_SELECTION_POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported runtime selection policy schema")
    status = payload.get("status")
    if status not in {"draft", "approved"}:
        raise ValueError("runtime selection policy status is invalid")
    if payload.get("default_mode") not in PROCESSING_MODES:
        raise ValueError("runtime selection default_mode is invalid")
    if payload.get("automatic_activation") is not False:
        raise ValueError("runtime selection cannot activate automatically")
    if payload.get("review_gate_required") is not True:
        raise ValueError("runtime selection review gate is required")
    if (
        payload.get("evidence_report_schema_version")
        != INDEPENDENT_STUDY_REPORT_SCHEMA_VERSION
    ):
        raise ValueError("runtime selection evidence schema does not match")
    class_modes = payload.get("class_modes")
    if (
        not isinstance(class_modes, dict)
        or any(
            _validate_identifier(input_class, "input_class") != input_class
            or mode not in PROCESSING_MODES
            for input_class, mode in class_modes.items()
        )
    ):
        raise ValueError("runtime selection class_modes are invalid")
    approved_by = payload.get("approved_by")
    approved_at = payload.get("approved_at_utc")
    if status == "draft":
        if approved_by is not None or approved_at is not None:
            raise ValueError("draft policy cannot contain approval metadata")
    else:
        _validate_identifier(approved_by, "approved_by")
        if not isinstance(approved_at, str) or not approved_at.endswith("Z"):
            raise ValueError("approved policy requires a UTC approval time")
        try:
            instant = datetime.fromisoformat(
                approved_at.replace("Z", "+00:00")
            )
        except ValueError as error:
            raise ValueError(
                "approved policy requires a UTC approval time"
            ) from error
        if instant.utcoffset() != timezone.utc.utcoffset(None):
            raise ValueError("approved policy requires a UTC approval time")
    return dict(payload)


def _validate_identifier(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or any(character.isspace() for character in value)
    ):
        raise ValueError(f"{field} must be a compact non-empty identifier")
    return value


def _validate_candidate(candidate: Any) -> Dict[str, Any]:
    if not isinstance(candidate, dict) or set(candidate) != _CANDIDATE_FIELDS:
        raise ValueError("independent study candidate fields do not match")
    candidate_id = _validate_identifier(
        candidate.get("candidate_id"),
        "candidate_id",
    )
    latency = _finite(candidate.get("latency_ms"), "latency_ms")
    cost = _finite(
        candidate.get("estimated_cost_units"),
        "estimated_cost_units",
    )
    dispatches = _positive_int(
        candidate.get("dispatch_count"),
        "dispatch_count",
    )
    if latency < 0.0 or cost < 0.0:
        raise ValueError("candidate operational metrics must be non-negative")
    if not isinstance(candidate.get("fallback"), bool):
        raise ValueError("candidate fallback must be boolean")
    return {
        "candidate_id": candidate_id,
        "latency_ms": latency,
        "dispatch_count": dispatches,
        "estimated_cost_units": cost,
        "fallback": candidate["fallback"],
    }


def _validate_scores(value: Any, candidate_ids: set[str]) -> Dict[str, Any]:
    if not isinstance(value, dict) or set(value) != candidate_ids:
        raise ValueError("candidate_scores must cover every candidate")
    clean = {}
    for candidate_id, dimensions in value.items():
        if (
            not isinstance(dimensions, dict)
            or set(dimensions) != set(RUBRIC_DIMENSIONS)
        ):
            raise ValueError("candidate score dimensions do not match")
        clean[candidate_id] = {}
        for dimension in RUBRIC_DIMENSIONS:
            score = dimensions[dimension]
            if (
                isinstance(score, bool)
                or not isinstance(score, int)
                or not 1 <= score <= 5
            ):
                raise ValueError("independent rubric scores must be in [1, 5]")
            clean[candidate_id][dimension] = score
    return clean


def _validate_study(
    payload: Mapping[str, Any],
    policy: IndependentStudyPolicy,
) -> Dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != _STUDY_FIELDS:
        raise ValueError("independent study fields do not match")
    if payload.get("schema_version") != INDEPENDENT_STUDY_SCHEMA_VERSION:
        raise ValueError("unsupported independent study schema")
    study_id = _validate_identifier(payload.get("study_id"), "study_id")
    evidence_origin = payload.get("evidence_origin")
    if evidence_origin not in _EVIDENCE_ORIGINS:
        raise ValueError("unsupported independent study evidence_origin")
    collected_at = payload.get("collected_at_utc")
    if not isinstance(collected_at, str) or not collected_at.endswith("Z"):
        raise ValueError("collected_at_utc must be a UTC timestamp")
    try:
        collected_instant = datetime.fromisoformat(
            collected_at.replace("Z", "+00:00")
        )
    except ValueError as error:
        raise ValueError(
            "collected_at_utc must be a UTC timestamp"
        ) from error
    if collected_instant.utcoffset() != timezone.utc.utcoffset(None):
        raise ValueError("collected_at_utc must be a UTC timestamp")
    if (
        payload.get("policy_schema_version")
        != INDEPENDENT_STUDY_POLICY_SCHEMA_VERSION
    ):
        raise ValueError("study policy schema does not match")
    privacy = payload.get("privacy")
    if not isinstance(privacy, dict) or set(privacy) != _PRIVACY_FIELDS:
        raise ValueError("independent study privacy fields do not match")
    expected_privacy = {
        "consent_obtained": True,
        "raw_input_stored": policy.store_raw_input,
        "raw_output_stored": policy.store_raw_output,
        "automatic_learning": policy.automatic_learning,
        "retention_days": policy.retention_days,
    }
    if privacy != expected_privacy:
        raise ValueError("independent study privacy policy does not match")

    raw_reviewers = payload.get("reviewers")
    if not isinstance(raw_reviewers, list) or not raw_reviewers:
        raise ValueError("independent study requires reviewers")
    reviewers = []
    reviewer_ids = set()
    for reviewer in raw_reviewers:
        if (
            not isinstance(reviewer, dict)
            or set(reviewer) != _REVIEWER_FIELDS
        ):
            raise ValueError("independent study reviewer fields do not match")
        reviewer_id = _validate_identifier(
            reviewer.get("reviewer_id"),
            "reviewer_id",
        )
        if reviewer_id in reviewer_ids:
            raise ValueError("reviewer_id values must be unique")
        reviewer_ids.add(reviewer_id)
        if not isinstance(reviewer.get("independent_from_generation"), bool):
            raise ValueError("reviewer independence must be boolean")
        if not isinstance(reviewer.get("consented"), bool):
            raise ValueError("reviewer consent must be boolean")
        if policy.consent_required and reviewer["consented"] is not True:
            raise ValueError("every reviewer must provide consent")
        reviewers.append(dict(reviewer))
    if len(reviewers) < policy.minimum_reviewers_per_case:
        raise ValueError("study does not meet minimum reviewer count")

    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("independent study requires cases")
    cases = []
    case_ids = set()
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict) or set(raw_case) != _CASE_FIELDS:
            raise ValueError("independent study case fields do not match")
        case_id = _validate_identifier(raw_case.get("case_id"), "case_id")
        if case_id in case_ids:
            raise ValueError("case_id values must be unique")
        case_ids.add(case_id)
        input_class = _validate_identifier(
            raw_case.get("input_class"),
            "input_class",
        )
        raw_candidates = raw_case.get("candidates")
        if not isinstance(raw_candidates, list) or len(raw_candidates) != 3:
            raise ValueError("each case must contain exactly three candidates")
        candidates = [_validate_candidate(item) for item in raw_candidates]
        candidate_ids = {
            candidate["candidate_id"] for candidate in candidates
        }
        if len(candidate_ids) != 3:
            raise ValueError("candidate_id values must be unique per case")
        reveal = raw_case.get("reveal")
        if (
            not isinstance(reveal, dict)
            or set(reveal) != candidate_ids
            or set(reveal.values()) != set(PROCESSING_MODES)
        ):
            raise ValueError("reveal must map candidates to processing modes")
        runtime_selected = raw_case.get("runtime_selected_mode")
        if runtime_selected not in PROCESSING_MODES:
            raise ValueError("runtime_selected_mode must be a processing mode")
        raw_reviews = raw_case.get("reviews")
        if (
            not isinstance(raw_reviews, list)
            or len(raw_reviews) != len(reviewers)
        ):
            raise ValueError("every registered reviewer must review each case")
        reviews = []
        reviewed_by = set()
        for raw_review in raw_reviews:
            if (
                not isinstance(raw_review, dict)
                or set(raw_review) != _REVIEW_FIELDS
            ):
                raise ValueError("independent study review fields do not match")
            reviewer_id = raw_review.get("reviewer_id")
            if reviewer_id not in reviewer_ids or reviewer_id in reviewed_by:
                raise ValueError("case reviewer references are invalid")
            preferred = raw_review.get("preferred_candidate_id")
            if preferred not in candidate_ids:
                raise ValueError("preferred_candidate_id is invalid")
            reviewed_by.add(reviewer_id)
            reviews.append(
                {
                    "reviewer_id": reviewer_id,
                    "preferred_candidate_id": preferred,
                    "candidate_scores": _validate_scores(
                        raw_review.get("candidate_scores"),
                        candidate_ids,
                    ),
                }
            )
        cases.append(
            {
                "case_id": case_id,
                "input_class": input_class,
                "candidates": candidates,
                "reveal": dict(reveal),
                "runtime_selected_mode": runtime_selected,
                "reviews": reviews,
            }
        )
    return {
        "study_id": study_id,
        "evidence_origin": evidence_origin,
        "collected_at_utc": collected_at,
        "privacy": dict(privacy),
        "reviewers": reviewers,
        "cases": cases,
    }


def _seed(label: str) -> int:
    return int.from_bytes(
        hashlib.sha256(label.encode("utf-8")).digest()[:8],
        "big",
    )


def _bootstrap_mean(
    values: Sequence[float],
    policy: IndependentStudyPolicy,
    label: str,
) -> Dict[str, Any]:
    if not values:
        raise ValueError("bootstrap requires values")
    estimate = mean(values)
    if len(values) == 1:
        return {
            "estimate": round(estimate, 6),
            "lower": round(estimate, 6),
            "upper": round(estimate, 6),
            "confidence": policy.confidence_level,
            "method": "case_bootstrap_percentile",
        }
    randomizer = random.Random(_seed(label))
    samples = sorted(
        mean(
            values[randomizer.randrange(len(values))]
            for _ in range(len(values))
        )
        for _ in range(policy.bootstrap_iterations)
    )
    alpha = (1.0 - policy.confidence_level) / 2.0
    lower_index = max(0, math.floor(alpha * (len(samples) - 1)))
    upper_index = min(
        len(samples) - 1,
        math.ceil((1.0 - alpha) * (len(samples) - 1)),
    )
    return {
        "estimate": round(estimate, 6),
        "lower": round(samples[lower_index], 6),
        "upper": round(samples[upper_index], 6),
        "confidence": policy.confidence_level,
        "method": "case_bootstrap_percentile",
    }


def _quadratic_weighted_kappa(
    first: Sequence[int],
    second: Sequence[int],
) -> Optional[float]:
    if len(first) != len(second) or not first:
        raise ValueError("weighted kappa requires paired ratings")
    labels = range(1, 6)
    count = len(first)
    observed = mean(((a - b) / 4.0) ** 2 for a, b in zip(first, second))
    first_counts = {label: first.count(label) for label in labels}
    second_counts = {label: second.count(label) for label in labels}
    expected = sum(
        ((a - b) / 4.0) ** 2
        * first_counts[a]
        * second_counts[b]
        / (count * count)
        for a in labels
        for b in labels
    )
    if expected == 0.0:
        return 1.0 if observed == 0.0 else None
    return round(1.0 - observed / expected, 6)


def _required_proportion_cases(policy: IndependentStudyPolicy) -> int:
    z = NormalDist().inv_cdf((1.0 + policy.confidence_level) / 2.0)
    return math.ceil(
        z * z * 0.25 / (policy.target_proportion_margin**2)
    )


def _required_mean_cases(
    differences: Sequence[float],
    policy: IndependentStudyPolicy,
) -> int:
    if len(differences) < 2:
        return policy.minimum_cases_per_input_class_for_policy
    sigma = stdev(differences)
    if sigma == 0.0:
        return policy.minimum_cases_per_input_class_for_policy
    z = NormalDist().inv_cdf((1.0 + policy.confidence_level) / 2.0)
    estimate = math.ceil(
        (z * sigma / max(policy.minimum_quality_gain, 1e-9)) ** 2
    )
    return max(policy.minimum_cases_per_input_class_for_policy, estimate)


def _mode_case_records(study: Mapping[str, Any]) -> list[Dict[str, Any]]:
    records = []
    for case in study["cases"]:
        candidates = {
            candidate["candidate_id"]: candidate
            for candidate in case["candidates"]
        }
        scores_by_candidate = {
            candidate_id: []
            for candidate_id in candidates
        }
        preferred_modes = []
        for review in case["reviews"]:
            preferred_modes.append(
                case["reveal"][review["preferred_candidate_id"]]
            )
            for candidate_id, scores in review[
                "candidate_scores"
            ].items():
                scores_by_candidate[candidate_id].extend(scores.values())
        mode_records = {}
        for candidate_id, candidate in candidates.items():
            mode = case["reveal"][candidate_id]
            mode_records[mode] = {
                "quality": mean(scores_by_candidate[candidate_id]),
                "latency_ms": candidate["latency_ms"],
                "dispatch_count": candidate["dispatch_count"],
                "estimated_cost_units": (
                    candidate["estimated_cost_units"]
                ),
                "fallback": candidate["fallback"],
            }
        counts = {
            mode: preferred_modes.count(mode) for mode in PROCESSING_MODES
        }
        top = max(counts.values())
        winners = [mode for mode, count in counts.items() if count == top]
        records.append(
            {
                "case_id": case["case_id"],
                "input_class": case["input_class"],
                "modes": mode_records,
                "preferred_modes": preferred_modes,
                "majority_preferred_mode": (
                    winners[0] if len(winners) == 1 else None
                ),
                "runtime_selected_mode": case["runtime_selected_mode"],
            }
        )
    return records


def _aggregate_modes(
    records: Sequence[Mapping[str, Any]],
    policy: IndependentStudyPolicy,
    label_prefix: str,
) -> Dict[str, Any]:
    result = {}
    for mode in PROCESSING_MODES:
        mode_records = [record["modes"][mode] for record in records]
        quality_values = [record["quality"] for record in mode_records]
        result[mode] = {
            "case_count": len(mode_records),
            "quality": _bootstrap_mean(
                quality_values,
                policy,
                f"{label_prefix}:{mode}:quality",
            ),
            "latency_ms_mean": round(
                mean(record["latency_ms"] for record in mode_records),
                3,
            ),
            "dispatch_count_mean": round(
                mean(record["dispatch_count"] for record in mode_records),
                6,
            ),
            "estimated_cost_units_mean": round(
                mean(
                    record["estimated_cost_units"]
                    for record in mode_records
                ),
                6,
            ),
            "fallback_rate": round(
                mean(int(record["fallback"]) for record in mode_records),
                6,
            ),
        }
    return result


def _quality_differences(
    records: Sequence[Mapping[str, Any]],
    mode: str,
) -> list[float]:
    return [
        record["modes"][mode]["quality"]
        - record["modes"]["horizontal"]["quality"]
        for record in records
    ]


def _pareto_frontier(metrics: Mapping[str, Any]) -> Dict[str, Any]:
    frontier = []
    dominated = {}
    for mode in PROCESSING_MODES:
        point = metrics[mode]
        dominators = []
        for other in PROCESSING_MODES:
            if other == mode:
                continue
            candidate = metrics[other]
            weakly_better = (
                candidate["quality"]["estimate"]
                >= point["quality"]["estimate"]
                and candidate["latency_ms_mean"] <= point["latency_ms_mean"]
                and candidate["dispatch_count_mean"]
                <= point["dispatch_count_mean"]
                and candidate["estimated_cost_units_mean"]
                <= point["estimated_cost_units_mean"]
                and candidate["fallback_rate"] <= point["fallback_rate"]
            )
            strictly_better = (
                candidate["quality"]["estimate"]
                > point["quality"]["estimate"]
                or candidate["latency_ms_mean"] < point["latency_ms_mean"]
                or candidate["dispatch_count_mean"]
                < point["dispatch_count_mean"]
                or candidate["estimated_cost_units_mean"]
                < point["estimated_cost_units_mean"]
                or candidate["fallback_rate"] < point["fallback_rate"]
            )
            if weakly_better and strictly_better:
                dominators.append(other)
        if dominators:
            dominated[mode] = dominators
        else:
            frontier.append(mode)
    return {
        "frontier_modes": frontier,
        "dominated_modes": dominated,
    }


def _agreement(
    study: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    policy: IndependentStudyPolicy,
) -> Dict[str, Any]:
    reviewer_ids = [
        reviewer["reviewer_id"] for reviewer in study["reviewers"]
    ]
    ratings = {reviewer_id: [] for reviewer_id in reviewer_ids}
    for case in study["cases"]:
        reviews = {
            review["reviewer_id"]: review for review in case["reviews"]
        }
        for reviewer_id in reviewer_ids:
            review = reviews[reviewer_id]
            for candidate_id in sorted(review["candidate_scores"]):
                for dimension in RUBRIC_DIMENSIONS:
                    ratings[reviewer_id].append(
                        review["candidate_scores"][candidate_id][dimension]
                    )
    kappas = []
    for first, second in combinations(reviewer_ids, 2):
        kappa = _quadratic_weighted_kappa(
            ratings[first],
            ratings[second],
        )
        if kappa is not None:
            kappas.append(kappa)
    preference_pairs = 0
    preference_matches = 0
    unanimous = 0
    runtime_eligible = 0
    runtime_matches = 0
    for record in records:
        preferences = record["preferred_modes"]
        unanimous += int(len(set(preferences)) == 1)
        for first, second in combinations(preferences, 2):
            preference_pairs += 1
            preference_matches += int(first == second)
        majority = record["majority_preferred_mode"]
        if majority is not None:
            runtime_eligible += 1
            runtime_matches += int(
                record["runtime_selected_mode"] == majority
            )
    return {
        "reviewer_count": len(reviewer_ids),
        "pairwise_quadratic_weighted_kappa_mean": (
            round(mean(kappas), 6) if kappas else None
        ),
        "preference_pairwise_agreement": round(
            preference_matches / preference_pairs,
            6,
        ),
        "unanimous_preference_rate": round(
            unanimous / len(records),
            6,
        ),
        "runtime_majority_preference_agreement": (
            {
                "eligible_case_count": runtime_eligible,
                "match_count": runtime_matches,
                "rate": round(runtime_matches / runtime_eligible, 6),
                "interval": wilson_interval(
                    runtime_matches,
                    runtime_eligible,
                    policy.confidence_level,
                ),
            }
            if runtime_eligible
            else None
        ),
    }


def _calibrate_policy(
    records: Sequence[Mapping[str, Any]],
    by_class: Mapping[str, Any],
    evidence_eligible: bool,
    policy: IndependentStudyPolicy,
) -> Dict[str, Any]:
    class_policies = {}
    for input_class, metrics in by_class.items():
        class_records = [
            record
            for record in records
            if record["input_class"] == input_class
        ]
        provisional = min(
            PROCESSING_MODES,
            key=lambda mode: (
                -metrics[mode]["quality"]["estimate"],
                metrics[mode]["estimated_cost_units_mean"],
                metrics[mode]["latency_ms_mean"],
            ),
        )
        differences = _quality_differences(class_records, provisional)
        gain = _bootstrap_mean(
            differences,
            policy,
            f"policy:{input_class}:{provisional}",
        )
        horizontal_cost = max(
            metrics["horizontal"]["estimated_cost_units_mean"],
            1e-9,
        )
        horizontal_latency = max(
            metrics["horizontal"]["latency_ms_mean"],
            1e-9,
        )
        cost_multiplier = (
            metrics[provisional]["estimated_cost_units_mean"]
            / horizontal_cost
        )
        latency_multiplier = (
            metrics[provisional]["latency_ms_mean"]
            / horizontal_latency
        )
        enough_cases = (
            len(class_records)
            >= policy.minimum_cases_per_input_class_for_policy
        )
        quality_established = (
            provisional == "horizontal"
            or gain["lower"] >= policy.minimum_quality_gain
        )
        operationally_allowed = (
            cost_multiplier <= policy.maximum_cost_multiplier
            and latency_multiplier <= policy.maximum_latency_multiplier
        )
        if not evidence_eligible:
            status = "contract_fixture_only"
        elif not enough_cases:
            status = "insufficient_cases"
        elif not quality_established:
            status = "quality_gain_not_established"
        elif not operationally_allowed:
            status = "operational_limits_exceeded"
        else:
            status = "awaiting_human_review"
        class_policies[input_class] = {
            "case_count": len(class_records),
            "provisional_best_mode": provisional,
            "quality_gain_over_horizontal": gain,
            "cost_multiplier_over_horizontal": round(
                cost_multiplier,
                6,
            ),
            "latency_multiplier_over_horizontal": round(
                latency_multiplier,
                6,
            ),
            "required_case_count_from_observed_variance": (
                _required_mean_cases(differences, policy)
            ),
            "status": status,
            "active_mode": policy.default_mode,
            "automatic_activation": False,
        }
    return {
        "schema_version": RUNTIME_SELECTION_POLICY_SCHEMA_VERSION,
        "status": "draft",
        "default_mode": policy.default_mode,
        "review_gate_required": policy.review_gate_required,
        "automatic_activation": False,
        "class_policies": class_policies,
    }


def evaluate_independent_study(
    payload: Mapping[str, Any],
    policy: IndependentStudyPolicy = DEFAULT_INDEPENDENT_STUDY_POLICY,
) -> Dict[str, Any]:
    study = _validate_study(payload, policy)
    records = _mode_case_records(study)
    independent_reviewers = [
        reviewer
        for reviewer in study["reviewers"]
        if reviewer["independent_from_generation"]
        and reviewer["consented"]
    ]
    evidence_eligible = (
        study["evidence_origin"] == "independent_blind_collection"
        and len(independent_reviewers)
        >= policy.minimum_reviewers_per_case
        and len(independent_reviewers) == len(study["reviewers"])
    )
    global_metrics = _aggregate_modes(records, policy, "global")
    input_classes = sorted(
        {record["input_class"] for record in records}
    )
    by_class = {
        input_class: _aggregate_modes(
            [
                record
                for record in records
                if record["input_class"] == input_class
            ],
            policy,
            f"class:{input_class}",
        )
        for input_class in input_classes
    }
    quality_comparisons = {}
    for mode in ("vertical", "hybrid"):
        differences = _quality_differences(records, mode)
        quality_comparisons[f"{mode}_minus_horizontal"] = {
            "quality_gain": _bootstrap_mean(
                differences,
                policy,
                f"global-difference:{mode}",
            ),
            "required_case_count_from_observed_variance": (
                _required_mean_cases(differences, policy)
            ),
        }
    return {
        "schema_version": INDEPENDENT_STUDY_REPORT_SCHEMA_VERSION,
        "study_id": study["study_id"],
        "evidence_origin": study["evidence_origin"],
        "evidence_eligible_for_policy": evidence_eligible,
        "case_count": len(records),
        "input_class_count": len(input_classes),
        "privacy": study["privacy"],
        "policy": policy.as_dict(),
        "mode_metrics": global_metrics,
        "quality_comparisons": quality_comparisons,
        "agreement": _agreement(study, records, policy),
        "sample_requirements": {
            "minimum_reviewers_per_case": (
                policy.minimum_reviewers_per_case
            ),
            "minimum_cases_per_input_class_for_policy": (
                policy.minimum_cases_per_input_class_for_policy
            ),
            "conservative_cases_for_preference_rate_margin": (
                _required_proportion_cases(policy)
            ),
        },
        "pareto_frontier": _pareto_frontier(global_metrics),
        "input_class_metrics": by_class,
        "input_class_pareto_frontiers": {
            input_class: _pareto_frontier(metrics)
            for input_class, metrics in by_class.items()
        },
        "selection_policy": _calibrate_policy(
            records,
            by_class,
            evidence_eligible,
            policy,
        ),
        "interpretation": (
            "Only independent_blind_collection evidence can advance a "
            "selection policy to human review. Contract fixtures remain "
            "draft-only and never activate runtime routing automatically."
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a privacy-minimized independent runtime study"
    )
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--policy-file", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input_file.read_text(encoding="utf-8"))
        policy = load_independent_study_policy(args.policy_file)
        report = evaluate_independent_study(payload, policy)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
