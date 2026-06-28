"""Harvest Thought Color samples from saved logs and router artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from .paths import DATA_DIR, REPORTS_DIR, REPO_ROOT


HARVEST_SCHEMA_VERSION = "thought-color-harvested-samples.v0.1"
HARVEST_REPORT_SCHEMA_VERSION = "thought-color-harvest-report.v0.1"
HARVESTED_SAMPLES_PATH = DATA_DIR / "thought_color_harvested_samples_v0_1.json"
HARVEST_REPORT_PATH = REPORTS_DIR / "thought_color_harvest_report_v0_1.json"

SOURCE_HARVESTED_CLAUDELOG = REPO_ROOT / "data" / "harvested_claudelog_v1.json"
SOURCE_CONVERSATION = REPO_ROOT / "data" / "conversation_accumulation_v1.json"
SOURCE_CONVERSATION_REVIEWS = (
    REPO_ROOT / "data" / "conversation_accumulation_reviews_v1.json"
)
SOURCE_ROUTER_REVIEW_QUEUE = (
    REPO_ROOT / "build" / "v6_boundary_debate_candidate_queue_review_v1.json"
)
ADOPTED_BENCHMARKS = (
    REPO_ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json",
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "v8_recovery_priority_review_candidate_benchmark_v1.json",
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "v9_accumulated_primary_review_candidate_benchmark_v1.json",
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "v9_constraint_operation_extension_benchmark_v1.json",
)

BASE_BY_INTENT = {
    "respond": (100, "direct_answer"),
    "explain": (110, "mechanism_explanation"),
    "clarify": (120, "clarification_gate"),
    "build": (130, "artifact_generation"),
    "verify": (140, "verification_review"),
    "summarize": (150, "summary_compression"),
    "explore": (160, "exploration_tradeoff"),
}
OPERATION_BY_INTENT = {
    "respond": "respond",
    "explain": "reason",
    "clarify": "route",
    "build": "generate",
    "verify": "verify",
    "summarize": "remember",
    "explore": "compare",
}
OPERATION_MAP = {
    "respond": "respond",
    "explain": "reason",
    "clarify": "route",
    "build": "generate",
    "verify": "verify",
    "summarize": "remember",
    "explore": "compare",
    "search": "verify",
    "calculate": "reason",
    "compare": "compare",
}
INTENSITY_BY_RISK = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "hold",
}
INTENSITY_BY_CONFIDENCE = {
    "low": "low",
    "medium": "medium",
    "high": "medium",
}
SOURCE_POLICIES = {
    "claudelog_approved_intent": {
        "training_allowed": True,
        "human_review_required": False,
        "adoption_status": "approved_harvested",
    },
    "conversation_accumulation_approved": {
        "training_allowed": True,
        "human_review_required": False,
        "adoption_status": "approved_human_reviewed",
    },
    "router_adopted_nonsealed": {
        "training_allowed": True,
        "human_review_required": False,
        "adoption_status": "approved_nonsealed_router",
    },
    "router_review_required": {
        "training_allowed": False,
        "human_review_required": True,
        "adoption_status": "review_required",
    },
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _quality_flags(text: str, *, source_confidence: str | None = None) -> list[str]:
    flags = []
    if "\ufffd" in text:
        flags.append("mojibake_suspected")
    if len(text) < 8:
        flags.append("very_short")
    if source_confidence == "low":
        flags.append("low_source_confidence")
    return flags


def _stance_from_semantics(semantics: Mapping[str, Any]) -> str:
    info = semantics.get("information_state", {})
    risk = semantics.get("risk", {})
    flags = set(risk.get("flags", []))
    if info.get("missing_required_information"):
        return "clarify"
    if info.get("requires_current_information"):
        return "reserve"
    if info.get("contains_unverified_claims"):
        return "challenge"
    if {"safety", "legal", "medical", "financial", "hostile_user"} & flags:
        return "challenge"
    if info.get("multiple_intents"):
        return "explore"
    return "neutral"


def _operation_from_semantics(semantics: Mapping[str, Any], intent: str) -> str:
    operations = semantics.get("operations") or [intent]
    for operation in operations:
        if operation in OPERATION_MAP:
            return OPERATION_MAP[operation]
    return OPERATION_BY_INTENT[intent]


def _intensity_from_semantics(semantics: Mapping[str, Any]) -> str:
    risk = semantics.get("risk", {})
    return INTENSITY_BY_RISK.get(risk.get("level", "low"), "medium")


def _code_from_intent(
    intent: str,
    *,
    stance: str = "neutral",
    operation: str | None = None,
    intensity: str = "medium",
) -> Dict[str, Any]:
    base_id, base_label = BASE_BY_INTENT[intent]
    return {
        "base_id": base_id,
        "base_label": base_label,
        "stance": stance,
        "operation": operation or OPERATION_BY_INTENT[intent],
        "intensity": intensity,
    }


def _code_from_semantics(semantics: Mapping[str, Any]) -> Dict[str, Any]:
    intent = semantics["primary_intent"]
    return _code_from_intent(
        intent,
        stance=_stance_from_semantics(semantics),
        operation=_operation_from_semantics(semantics, intent),
        intensity=_intensity_from_semantics(semantics),
    )


def _policy(source_kind: str) -> Dict[str, Any]:
    return dict(SOURCE_POLICIES[source_kind])


def _sample(
    *,
    sample_id: str,
    source_kind: str,
    source_path: Path,
    source_id: str,
    lane: str,
    language: str,
    input_text: str,
    expected: Mapping[str, Any],
    source_semantics: Mapping[str, Any] | None = None,
    collision_policy: str = "share_base_split_modifier",
    judgment_note: str = "",
    near_miss: Mapping[str, Any] | None = None,
    source_confidence: str | None = None,
) -> Dict[str, Any]:
    item = {
        "id": sample_id,
        "schema_version": "thought-color-harvested-sample.v0.1",
        "source_kind": source_kind,
        "source_path": str(source_path.relative_to(REPO_ROOT)),
        "source_id": source_id,
        "lane": lane,
        **_policy(source_kind),
        "language": language,
        "input": input_text,
        "input_sha256": _sha256_text(input_text),
        "expected": dict(expected),
        "collision_policy": collision_policy,
        "quality_flags": _quality_flags(
            input_text,
            source_confidence=source_confidence,
        ),
        "judgment_note": judgment_note,
    }
    if source_confidence is not None:
        item["source_confidence"] = source_confidence
    if source_semantics is not None:
        item["source_semantics"] = dict(source_semantics)
    if near_miss is not None:
        item["near_miss"] = dict(near_miss)
    return item


def _harvest_claudelog() -> list[Dict[str, Any]]:
    if not SOURCE_HARVESTED_CLAUDELOG.exists():
        return []
    payload = _read_json(SOURCE_HARVESTED_CLAUDELOG)
    grouped: Dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for example in payload.get("examples", []):
        intent = example.get("intent")
        if (
            example.get("review_status") != "approved"
            or intent not in BASE_BY_INTENT
        ):
            continue
        grouped[intent].append(example)

    confidence_order = {"high": 0, "medium": 1, "low": 2}
    samples = []
    for intent in sorted(grouped):
        selected = sorted(
            grouped[intent],
            key=lambda item: (
                confidence_order.get(item.get("confidence", "medium"), 9),
                len(item.get("input", "")),
                item.get("input", ""),
            ),
        )[:12]
        for index, example in enumerate(selected, start=1):
            note = str(example.get("note", ""))
            stance = (
                "empathize"
                if any(word in note.lower() for word in ("social", "thanks", "status"))
                else "neutral"
            )
            if intent == "clarify":
                stance = "clarify"
            expected = _code_from_intent(
                intent,
                stance=stance,
                intensity=INTENSITY_BY_CONFIDENCE.get(
                    example.get("confidence", "medium"),
                    "medium",
                ),
            )
            samples.append(
                _sample(
                    sample_id=f"tc-harvest-claudelog-{intent}-{index:03d}",
                    source_kind="claudelog_approved_intent",
                    source_path=SOURCE_HARVESTED_CLAUDELOG,
                    source_id=f"claudelog:{intent}:{index}",
                    lane="answer_or_request_log",
                    language=example.get("language", "mixed"),
                    input_text=example["input"],
                    expected=expected,
                    source_semantics={"intent": intent},
                    collision_policy="share_base",
                    judgment_note=note,
                    source_confidence=example.get("confidence", "medium"),
                )
            )
    return samples


def _harvest_conversation() -> list[Dict[str, Any]]:
    if not SOURCE_CONVERSATION.exists() or not SOURCE_CONVERSATION_REVIEWS.exists():
        return []
    payload = _read_json(SOURCE_CONVERSATION)
    reviews = _read_json(SOURCE_CONVERSATION_REVIEWS).get("reviews", {})
    samples = []
    for case in payload.get("cases", []):
        review = reviews.get(case["id"], {})
        if review.get("status") != "approved":
            continue
        expected_source = review.get("expected", case.get("expected", {}))
        intent = expected_source.get("intent")
        if intent not in BASE_BY_INTENT:
            continue
        processing = expected_source.get("processing_class", "standard")
        intensity = "low" if processing == "economy" else "medium"
        if case.get("critical_underprocessing"):
            intensity = "high"
        expected = _code_from_intent(
            intent,
            stance="clarify" if intent == "clarify" else "neutral",
            intensity=intensity,
        )
        samples.append(
            _sample(
                sample_id=f"tc-harvest-accum-{case['id']}",
                source_kind="conversation_accumulation_approved",
                source_path=SOURCE_CONVERSATION,
                source_id=case["id"],
                lane="conversation_accumulation",
                language=case.get("language", "mixed"),
                input_text=case["input"],
                expected=expected,
                source_semantics=expected_source,
                collision_policy="share_base_split_modifier",
                judgment_note=review.get("notes", ""),
            )
        )
    return samples


def _harvest_adopted_benchmarks() -> list[Dict[str, Any]]:
    samples = []
    for path in ADOPTED_BENCHMARKS:
        if not path.exists():
            continue
        payload = _read_json(path)
        if payload.get("review_status") != "human_reviewed":
            continue
        for case in payload.get("cases", []):
            semantics = case["expected"]
            expected = _code_from_semantics(semantics)
            samples.append(
                _sample(
                    sample_id=f"tc-harvest-adopted-{case['id']}",
                    source_kind="router_adopted_nonsealed",
                    source_path=path,
                    source_id=case["id"],
                    lane="router_adopted_nonsealed",
                    language=case.get("language", "mixed"),
                    input_text=case["input"],
                    expected=expected,
                    source_semantics=semantics,
                    collision_policy=(
                        "split_base_share_modifier"
                        if case.get("contrast_group")
                        else "share_base_split_modifier"
                    ),
                    judgment_note=(
                        f"human-reviewed nonsealed router fixture; "
                        f"source_group={case.get('source_group')}"
                    ),
                )
            )
    return samples


def _harvest_router_review_queue() -> list[Dict[str, Any]]:
    if not SOURCE_ROUTER_REVIEW_QUEUE.exists():
        return []
    payload = _read_json(SOURCE_ROUTER_REVIEW_QUEUE)
    samples = []
    for item in payload.get("items", []):
        semantics = item["expected"]
        expected = _code_from_semantics(semantics)
        actual = item.get("actual")
        near_miss = None
        if actual:
            actual_code = _code_from_semantics(actual)
            if actual_code != expected:
                near_miss = {
                    "current_route": actual_code,
                    "route_gap_fields": item.get("fields", []),
                }
        samples.append(
            _sample(
                sample_id=f"tc-harvest-router-review-{item['id']}",
                source_kind="router_review_required",
                source_path=SOURCE_ROUTER_REVIEW_QUEUE,
                source_id=item["id"],
                lane="router_judgment_review_queue",
                language="en" if item["prompt"].isascii() else "mixed",
                input_text=item["prompt"],
                expected=expected,
                source_semantics=semantics,
                collision_policy=(
                    "split_base"
                    if near_miss and near_miss.get("route_gap_fields")
                    else "share_base_split_modifier"
                ),
                judgment_note=item.get("review_focus", ""),
                near_miss=near_miss,
            )
        )
    return samples


def _deduplicate(samples: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    seen = set()
    deduped = []
    for sample in samples:
        digest = sample["input_sha256"]
        source_kind = sample["source_kind"]
        key = (digest, source_kind)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sample)
    return deduped


def harvest_samples() -> Dict[str, Any]:
    samples = _deduplicate(
        [
            *_harvest_claudelog(),
            *_harvest_conversation(),
            *_harvest_adopted_benchmarks(),
            *_harvest_router_review_queue(),
        ]
    )
    return {
        "schema_version": HARVEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Thought Color samples distilled from saved logs, approved "
            "nonsealed fixtures, and router review queues."
        ),
        "policy": {
            "sealed_fixtures_used": False,
            "raw_router_turn_text_used": False,
            "review_required_items_are_training_data": False,
            "approved_items_may_be_used_for_experiment_training": True,
        },
        "sources": [
            str(SOURCE_HARVESTED_CLAUDELOG.relative_to(REPO_ROOT)),
            str(SOURCE_CONVERSATION.relative_to(REPO_ROOT)),
            str(SOURCE_CONVERSATION_REVIEWS.relative_to(REPO_ROOT)),
            *[
                str(path.relative_to(REPO_ROOT))
                for path in ADOPTED_BENCHMARKS
                if path.exists()
            ],
            str(SOURCE_ROUTER_REVIEW_QUEUE.relative_to(REPO_ROOT)),
        ],
        "samples": samples,
    }


def summarize(payload: Mapping[str, Any]) -> Dict[str, Any]:
    samples = payload["samples"]
    source_counts = Counter(sample["source_kind"] for sample in samples)
    lane_counts = Counter(sample["lane"] for sample in samples)
    status_counts = Counter(sample["adoption_status"] for sample in samples)
    base_counts = Counter(sample["expected"]["base_label"] for sample in samples)
    quality_counts = Counter(
        flag for sample in samples for flag in sample.get("quality_flags", [])
    )
    route_gap_count = sum(1 for sample in samples if sample.get("near_miss"))
    training_allowed_count = sum(1 for sample in samples if sample["training_allowed"])
    review_required_count = sum(
        1 for sample in samples if sample["human_review_required"]
    )
    return {
        "schema_version": HARVEST_REPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(samples),
        "training_allowed_count": training_allowed_count,
        "review_required_count": review_required_count,
        "route_gap_count": route_gap_count,
        "source_counts": dict(sorted(source_counts.items())),
        "lane_counts": dict(sorted(lane_counts.items())),
        "adoption_status_counts": dict(sorted(status_counts.items())),
        "base_counts": dict(sorted(base_counts.items())),
        "quality_flag_counts": dict(sorted(quality_counts.items())),
        "policy": payload["policy"],
        "output": str(HARVESTED_SAMPLES_PATH),
    }


def write_harvest(
    *,
    samples_path: Path = HARVESTED_SAMPLES_PATH,
    report_path: Path = HARVEST_REPORT_PATH,
) -> Dict[str, Any]:
    payload = harvest_samples()
    samples_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    samples_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report = summarize(payload)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    if args.no_write:
        report = summarize(harvest_samples())
    else:
        report = write_harvest()
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

