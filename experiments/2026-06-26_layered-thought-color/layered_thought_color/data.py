"""Learning-data copy helpers.

The copied snapshot intentionally excludes sealed cases. This lets the
experiment reuse the human-reviewed visible data without opening any active or
measurement-only sealed lane for tuning.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from .paths import (
    SOURCE_BENCHMARK,
    VISIBLE_BENCHMARK_COPY,
    VISIBLE_BENCHMARK_MANIFEST,
)


VISIBLE_SPLITS = ("train", "validation")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_payload(
    payload: Mapping[str, Any],
    *,
    splits: Iterable[str] = VISIBLE_SPLITS,
) -> Dict[str, Any]:
    selected = set(splits)
    cases = [
        case for case in payload["cases"] if case.get("split") in selected
    ]
    return {
        "schema_version": payload["schema_version"],
        "frozen_at": payload["frozen_at"],
        "authoring_method": (
            payload["authoring_method"]
            + "; copied into Thought Color experiment with sealed cases removed"
        ),
        "review_status": payload["review_status"],
        "policy": (
            "Copied train/validation-only view for Thought Color Code v0.1. "
            "Sealed cases are excluded and must not be used for tuning."
        ),
        "cases": cases,
    }


def copy_visible_benchmark(
    *,
    source_path: Path = SOURCE_BENCHMARK,
    output_path: Path = VISIBLE_BENCHMARK_COPY,
    manifest_path: Path = VISIBLE_BENCHMARK_MANIFEST,
) -> Dict[str, Any]:
    source_payload = json.loads(source_path.read_text(encoding="utf-8"))
    output_payload = visible_payload(source_payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    split_counts: Dict[str, int] = {}
    for case in output_payload["cases"]:
        split_counts[case["split"]] = split_counts.get(case["split"], 0) + 1

    manifest = {
        "schema_version": "thought-color-learning-data-copy.v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source_path),
        "source_sha256": sha256_file(source_path),
        "output": str(output_path),
        "output_sha256": sha256_file(output_path),
        "included_splits": list(VISIBLE_SPLITS),
        "excluded_splits": ["sealed"],
        "case_count": len(output_payload["cases"]),
        "split_counts": split_counts,
        "sealed_cases_copied": False,
        "sealed_labels_used_for_tuning": False,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest

