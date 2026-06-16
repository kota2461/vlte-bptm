"""Review V2 measurement readiness without opening the sealed fixture."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCUMULATION_REPORT = (
    ROOT / "build" / "conversation_accumulation_v1_report.json"
)
REGISTRY_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
)
OUTPUT_PATH = ROOT / "build" / "v2_measurement_readiness_review.json"


def main() -> None:
    accumulation = json.loads(
        ACCUMULATION_REPORT.read_text(encoding="utf-8")
    )
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    sealed = registry["fixtures"]["pattern_language_sealed_v2.json"]

    blocked_reasons = []
    collection = accumulation["collection"]
    measurements = accumulation["measurements"]
    gates = accumulation["gates"]
    if not collection["collection_stop_reached"]:
        blocked_reasons.append("collection_stop_not_reached")
    if not gates["review_gate_met"]:
        blocked_reasons.append("human_review_gate_not_met")
    if not gates["accuracy_gate_met"]:
        blocked_reasons.append("accuracy_gate_not_met")
    if not gates["critical_underprocessing_gate_met"]:
        blocked_reasons.append("critical_underprocessing_gate_not_met")
    if gates["visible_benchmark_overlap_count"] != 0:
        blocked_reasons.append("visible_benchmark_overlap_detected")
    if sealed["status"] != "active" or sealed["measured"]:
        blocked_reasons.append("sealed_fixture_not_available")

    decision = "eligible" if not blocked_reasons else "blocked"
    report = {
        "schema_version": "v2-measurement-readiness-review.v1",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "candidate": accumulation["candidate"],
        "decision": decision,
        "sealed_fixture_opened": False,
        "sealed_fixture": {
            "registry_name": "pattern_language_sealed_v2.json",
            "sha256": sealed["sha256"],
            "case_count": sealed["case_count"],
            "status": sealed["status"],
            "measured": sealed["measured"],
            "reviewed": sealed["reviewed"],
        },
        "readiness": {
            "case_count": collection["case_count"],
            "target_case_count": collection["target_case_count"],
            "reviewed_count": collection["reviewed_count"],
            "required_reviewed_count": collection[
                "required_reviewed_count"
            ],
            "end_to_end_route_accuracy": measurements[
                "end_to_end_route_accuracy"
            ],
            "required_end_to_end_route_accuracy": 0.9,
            "critical_underprocessing": measurements[
                "critical_underprocessing"
            ],
            "allowed_critical_underprocessing": 0,
        },
        "blocked_reasons": blocked_reasons,
        "next_review_condition": (
            "2026-06-20T23:59:59+09:00 or 50 collected cases, "
            "whichever occurs first; at least 40 human-approved cases"
        ),
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
