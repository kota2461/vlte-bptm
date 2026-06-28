"""Generate synthetic Thought Color contrast samples with Gemma.

This module prepares 5 lanes x 7 base families x 5 samples = 175 candidates.
Generated samples are review-required by default and are not training data
until explicitly adopted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from .code import INTENSITY_LABELS, OPERATION_LABELS, STANCE_LABELS, ThoughtColorCode
from .paths import DATA_DIR, REPORTS_DIR
from .sample_pool import COLLISION_POLICIES, LANGUAGES, LANES


DEFAULT_BASE_URL = "http://192.168.10.124:1234"
DEFAULT_MODEL = "google/gemma-4-12b-qat"
SYNTHETIC_CANDIDATES_PATH = DATA_DIR / "thought_color_synthetic_candidates_v0_1.json"
SYNTHETIC_REPORT_PATH = REPORTS_DIR / "thought_color_synthetic_report_v0_1.json"

SYNTHETIC_SCHEMA_VERSION = "thought-color-synthetic-candidates.v0.1"
SYNTHETIC_BATCH_SCHEMA_VERSION = "thought-color-synthetic-batch.v0.1"

GENERATION_LANES = (
    "same_base_different_stance",
    "same_base_different_operation",
    "same_operation_different_base",
    "collision_should_split",
    "collision_should_share",
)
BASE_FAMILIES = (
    {
        "base_id": 100,
        "base_label": "direct_answer",
        "description": "Short factual answer or direct response.",
    },
    {
        "base_id": 110,
        "base_label": "mechanism_explanation",
        "description": "Explain why or how something works.",
    },
    {
        "base_id": 120,
        "base_label": "clarification_gate",
        "description": "Ask for missing information or route uncertainty.",
    },
    {
        "base_id": 130,
        "base_label": "artifact_generation",
        "description": "Create, draft, implement, or structure an artifact.",
    },
    {
        "base_id": 140,
        "base_label": "verification_review",
        "description": "Check, review, validate, or challenge an artifact or claim.",
    },
    {
        "base_id": 150,
        "base_label": "summary_compression",
        "description": "Compress, recap, or preserve key points.",
    },
    {
        "base_id": 160,
        "base_label": "exploration_tradeoff",
        "description": "Compare options, explore tradeoffs, or brainstorm.",
    },
)

LANE_COLLISION_POLICY = {
    "same_base_different_stance": "share_base_split_modifier",
    "same_base_different_operation": "share_base_split_modifier",
    "same_operation_different_base": "split_base_share_modifier",
    "collision_should_split": "split_base",
    "collision_should_share": "share_base",
}
LANE_NOTES = {
    "same_base_different_stance": (
        "Keep the same base family. Vary stance while keeping operation and "
        "surface task close enough to make the contrast visible."
    ),
    "same_base_different_operation": (
        "Keep the same base family. Vary operation while keeping stance mostly "
        "neutral unless the blueprint says otherwise."
    ),
    "same_operation_different_base": (
        "Use the requested operation, but make the base family clearly different "
        "from other bases that could use the same operation."
    ),
    "collision_should_split": (
        "Create a sample that looks superficially similar to another base, but "
        "should split into the target base."
    ),
    "collision_should_share": (
        "Create a sample with different wording that should still share the "
        "target base."
    ),
}
STANCE_SEQUENCE = ("neutral", "clarify", "challenge", "empathize", "reserve")
OPERATION_SEQUENCE = ("respond", "reason", "compare", "verify", "generate")
INTENSITY_SEQUENCE = ("low", "medium", "high", "medium", "hold")
LANGUAGE_SEQUENCE = ("en", "ja", "en", "ja", "en")


@dataclass(frozen=True)
class SyntheticSpec:
    sample_id: str
    lane: str
    group_id: str
    language: str
    base_id: int
    base_label: str
    stance: str
    operation: str
    intensity: str
    collision_policy: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.sample_id,
            "lane": self.lane,
            "group_id": self.group_id,
            "language": self.language,
            "expected": {
                "base_id": self.base_id,
                "base_label": self.base_label,
                "stance": self.stance,
                "operation": self.operation,
                "intensity": self.intensity,
            },
            "collision_policy": self.collision_policy,
        }


@dataclass(frozen=True)
class SyntheticTask:
    task_id: str
    lane: str
    base: Mapping[str, Any]
    specs: tuple[SyntheticSpec, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "lane": self.lane,
            "base": dict(self.base),
            "specs": [spec.as_dict() for spec in self.specs],
        }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _loose_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _operation_for_base(base_label: str) -> str:
    return {
        "direct_answer": "respond",
        "mechanism_explanation": "reason",
        "clarification_gate": "route",
        "artifact_generation": "generate",
        "verification_review": "verify",
        "summary_compression": "remember",
        "exploration_tradeoff": "compare",
    }[base_label]


def _split_near_base(base_label: str) -> str:
    return {
        "direct_answer": "mechanism_explanation",
        "mechanism_explanation": "direct_answer",
        "clarification_gate": "exploration_tradeoff",
        "artifact_generation": "verification_review",
        "verification_review": "artifact_generation",
        "summary_compression": "mechanism_explanation",
        "exploration_tradeoff": "artifact_generation",
    }[base_label]


def _spec_for(lane: str, base: Mapping[str, Any], pattern: int) -> SyntheticSpec:
    base_id = int(base["base_id"])
    base_label = str(base["base_label"])
    sample_id = (
        f"tc-synth-{_slug(lane)}-{_slug(base_label)}-{pattern + 1:02d}"
    )
    language = LANGUAGE_SEQUENCE[pattern]
    stance = "neutral"
    operation = _operation_for_base(base_label)
    intensity = INTENSITY_SEQUENCE[pattern]

    if lane == "same_base_different_stance":
        stance = STANCE_SEQUENCE[pattern]
        group_id = f"synth-{_slug(base_label)}-stance"
    elif lane == "same_base_different_operation":
        operation = OPERATION_SEQUENCE[pattern]
        group_id = f"synth-{_slug(base_label)}-operation"
    elif lane == "same_operation_different_base":
        operation = OPERATION_SEQUENCE[pattern]
        group_id = f"synth-same-operation-{operation}-p{pattern + 1:02d}"
    elif lane == "collision_should_split":
        stance = "challenge" if pattern in (2, 4) else "neutral"
        group_id = (
            f"synth-split-{_slug(base_label)}-from-"
            f"{_slug(_split_near_base(base_label))}"
        )
    elif lane == "collision_should_share":
        stance = STANCE_SEQUENCE[pattern] if pattern in (1, 3) else "neutral"
        group_id = f"synth-share-{_slug(base_label)}"
    else:
        raise ValueError(f"unsupported lane: {lane}")

    return SyntheticSpec(
        sample_id=sample_id,
        lane=lane,
        group_id=group_id,
        language=language,
        base_id=base_id,
        base_label=base_label,
        stance=stance,
        operation=operation,
        intensity=intensity,
        collision_policy=LANE_COLLISION_POLICY[lane],
    )


def build_generation_plan() -> tuple[SyntheticTask, ...]:
    tasks = []
    for lane in GENERATION_LANES:
        for base in BASE_FAMILIES:
            base_label = str(base["base_label"])
            specs = tuple(_spec_for(lane, base, pattern) for pattern in range(5))
            tasks.append(
                SyntheticTask(
                    task_id=f"{_slug(lane)}__{_slug(base_label)}",
                    lane=lane,
                    base=base,
                    specs=specs,
                )
            )
    return tuple(tasks)


def generation_plan_summary(tasks: Sequence[SyntheticTask] | None = None) -> Dict[str, Any]:
    plan = tuple(tasks) if tasks is not None else build_generation_plan()
    sample_count = sum(len(task.specs) for task in plan)
    return {
        "schema_version": "thought-color-synthetic-plan-summary.v0.1",
        "model": DEFAULT_MODEL,
        "base_url": DEFAULT_BASE_URL,
        "task_count": len(plan),
        "sample_count": sample_count,
        "lanes": list(GENERATION_LANES),
        "base_family_count": len(BASE_FAMILIES),
        "patterns_per_lane_base": 5,
        "expected_shape": "5 lanes x 7 base families x 5 patterns = 175",
    }


def _system_prompt() -> str:
    return (
        "You generate concise synthetic examples for Thought Color Code v0.1. "
        "Return JSON only. Do not include markdown fences. Do not use real "
        "people, current news, legal/medical/financial advice, private data, "
        "or copyrighted text. Each sample must be one user input, not an answer. "
        "Keep text short but natural. Labels must exactly match the blueprint."
    )


def _user_prompt(task: SyntheticTask) -> str:
    payload = {
        "schema_version": "thought-color-synthetic-request.v0.1",
        "instruction": (
            "Create exactly five samples matching these blueprints. The input "
            "text may be English or Japanese according to language. Do not "
            "change id, lane, group_id, expected labels, or collision_policy. "
            "For each sample, add input, two judgment_questions, generation_note, "
            "and near_miss. near_miss should name the closest wrong base or "
            "modifier and explain why it is wrong in one short sentence."
        ),
        "lane": task.lane,
        "lane_note": LANE_NOTES[task.lane],
        "base": dict(task.base),
        "allowed": {
            "stance": list(STANCE_LABELS),
            "operation": list(OPERATION_LABELS),
            "intensity": list(INTENSITY_LABELS),
            "language": list(LANGUAGES),
            "collision_policy": list(COLLISION_POLICIES),
        },
        "response_schema": {
            "schema_version": SYNTHETIC_BATCH_SCHEMA_VERSION,
            "task_id": task.task_id,
            "cases": [
                {
                    "id": "same as blueprint",
                    "lane": "same as blueprint",
                    "group_id": "same as blueprint",
                    "language": "same as blueprint",
                    "input": "new short user request",
                    "expected": {
                        "base_id": "same as blueprint",
                        "base_label": "same as blueprint",
                        "stance": "same as blueprint",
                        "operation": "same as blueprint",
                        "intensity": "same as blueprint",
                    },
                    "collision_policy": "same as blueprint",
                    "judgment_questions": ["question 1", "question 2"],
                    "generation_note": "why this sample fits",
                    "near_miss": {
                        "wrong_base_label": "closest wrong base",
                        "wrong_modifier": "closest wrong modifier if relevant",
                        "why_wrong": "short reason",
                    },
                }
            ],
        },
        "blueprints": [spec.as_dict() for spec in task.specs],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def messages_for_task(task: SyntheticTask) -> list[Dict[str, str]]:
    return [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": _user_prompt(task)},
    ]


def _extract_json(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model response did not contain a JSON object")
    return json.loads(cleaned[start : end + 1])


def _non_empty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _validate_case(case: Mapping[str, Any], spec: SyntheticSpec, field: str) -> Dict[str, Any]:
    required = {
        "id",
        "lane",
        "group_id",
        "language",
        "input",
        "expected",
        "collision_policy",
        "judgment_questions",
        "generation_note",
        "near_miss",
    }
    repaired_case = dict(case)
    warnings = []
    if "generation_note" not in repaired_case:
        repaired_case["generation_note"] = "Generation note missing from model response."
        warnings.append({"kind": "missing_generation_note_repaired"})
    unknown = sorted(set(case) - required)
    missing = sorted(required - set(repaired_case))
    if missing:
        raise ValueError(f"{field} missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"{field} unknown field: {unknown[0]}")
    expected = repaired_case["expected"]
    if not isinstance(expected, Mapping):
        raise ValueError(f"{field}.expected must be an object")
    blueprint = spec.as_dict()
    for key in ("id", "lane", "group_id", "language", "collision_policy"):
        if repaired_case[key] != blueprint[key]:
            if key in {"id", "lane", "group_id", "collision_policy"} and (
                _loose_key(repaired_case[key]) == _loose_key(blueprint[key])
            ):
                warnings.append(
                    {
                        "kind": f"{key}_format_repaired",
                        "actual": repaired_case[key],
                        "expected": blueprint[key],
                    }
                )
                repaired_case[key] = blueprint[key]
            else:
                raise ValueError(f"{field}.{key} differs from blueprint")
    if expected != blueprint["expected"]:
        raise ValueError(f"{field}.expected differs from blueprint")
    input_text = _non_empty(repaired_case["input"], f"{field}.input")
    questions = repaired_case["judgment_questions"]
    if not isinstance(questions, list) or len(questions) != 2:
        raise ValueError(f"{field}.judgment_questions must contain two items")
    for index, question in enumerate(questions):
        _non_empty(question, f"{field}.judgment_questions[{index}]")
    near_miss = repaired_case["near_miss"]
    if not isinstance(near_miss, Mapping):
        raise ValueError(f"{field}.near_miss must be an object")
    _non_empty(repaired_case["generation_note"], f"{field}.generation_note")
    ThoughtColorCode.from_labels(
        base_id=spec.base_id,
        stance=spec.stance,
        operation=spec.operation,
        intensity=spec.intensity,
    )
    normalized = dict(repaired_case)
    normalized["input_sha256"] = hashlib.sha256(input_text.encode("utf-8")).hexdigest()
    normalized["adoption_status"] = "synthetic_review_required"
    normalized["training_allowed"] = False
    normalized["human_review_required"] = True
    if warnings:
        normalized["validation_warnings"] = warnings
    return normalized

def validate_batch_payload(payload: Mapping[str, Any], task: SyntheticTask) -> list[Dict[str, Any]]:
    warnings = []
    if payload.get("schema_version") != SYNTHETIC_BATCH_SCHEMA_VERSION:
        warnings.append(
            {
                "kind": "schema_version_repaired",
                "actual": payload.get("schema_version"),
                "expected": SYNTHETIC_BATCH_SCHEMA_VERSION,
            }
        )
    if payload.get("task_id") != task.task_id:
        if _loose_key(payload.get("task_id")) == _loose_key(task.task_id):
            warnings.append(
                {
                    "kind": "task_id_format_repaired",
                    "actual": payload.get("task_id"),
                    "expected": task.task_id,
                }
            )
        else:
            raise ValueError("task_id mismatch")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != len(task.specs):
        raise ValueError("synthetic batch must contain exactly five cases")
    samples = [
        _validate_case(case, spec, f"cases[{index}]")
        for index, (case, spec) in enumerate(zip(cases, task.specs))
    ]
    if warnings:
        for sample in samples:
            sample["validation_warnings"] = [
                *sample.get("validation_warnings", []),
                *warnings,
            ]
    return samples


def _chat_completion(
    *,
    base_url: str,
    model: str,
    messages: Sequence[Mapping[str, str]],
    temperature: float,
    max_tokens: int,
    timeout: float,
) -> str:
    endpoint = base_url.rstrip("/") + "/v1/chat/completions"
    data = json.dumps(
        {
            "model": model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"].get("content") or ""
    return content


def generate_candidates(
    *,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 5000,
    timeout: float = 180.0,
    limit_batches: int | None = None,
    task_ids: Iterable[str] | None = None,
) -> Dict[str, Any]:
    tasks = build_generation_plan()
    if task_ids is not None:
        requested = set(task_ids)
        tasks = tuple(task for task in tasks if task.task_id in requested)
    if limit_batches is not None:
        tasks = tasks[:limit_batches]
    samples = []
    batches = []
    failures = []
    for task in tasks:
        messages = messages_for_task(task)
        prompt_digest = hashlib.sha256(
            json.dumps(messages, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        try:
            response_text = _chat_completion(
                base_url=base_url,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            payload = _extract_json(response_text)
            batch_samples = validate_batch_payload(payload, task)
        except Exception as error:
            failures.append(
                {
                    "task_id": task.task_id,
                    "lane": task.lane,
                    "base_label": task.base["base_label"],
                    "prompt_sha256": prompt_digest,
                    "error": str(error),
                }
            )
            continue
        for sample in batch_samples:
            sample["source_kind"] = "gemma4_synthetic_contrast"
            sample["source_model"] = model
            sample["source_base_url"] = base_url
            sample["source_task_id"] = task.task_id
            sample["prompt_sha256"] = prompt_digest
        samples.extend(batch_samples)
        batches.append(
            {
                "task_id": task.task_id,
                "lane": task.lane,
                "base_label": task.base["base_label"],
                "sample_count": len(batch_samples),
                "prompt_sha256": prompt_digest,
            }
        )

    return {
        "schema_version": SYNTHETIC_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "base_url": base_url,
        "policy": {
            "synthetic_samples_are_training_data": False,
            "human_review_required_before_training": True,
            "sealed_fixtures_used": False,
        },
        "plan_summary": generation_plan_summary(tasks),
        "batches": batches,
        "failures": failures,
        "samples": samples,
    }


def retry_failures(
    *,
    source_path: Path,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 5000,
    timeout: float = 180.0,
) -> Dict[str, Any]:
    existing = json.loads(source_path.read_text(encoding="utf-8"))
    failed_task_ids = [failure["task_id"] for failure in existing.get("failures", [])]
    retry_payload = generate_candidates(
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        task_ids=failed_task_ids,
    )
    retried = set(failed_task_ids)
    merged = dict(existing)
    merged["created_at"] = datetime.now(timezone.utc).isoformat()
    merged["model"] = model
    merged["base_url"] = base_url
    merged["samples"] = [
        sample
        for sample in existing.get("samples", [])
        if sample.get("source_task_id") not in retried
    ] + retry_payload["samples"]
    merged["batches"] = [
        batch
        for batch in existing.get("batches", [])
        if batch.get("task_id") not in retried
    ] + retry_payload["batches"]
    merged["failures"] = retry_payload["failures"]
    merged["retry_meta"] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source_path),
        "requested_task_count": len(failed_task_ids),
        "resolved_task_count": len(retry_payload["batches"]),
        "remaining_failure_count": len(retry_payload["failures"]),
    }
    return merged

def summarize_candidates(payload: Mapping[str, Any]) -> Dict[str, Any]:
    samples = payload.get("samples", [])
    failures = payload.get("failures", [])
    lane_counts: Dict[str, int] = {}
    base_counts: Dict[str, int] = {}
    for sample in samples:
        lane_counts[sample["lane"]] = lane_counts.get(sample["lane"], 0) + 1
        label = sample["expected"]["base_label"]
        base_counts[label] = base_counts.get(label, 0) + 1
    return {
        "schema_version": "thought-color-synthetic-report.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": payload.get("model", DEFAULT_MODEL),
        "base_url": payload.get("base_url", DEFAULT_BASE_URL),
        "sample_count": len(samples),
        "batch_count": len(payload.get("batches", [])),
        "failure_count": len(failures),
        "validation_warning_count": sum(
            len(sample.get("validation_warnings", [])) for sample in samples
        ),
        "lane_counts": dict(sorted(lane_counts.items())),
        "base_counts": dict(sorted(base_counts.items())),
        "training_allowed_count": sum(
            1 for sample in samples if sample.get("training_allowed")
        ),
        "review_required_count": sum(
            1 for sample in samples if sample.get("human_review_required")
        ),
        "policy": payload.get("policy", {}),
        "output": str(SYNTHETIC_CANDIDATES_PATH),
    }


def write_candidates(payload: Mapping[str, Any]) -> Dict[str, Any]:
    SYNTHETIC_CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_CANDIDATES_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report = summarize_candidates(payload)
    SYNTHETIC_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=5000)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--limit-batches", type=int)
    parser.add_argument("--task-id", action="append", dest="task_ids")
    parser.add_argument("--retry-failures-from", type=Path)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--dry-run-plan", action="store_true")
    args = parser.parse_args(argv)

    if args.retry_failures_from:
        payload = retry_failures(
            source_path=args.retry_failures_from,
            base_url=args.base_url,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
        report = write_candidates(payload)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return

    if args.generate:
        payload = generate_candidates(
            base_url=args.base_url,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            limit_batches=args.limit_batches,
            task_ids=args.task_ids,
        )
        report = write_candidates(payload)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return

    tasks = build_generation_plan()
    if args.limit_batches is not None:
        tasks = tasks[: args.limit_batches]
    summary = generation_plan_summary(tasks)
    if args.dry_run_plan:
        summary["tasks"] = [task.as_dict() for task in tasks]
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()










