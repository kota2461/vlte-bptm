"""Generate the gate fixture registry (v0.2.2 design, layer 1).

Freezes version + SHA-256 + minimum counts for every gate fixture.
Amending a fixture afterwards requires regenerating this registry with a
new version entry, a reason, and human approval.
"""

import hashlib
import io
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FIXTURE_DIR = Path("tests/fixtures")
OUTPUT = FIXTURE_DIR / "gate_fixture_registry.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    regression_path = FIXTURE_DIR / "pattern_router_cases_v1.json"
    foundation_path = FIXTURE_DIR / "foundation_anchor_suite_v1.json"
    sealed_path = FIXTURE_DIR / "sealed_boundary_slice_v1.json"
    regression = json.loads(regression_path.read_text(encoding="utf-8"))
    foundation = json.loads(foundation_path.read_text(encoding="utf-8"))
    sealed = json.loads(sealed_path.read_text(encoding="utf-8"))

    registry = {
        "schema_version": "gate-fixture-registry.v1",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "rules": [
            "anchors are append-only; deleting or relabeling requires a "
            "new registry version, a reason, and human approval",
            "minimum counts are monotonic: never lowered",
            "sealed-test fixtures join this registry once introduced and "
            "rotate to a new version after being used for tuning",
        ],
        "fixtures": {
            "pattern_router_cases_v1.json": {
                "version": "v1.1",
                "sha256": sha256(regression_path),
                "min_case_count": len(regression),
                "min_route_counts": dict(
                    Counter(case["route"] for case in regression)
                ),
                "amendments": [
                    "2026-06-11 clarify_target text amended (ambiguous "
                    "phrasing; see PATTERN_ROUTER_v0_1_1_spec.md)"
                ],
            },
            "foundation_anchor_suite_v1.json": {
                "version": "v1.0",
                "sha256": sha256(foundation_path),
                "min_case_count": len(foundation["cases"]),
                "min_route_counts": dict(
                    Counter(case["route"] for case in foundation["cases"])
                ),
                "amendments": [],
            },
            "sealed_boundary_slice_v1.json": {
                "version": "v1.0",
                "sha256": sha256(sealed_path),
                "min_case_count": len(sealed["cases"]),
                "min_route_counts": dict(
                    Counter(case["route"] for case in sealed["cases"])
                ),
                "role": "sealed measurement only; NOT a promotion gate check",
                "amendments": [],
            },
        },
    }
    OUTPUT.write_text(
        json.dumps(registry, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    for name, entry in registry["fixtures"].items():
        print(name, entry["version"], entry["sha256"][:12],
              "min:", entry["min_case_count"])


if __name__ == "__main__":
    main()
