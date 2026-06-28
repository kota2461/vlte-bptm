"""Demo output for the layered thought color experiment."""

from __future__ import annotations

import json

from .code import (
    BASE_COUNT,
    ThoughtColorCode,
    collision_profile,
    raw_capacity,
    valid_capacity,
)


def main() -> None:
    examples = (
        ThoughtColorCode.from_labels(
            base_id=42,
            stance="explore",
            operation="verify",
            intensity="medium",
        ),
        ThoughtColorCode.from_labels(
            base_id=42,
            stance="clarify",
            operation="respond",
            intensity="low",
        ),
        ThoughtColorCode.from_labels(
            base_id=513,
            stance="empathize",
            operation="reason",
            intensity="hold",
        ),
    )
    payload = {
        "schema_version": ThoughtColorCode.SCHEMA_VERSION,
        "base_count": BASE_COUNT,
        "raw_capacity": raw_capacity(),
        "valid_capacity": valid_capacity(),
        "examples": [example.as_dict() for example in examples],
        "collision_profile": collision_profile(examples),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

