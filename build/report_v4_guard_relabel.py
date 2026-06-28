"""Report V4 guard/relabel implementation coverage against Failure Memory fixture."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"
REPORT_PATH = ROOT / "build" / "v4_guard_relabel_implementation_report.json"

sys.path.insert(0, str(ROOT))

from semantic_routing import route  # noqa: E402


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _update_adoption(summary: dict) -> None:
    adoption = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
    for step in adoption.get("sequence", []):
        if step["step"] == 5:
            step["status"] = "completed"
        elif step["step"] == 6:
            step["status"] = "next"
    adoption.setdefault("review_decision", {})["guard_relabel_report"] = _rel(REPORT_PATH)
    adoption["review_decision"]["guard_relabel_subset_matches"] = summary["guard_subset_match_count"]
    adoption["review_decision"]["guard_relabel_total"] = summary["item_count"]
    ADOPTION_PATH.write_text(json.dumps(adoption, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    measurements = []
    by_severity = Counter()
    subset_matches = 0
    exact_matches = 0
    for item in fixture["items"]:
        guard = route(item["input"]).trace["failure_guard"]
        expected = set(item["guard_action"])
        actual = set(guard["guard_actions"])
        subset_match = expected <= actual
        exact_match = expected == actual
        subset_matches += int(subset_match)
        exact_matches += int(exact_match)
        by_severity[guard["severity"]] += 1
        measurements.append(
            {
                "id": item["id"],
                "source_candidate_id": item["source_candidate_id"],
                "mode": item["mode"],
                "expected_guard_actions": sorted(expected),
                "actual_guard_actions": sorted(actual),
                "missing_guard_actions": sorted(expected - actual),
                "extra_guard_actions": sorted(actual - expected),
                "subset_match": subset_match,
                "exact_match": exact_match,
                "severity": guard["severity"],
                "relabel_hints": guard["relabel_hints"],
                "reason_codes": guard["reason_codes"],
            }
        )

    summary = {
        "item_count": len(measurements),
        "guard_subset_match_count": subset_matches,
        "guard_subset_match_rate": subset_matches / len(measurements) if measurements else 0.0,
        "guard_exact_match_count": exact_matches,
        "guard_exact_match_rate": exact_matches / len(measurements) if measurements else 0.0,
        "by_severity": dict(sorted(by_severity.items())),
    }
    report = {
        "schema_version": "v4-guard-relabel-implementation-report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "success_pattern_lane_write_allowed": False,
            "packet_rewrite_allowed": False,
            "trace_guard_hints_enabled": True,
        },
        "fixture": _rel(FIXTURE_PATH),
        "summary": summary,
        "measurements": measurements,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _update_adoption(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
