"""Compare recovered source baseline against the pyc-output oracle."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORACLE_PATH = ROOT / "build" / "baseline_source_recovery_oracle_v1.json"
REPORT_PATH = ROOT / "build" / "baseline_source_recovery_oracle_comparison_v1.json"

from semantic_routing.baseline import extract_semantic_packet


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    oracle = _load(ORACLE_PATH)
    mismatches = []
    for item in oracle["outputs"]:
        expected = item["packet"]
        actual = extract_semantic_packet(item["input"]).as_dict()
        if actual != expected:
            fields = [key for key in expected if expected.get(key) != actual.get(key)]
            mismatches.append(
                {
                    "fixture": item["fixture"],
                    "case_id": item["case_id"],
                    "request_digest": expected["request_digest"],
                    "fields": fields,
                    "expected_primary": expected["intent_candidates"][0]["intent"],
                    "actual_primary": actual["intent_candidates"][0]["intent"],
                }
            )
    payload = {
        "schema_version": "baseline-source-recovery-oracle-comparison.v1",
        "status": "matched" if not mismatches else "mismatch",
        "case_count": oracle["case_count"],
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:50],
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()