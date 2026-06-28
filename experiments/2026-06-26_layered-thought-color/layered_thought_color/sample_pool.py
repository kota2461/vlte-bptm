"""Validation and summary for dedicated Thought Color samples."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from .code import (
    BASE_COUNT,
    INTENSITY_LABELS,
    OPERATION_LABELS,
    STANCE_LABELS,
    ThoughtColorCode,
    collision_profile,
)
from .paths import DATA_DIR


SAMPLE_POOL_SCHEMA_VERSION = "thought-color-sample-pool.v0.1"
DEFAULT_SAMPLE_POOL_PATH = DATA_DIR / "thought_color_sample_pool_v0_1.json"
LANES = (
    "same_base_different_stance",
    "same_base_different_operation",
    "same_operation_different_base",
    "collision_should_share",
    "collision_should_split",
    "missing_context",
    "supportive_modifier",
)
COLLISION_POLICIES = (
    "share_base",
    "share_base_split_modifier",
    "split_base",
    "split_base_share_modifier",
    "share_modifier",
)
LANGUAGES = ("en", "ja", "mixed")


@dataclass(frozen=True)
class ThoughtColorSample:
    case_id: str
    lane: str
    group_id: str
    language: str
    input_text: str
    expected: ThoughtColorCode
    base_label: str
    collision_policy: str
    judgment_questions: Tuple[str, ...]


@dataclass(frozen=True)
class ThoughtColorSamplePool:
    path: Path
    cases: Tuple[ThoughtColorSample, ...]
    base_catalog: Mapping[int, str]

    def summary(self) -> Dict[str, Any]:
        groups: Dict[str, list[ThoughtColorSample]] = defaultdict(list)
        for case in self.cases:
            groups[case.group_id].append(case)
        return {
            "schema_version": "thought-color-sample-pool-summary.v0.1",
            "path": str(self.path),
            "case_count": len(self.cases),
            "lane_counts": dict(sorted(Counter(c.lane for c in self.cases).items())),
            "language_counts": dict(
                sorted(Counter(c.language for c in self.cases).items())
            ),
            "base_counts": {
                self.base_catalog[base_id]: count
                for base_id, count in sorted(
                    Counter(c.expected.base_id for c in self.cases).items()
                )
            },
            "group_count": len(groups),
            "multi_case_group_count": sum(
                1 for samples in groups.values() if len(samples) > 1
            ),
            "collision_profile": collision_profile(
                sample.expected for sample in self.cases
            ),
        }


def _strict_object(
    value: Any,
    field: str,
    required_fields: Sequence[str],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    actual = set(value)
    required = set(required_fields)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing:
        raise ValueError(f"{field} is missing field: {missing[0]}")
    if unknown:
        raise ValueError(f"{field} has unknown field: {unknown[0]}")
    return value


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _string_choice(value: Any, field: str, choices: Sequence[str]) -> str:
    text = _non_empty_string(value, field)
    if text not in choices:
        raise ValueError(f"{field} has unknown value: {text}")
    return text


def _questions(value: Any, field: str) -> Tuple[str, ...]:
    if not isinstance(value, list) or len(value) < 2:
        raise ValueError(f"{field} must contain at least two questions")
    questions = tuple(_non_empty_string(item, field) for item in value)
    if len(set(questions)) != len(questions):
        raise ValueError(f"{field} must be unique")
    return questions


def _base_catalog(raw_items: Any) -> Dict[int, str]:
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("base_catalog must be a non-empty array")
    catalog: Dict[int, str] = {}
    labels = set()
    for index, raw in enumerate(raw_items):
        item = _strict_object(
            raw,
            f"base_catalog[{index}]",
            ("base_id", "base_label", "description"),
        )
        base_id = item["base_id"]
        if isinstance(base_id, bool) or not isinstance(base_id, int):
            raise ValueError("base_id must be an integer")
        if not 0 <= base_id < BASE_COUNT:
            raise ValueError("base_id is outside Base2024")
        label = _non_empty_string(
            item["base_label"],
            f"base_catalog[{index}].base_label",
        )
        if base_id in catalog:
            raise ValueError(f"duplicate base_id: {base_id}")
        if label in labels:
            raise ValueError(f"duplicate base_label: {label}")
        labels.add(label)
        catalog[base_id] = label
    return catalog


def _parse_case(
    raw: Any,
    field: str,
    base_catalog: Mapping[int, str],
) -> ThoughtColorSample:
    payload = _strict_object(
        raw,
        field,
        (
            "id",
            "lane",
            "group_id",
            "language",
            "input",
            "expected",
            "collision_policy",
            "judgment_questions",
        ),
    )
    expected = _strict_object(
        payload["expected"],
        f"{field}.expected",
        ("base_id", "base_label", "stance", "operation", "intensity"),
    )
    base_id = expected["base_id"]
    if isinstance(base_id, bool) or not isinstance(base_id, int):
        raise ValueError(f"{field}.expected.base_id must be an integer")
    if base_id not in base_catalog:
        raise ValueError(f"{field}.expected.base_id is not in base_catalog")
    base_label = _non_empty_string(
        expected["base_label"],
        f"{field}.expected.base_label",
    )
    if base_catalog[base_id] != base_label:
        raise ValueError(f"{field}.expected base label does not match catalog")
    code = ThoughtColorCode.from_labels(
        base_id=base_id,
        stance=_string_choice(
            expected["stance"],
            f"{field}.expected.stance",
            STANCE_LABELS,
        ),
        operation=_string_choice(
            expected["operation"],
            f"{field}.expected.operation",
            OPERATION_LABELS,
        ),
        intensity=_string_choice(
            expected["intensity"],
            f"{field}.expected.intensity",
            INTENSITY_LABELS,
        ),
    )
    return ThoughtColorSample(
        case_id=_non_empty_string(payload["id"], f"{field}.id"),
        lane=_string_choice(payload["lane"], f"{field}.lane", LANES),
        group_id=_non_empty_string(payload["group_id"], f"{field}.group_id"),
        language=_string_choice(payload["language"], f"{field}.language", LANGUAGES),
        input_text=_non_empty_string(payload["input"], f"{field}.input"),
        expected=code,
        base_label=base_label,
        collision_policy=_string_choice(
            payload["collision_policy"],
            f"{field}.collision_policy",
            COLLISION_POLICIES,
        ),
        judgment_questions=_questions(
            payload["judgment_questions"],
            f"{field}.judgment_questions",
        ),
    )


def parse_sample_pool(value: Any, *, path: Path) -> ThoughtColorSamplePool:
    payload = _strict_object(
        value,
        "sample_pool",
        (
            "schema_version",
            "created",
            "purpose",
            "rules",
            "base_catalog",
            "channel_labels",
            "cases",
        ),
    )
    if payload["schema_version"] != SAMPLE_POOL_SCHEMA_VERSION:
        raise ValueError("unsupported sample pool schema")
    base_catalog = _base_catalog(payload["base_catalog"])
    cases_raw = payload["cases"]
    if not isinstance(cases_raw, list) or len(cases_raw) < 24:
        raise ValueError("sample pool must contain at least 24 cases")
    cases = tuple(
        _parse_case(raw, f"cases[{index}]", base_catalog)
        for index, raw in enumerate(cases_raw)
    )
    ids = [case.case_id for case in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("sample ids must be unique")
    inputs = [case.input_text for case in cases]
    if len(set(inputs)) != len(inputs):
        raise ValueError("sample inputs must be unique")
    missing_lanes = sorted(set(LANES) - {case.lane for case in cases})
    if missing_lanes:
        raise ValueError(f"sample pool is missing lane: {missing_lanes[0]}")
    group_counts = Counter(case.group_id for case in cases)
    if not all(count >= 2 for count in group_counts.values()):
        raise ValueError("each group_id must contain at least two cases")
    return ThoughtColorSamplePool(
        path=path,
        cases=cases,
        base_catalog=base_catalog,
    )


def load_sample_pool(path: str | Path = DEFAULT_SAMPLE_POOL_PATH) -> ThoughtColorSamplePool:
    sample_path = Path(path)
    return parse_sample_pool(
        json.loads(sample_path.read_text(encoding="utf-8")),
        path=sample_path,
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_SAMPLE_POOL_PATH,
    )
    args = parser.parse_args(argv)
    pool = load_sample_pool(args.path)
    print(json.dumps(pool.summary(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

