"""Replay V4 Failure Memory fixture against the current semantic route()."""

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v4_failure_memory_replay_v1.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"

sys.path.insert(0, str(ROOT))

from semantic_routing import route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso


def _packet_dict(routed: Any) -> dict[str, Any]:
    packet = routed.packet
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
    }


def _matches(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, bool]:
    return {
        "primary_intent": actual["primary_intent"] == expected["primary_intent"],
        "operations": actual["operations"] == expected["operations"],
        "information_state": actual["information_state"] == expected["information_state"],
        "constraints": actual["constraints"] == expected["constraints"],
        "risk": actual["risk"] == expected["risk"],
    }


def _update_adoption(report_path: Path, total: int, exact: int) -> None:
    adoption = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
    for step in adoption.get("sequence", []):
        if step["step"] == 4:
            step["status"] = "completed" if total == exact else "completed_with_misses"
        elif step["step"] == 5:
            step["status"] = "next"
    adoption.setdefault("review_decision", {})["replay_report"] = str(report_path.relative_to(ROOT))
    adoption["review_decision"]["replay_exact_matches"] = exact
    adoption["review_decision"]["replay_total"] = total
    ADOPTION_PATH.write_text(json.dumps(adoption, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    measurements = []
    exact = 0
    for item in fixture["items"]:
        actual = _packet_dict(route(item["input"]))
        field_matches = _matches(actual, item["trigger_packet"])
        exact_match = all(field_matches.values())
        exact += int(exact_match)
        measurements.append(
            {
                "id": item["id"],
                "source_candidate_id": item["source_candidate_id"],
                "mode": item["mode"],
                "exact_match": exact_match,
                "field_matches": field_matches,
                "expected": item["trigger_packet"],
                "actual": actual,
                "guard_action": item["guard_action"],
            }
        )

    report = {
        "schema_version": "v4-failure-memory-replay.v1",
        "generated_at": reproducible_now_iso(),
        "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
        "summary": {
            "item_count": len(measurements),
            "exact_match_count": exact,
            "exact_match_rate": exact / len(measurements) if measurements else 0.0,
            "miss_count": len(measurements) - exact,
        },
        "measurements": measurements,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _update_adoption(REPORT_PATH, len(measurements), exact)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
