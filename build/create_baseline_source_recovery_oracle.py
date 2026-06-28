"""Capture current baseline outputs before removing the pyc loader.

This is a recovery aid, not training data. It records the packet emitted by
the currently importable baseline for fixture inputs so the source rewrite can
be checked for behavioral drift without consulting sealed expected labels.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
OUTPUT = ROOT / "build" / "baseline_source_recovery_oracle_v1.json"
sys.path.insert(0, str(ROOT))

from semantic_routing.baseline import extract_semantic_packet


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _case_texts() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for path in sorted(FIXTURES.glob("*.json")):
        try:
            payload = _read_json(path)
        except Exception:
            continue
        cases = payload.get("cases") if isinstance(payload, dict) else None
        if not isinstance(cases, list):
            continue
        for raw in cases:
            if not isinstance(raw, dict):
                continue
            text = raw.get("input")
            if not isinstance(text, str) or not text.strip():
                continue
            items.append(
                {
                    "fixture": path.name,
                    "case_id": str(raw.get("id", "")),
                    "input": text,
                }
            )
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in items:
        if item["input"] in seen:
            continue
        seen.add(item["input"])
        unique.append(item)
    return unique


def main() -> None:
    cases = _case_texts()
    outputs = []
    for item in cases:
        packet = extract_semantic_packet(item["input"])
        outputs.append(
            {
                "fixture": item["fixture"],
                "case_id": item["case_id"],
                "input": item["input"],
                "packet": packet.as_dict(),
            }
        )

    payload = {
        "schema_version": "baseline-source-recovery-oracle.v1",
        "status": "pyc_loader_behavior_captured",
        "policy": {
            "training_data": False,
            "expected_labels_used": False,
            "purpose": "behavioral regression oracle for source recovery",
        },
        "case_count": len(outputs),
        "outputs": outputs,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "output": str(OUTPUT.relative_to(ROOT)),
                "case_count": len(outputs),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()