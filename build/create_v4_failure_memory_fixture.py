"""Create V4 Failure Memory fixture from reviewed non-sealed selections."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELECTION_PATH = ROOT / "build" / "v4_failure_memory_selection_recommendation_v1.json"
CANDIDATE_PATH = ROOT / "build" / "critical_constraints_candidates_v1.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v4_failure_memory_fixture_v1_report.json"

sys.path.insert(0, str(ROOT))


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _bad_tendencies(candidate: dict[str, Any], decision: str) -> list[str]:
    draft = candidate["draft_expected"]
    info = draft["information_state"]
    constraints = draft["constraints"]
    operations = draft["operations"]
    tendencies: list[str] = []

    if info["missing_required_information"]:
        tendencies.append("respond_without_required_information")
    if info["contains_unverified_claims"]:
        tendencies.append("accept_unverified_claim_without_check")
    if info["requires_current_information"]:
        tendencies.append("answer_with_stale_or_unverified_current_info")
    if info["multiple_intents"]:
        tendencies.append("collapse_compound_intent_into_single_response")
    if "verify" in operations:
        tendencies.append("skip_verification_step")
    if "search" in operations:
        tendencies.append("skip_current_information_lookup")
    if "calculate" in operations:
        tendencies.append("skip_calculation_check")
    if constraints["must"] or constraints["must_not"] or constraints["formats"]:
        tendencies.append("ignore_explicit_constraints")
    if decision == "adopt_context_pair_for_review":
        tendencies.append("treat_error_report_as_bare_status")

    return sorted(set(tendencies)) or ["overconfident_direct_response"]


def _guard_actions(candidate: dict[str, Any], decision: str) -> list[str]:
    draft = candidate["draft_expected"]
    info = draft["information_state"]
    constraints = draft["constraints"]
    operations = draft["operations"]
    intent = draft["primary_intent"]
    risk = draft["risk"]
    actions: list[str] = []

    if intent == "clarify" or info["missing_required_information"]:
        actions.extend(["clarify_up", "ask_first"])
    if info["contains_unverified_claims"] or "verify" in operations:
        actions.extend(["verify_up", "avoid_overclaim"])
    if info["requires_current_information"] or "search" in operations:
        actions.extend(["search_up", "avoid_stale_answer"])
    if info["multiple_intents"]:
        actions.extend(["preserve_multi_intent", "split_or_sequence_operations"])
    if "calculate" in operations:
        actions.append("calculate_check")
    if constraints["must"] or constraints["must_not"] or constraints["formats"]:
        actions.append("preserve_constraints")
    if risk["level"] != "low":
        actions.append("risk_check_up")
    if decision == "adopt_context_pair_for_review":
        actions.extend(
            [
                "inspect_error_context",
                "avoid_status_only_response",
                "ask_for_missing_artifact_if_error_context_absent",
            ]
        )

    return sorted(set(actions)) or ["review_before_response"]


def _severity(candidate: dict[str, Any], decision: str) -> str:
    draft = candidate["draft_expected"]
    info = draft["information_state"]
    operations = draft["operations"]
    risk = draft["risk"]
    if risk["level"] != "low" or info["requires_current_information"]:
        return "major"
    if (
        info["missing_required_information"]
        or info["contains_unverified_claims"]
        or "calculate" in operations
        or decision == "adopt_context_pair_for_review"
    ):
        return "medium"
    return "minor"


def _item_from_selection(index: int, selected: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    decision = selected["decision"]
    mode = "context_pair" if decision == "adopt_context_pair_for_review" else "single"
    trigger = candidate["draft_expected"]
    item = {
        "id": f"fm-v4-{index:03d}",
        "source_candidate_id": selected["id"],
        "source_path": _rel(CANDIDATE_PATH),
        "source_decision": decision,
        "mode": mode,
        "lane": "critical_constraints_review",
        "human_review_status": "approved_for_failure_memory_fixture",
        "training_status": "not_training_data",
        "allowed_use": "nonsealed_failure_memory_replay_only",
        "success_pattern_write_allowed": False,
        "input": candidate["input"],
        "context": [],
        "trigger_packet": trigger,
        "failure_condition": selected["review_focus"],
        "bad_tendency": _bad_tendencies(candidate, decision),
        "guard_action": _guard_actions(candidate, decision),
        "severity": _severity(candidate, decision),
        "reason": selected["reason"],
        "reason_tags": selected["reason_tags"],
        "source_origins": candidate["origins"],
    }
    if mode == "context_pair":
        pair = selected["context_pair"]
        item["context"] = [
            {
                "role": "previous_log_memo",
                "source": pair["context_memo_source"],
                "input": pair["context_memo"]["input"],
                "intent": pair["context_memo"]["intent"],
                "note": pair["context_memo"].get("note"),
            }
        ]
        item["context_pair_pattern"] = pair["pattern"]
        item["context_pair_review_guidance"] = pair["review_guidance"]
    return item


def _update_adoption(selection: dict[str, Any]) -> None:
    adoption = _load(ADOPTION_PATH)
    adoption["status"] = "reviewed_for_failure_memory_fixture_v1"
    adoption["review_decision"] = {
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "selection_recommendation": _rel(SELECTION_PATH),
        "fixture": _rel(FIXTURE_PATH),
        "selected_for_fixture": selection["summary"]["selected_count"],
        "context_pair_count": selection["summary"]["selected_context_pair_count"],
        "excluded_for_now": selection["summary"]["excluded_for_now_count"],
        "notes": [
            "User approved adoption after context-dependence review.",
            "cc-open-v1-057 was excluded as an option-B continuation with weak standalone signal.",
            "cc-open-v1-038 is adopted only as a bounded previous-error-report + verify/check context pair.",
        ],
    }
    adoption.setdefault("summary", {})["selected_for_failure_memory_fixture"] = selection["summary"]["selected_count"]
    adoption["summary"]["context_pair_adoptions"] = selection["summary"]["selected_context_pair_count"]
    for step in adoption.get("sequence", []):
        if step["step"] == 2:
            step["status"] = "completed_by_user_review"
        elif step["step"] == 3:
            step["status"] = "completed"
        elif step["step"] == 4:
            step["status"] = "pending"
        elif step["step"] == 5:
            step["status"] = "pending"
    ADOPTION_PATH.write_text(json.dumps(adoption, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    selection = _load(SELECTION_PATH)
    candidates = {item["id"]: item for item in _load(CANDIDATE_PATH)["candidates"]}
    items = [
        _item_from_selection(index, selected, candidates[selected["id"]])
        for index, selected in enumerate(selection["selected"], start=1)
    ]

    by_severity = Counter(item["severity"] for item in items)
    by_guard_action = Counter(action for item in items for action in item["guard_action"])
    by_mode = Counter(item["mode"] for item in items)
    payload = {
        "schema_version": "v4-failure-memory-fixture.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "adopted_for_nonsealed_replay",
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "sealed_text_used": False,
            "success_pattern_lane_write_allowed": False,
            "human_review_completed": True,
            "context_memo_training_allowed": False,
            "same_cycle_promotion_allowed": False,
        },
        "sources": [
            {
                "name": "selection_recommendation",
                "path": _rel(SELECTION_PATH),
                "sealed": False,
            },
            {
                "name": "critical_constraints_candidates",
                "path": _rel(CANDIDATE_PATH),
                "sealed": False,
            },
        ],
        "summary": {
            "item_count": len(items),
            "context_pair_count": by_mode.get("context_pair", 0),
            "single_count": by_mode.get("single", 0),
            "by_severity": dict(sorted(by_severity.items())),
            "by_guard_action": dict(sorted(by_guard_action.items())),
        },
        "items": items,
    }
    FIXTURE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    report = {
        "schema_version": "v4-failure-memory-fixture-report.v1",
        "generated_at": payload["generated_at"],
        "fixture": _rel(FIXTURE_PATH),
        "selection": _rel(SELECTION_PATH),
        "summary": payload["summary"],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _update_adoption(selection)
    print(json.dumps({"fixture": _rel(FIXTURE_PATH), "report": _rel(REPORT_PATH), "summary": payload["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
