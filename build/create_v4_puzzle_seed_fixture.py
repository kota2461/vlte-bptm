"""Create V4 non-sealed puzzle task seed fixture."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v4_puzzle_task_seed_v1.json"
REPORT_PATH = ROOT / "build" / "v4_puzzle_task_seed_report.json"
ADOPTION_PATH = ROOT / "build" / "v4_failure_memory_adoption_v1.json"

sys.path.insert(0, str(ROOT))

from semantic_routing.puzzle_task import (  # noqa: E402
    PUZZLE_DOMAINS,
    PUZZLE_EXPECTED_ROUTES,
    PUZZLE_OPERATIONS,
    parse_puzzle_task_seed,
)


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _task(
    task_id: str,
    *,
    language: str,
    domain: str,
    difficulty: str,
    input_text: str,
    route: str,
    answer: str | None,
    answer_type: str,
    rationale_tags: list[str],
    operations: list[str],
    ambiguous: bool = False,
    missing: bool = False,
    ambiguity_notes: list[str] | None = None,
    response_format: str = "answer_then_brief_reason",
    max_steps: int = 4,
    allow_multiple_answers: bool = False,
    bad_tendency: list[str] | None = None,
    guard_action: list[str] | None = None,
    severity: str = "minor",
) -> dict[str, Any]:
    return {
        "id": task_id,
        "language": language,
        "domain": domain,
        "difficulty": difficulty,
        "input": input_text,
        "expected": {
            "route": route,
            "answer": answer,
            "answer_type": answer_type,
            "rationale_tags": rationale_tags,
        },
        "allowed_reasoning_operations": operations,
        "ambiguity": {
            "ambiguous": ambiguous,
            "missing_required_information": missing,
            "notes": ambiguity_notes or [],
        },
        "constraints": {
            "response_format": response_format,
            "max_steps": max_steps,
            "allow_multiple_answers": allow_multiple_answers,
        },
        "guard_expectations": {
            "on_failure_bad_tendency": bad_tendency or [
                "guess_without_checking_constraints"
            ],
            "guard_action": guard_action or [
                "parse_conditions_first",
                "show_minimal_reasoning",
            ],
            "severity": severity,
        },
        "review_status": "draft",
        "training_status": "not_training_data",
        "allowed_use": "nonsealed_puzzle_seed_replay_only",
    }


def _seed_tasks() -> list[dict[str, Any]]:
    return [
        _task(
            "puzzle-v4-seed-001",
            language="en",
            domain="sequence",
            difficulty="easy",
            input_text="What number comes next: 2, 4, 8, 16, ?",
            route="solve",
            answer="32",
            answer_type="number",
            rationale_tags=["doubling_sequence"],
            operations=["pattern_detect", "calculate"],
        ),
        _task(
            "puzzle-v4-seed-002",
            language="ja",
            domain="arithmetic",
            difficulty="easy",
            input_text="??3?????????????4??????5???????????????",
            route="solve",
            answer="7",
            answer_type="number",
            rationale_tags=["multiply_then_subtract"],
            operations=["parse_conditions", "calculate"],
        ),
        _task(
            "puzzle-v4-seed-003",
            language="en",
            domain="logic",
            difficulty="medium",
            input_text="All zibs are nols. Some nols are blue. Can we conclude that some zibs are blue?",
            route="solve",
            answer="No",
            answer_type="choice",
            rationale_tags=["insufficient_syllogism"],
            operations=["parse_conditions", "deduce"],
            bad_tendency=["overinfer_from_some_statement"],
            guard_action=["avoid_overclaim", "deduce_from_given_conditions_only"],
            severity="medium",
        ),
        _task(
            "puzzle-v4-seed-004",
            language="ja",
            domain="constraint_satisfaction",
            difficulty="easy",
            input_text="A?B???????B?C??????????????????????",
            route="solve",
            answer="C",
            answer_type="choice",
            rationale_tags=["transitive_order"],
            operations=["parse_conditions", "deduce"],
        ),
        _task(
            "puzzle-v4-seed-005",
            language="en",
            domain="constraint_satisfaction",
            difficulty="medium",
            input_text="A, B, and C sit in one row. A is right of B. B is right of C. What is the order from left to right?",
            route="solve",
            answer="C-B-A",
            answer_type="ordering",
            rationale_tags=["linear_order_constraints"],
            operations=["parse_conditions", "deduce", "preserve_constraints"],
            max_steps=5,
        ),
        _task(
            "puzzle-v4-seed-006",
            language="en",
            domain="language",
            difficulty="easy",
            input_text="Which word does not belong: triangle, square, circle, apple?",
            route="solve",
            answer="apple",
            answer_type="text",
            rationale_tags=["category_outlier"],
            operations=["compare", "deduce"],
        ),
        _task(
            "puzzle-v4-seed-007",
            language="ja",
            domain="sequence",
            difficulty="easy",
            input_text="????????: 1, 1, 2, 3, 5, ?",
            route="solve",
            answer="8",
            answer_type="number",
            rationale_tags=["fibonacci_sequence"],
            operations=["pattern_detect", "calculate"],
        ),
        _task(
            "puzzle-v4-seed-008",
            language="en",
            domain="arithmetic",
            difficulty="easy",
            input_text="A train leaves at 9:00 and the trip takes 45 minutes. What time does it arrive?",
            route="solve",
            answer="9:45",
            answer_type="time",
            rationale_tags=["time_addition"],
            operations=["parse_conditions", "calculate"],
        ),
        _task(
            "puzzle-v4-seed-009",
            language="en",
            domain="logic",
            difficulty="easy",
            input_text="The red key opens only the red door. Which key opens the red door?",
            route="solve",
            answer="red key",
            answer_type="text",
            rationale_tags=["direct_condition"],
            operations=["parse_conditions", "deduce"],
        ),
        _task(
            "puzzle-v4-seed-010",
            language="en",
            domain="constraint_satisfaction",
            difficulty="easy",
            input_text="Mia is left of Noor. Noor is left of Omar. Who is in the middle?",
            route="solve",
            answer="Noor",
            answer_type="text",
            rationale_tags=["linear_middle"],
            operations=["parse_conditions", "deduce"],
        ),
        _task(
            "puzzle-v4-seed-011",
            language="en",
            domain="ambiguous",
            difficulty="medium",
            input_text="What is the next number: 1, 2, 4, ?",
            route="clarify",
            answer="Ask which rule should be used before solving.",
            answer_type="clarification",
            rationale_tags=["multiple_sequence_rules_possible"],
            operations=["pattern_detect", "ask_clarify"],
            ambiguous=True,
            ambiguity_notes=["multiple_rules_possible"],
            response_format="clarifying_question",
            allow_multiple_answers=True,
            bad_tendency=["guess_single_rule_for_ambiguous_sequence"],
            guard_action=["ask_clarify", "avoid_unjustified_guess"],
            severity="medium",
        ),
        _task(
            "puzzle-v4-seed-012",
            language="ja",
            domain="ambiguous",
            difficulty="medium",
            input_text="????????? 3, 6, ? ?????????",
            route="clarify",
            answer="Ask for the previously discussed rule before solving.",
            answer_type="clarification",
            rationale_tags=["missing_prior_rule"],
            operations=["ask_clarify", "preserve_constraints"],
            missing=True,
            ambiguity_notes=["prior_rule_missing"],
            response_format="clarifying_question",
            bad_tendency=["use_missing_thread_context_as_if_known"],
            guard_action=["ask_clarify", "avoid_context_fabrication"],
            severity="medium",
        ),
    ]


def _summary(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "task_count": len(tasks),
        "ambiguous_count": sum(task["ambiguity"]["ambiguous"] for task in tasks),
        "missing_info_count": sum(
            task["ambiguity"]["missing_required_information"] for task in tasks
        ),
        "by_domain": dict(sorted(Counter(task["domain"] for task in tasks).items())),
        "by_expected_route": dict(
            sorted(Counter(task["expected"]["route"] for task in tasks).items())
        ),
        "by_difficulty": dict(
            sorted(Counter(task["difficulty"] for task in tasks).items())
        ),
    }


def _update_adoption(summary: dict[str, Any]) -> None:
    adoption = json.loads(ADOPTION_PATH.read_text(encoding="utf-8"))
    adoption.setdefault("review_decision", {})["puzzle_task_seed_fixture"] = _rel(FIXTURE_PATH)
    adoption["review_decision"]["puzzle_task_seed_report"] = _rel(REPORT_PATH)
    adoption["review_decision"]["puzzle_task_seed_count"] = summary["task_count"]
    adoption["review_decision"]["puzzle_task_seed_clarify_count"] = summary["by_expected_route"].get("clarify", 0)
    adoption.setdefault("summary", {})["puzzle_task_seed_items"] = summary["task_count"]
    adoption["summary"]["puzzle_task_seed_clarify_items"] = summary["by_expected_route"].get("clarify", 0)
    for step in adoption.get("sequence", []):
        if step["step"] == 6:
            step["status"] = "completed"
        elif step["step"] == 7:
            step["status"] = "next"
    ADOPTION_PATH.write_text(json.dumps(adoption, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    tasks = _seed_tasks()
    summary = _summary(tasks)
    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "v4-puzzle-task-seed.v1",
        "generated_at": generated_at,
        "status": "draft_seed",
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "v3_sealed_text_used": False,
            "success_pattern_lane_write_allowed": False,
            "failures_enter_failure_memory_first": True,
            "human_review_required_before_training": True,
            "same_cycle_promotion_allowed": False,
        },
        "schema": {
            "task_required_fields": [
                "id",
                "language",
                "domain",
                "difficulty",
                "input",
                "expected",
                "allowed_reasoning_operations",
                "ambiguity",
                "constraints",
                "guard_expectations",
                "review_status",
                "training_status",
                "allowed_use",
            ],
            "allowed_domains": list(PUZZLE_DOMAINS),
            "allowed_operations": list(PUZZLE_OPERATIONS),
            "expected_routes": list(PUZZLE_EXPECTED_ROUTES),
        },
        "summary": summary,
        "tasks": tasks,
    }
    parsed = parse_puzzle_task_seed(payload)
    FIXTURE_PATH.write_text(json.dumps(parsed.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    report = {
        "schema_version": "v4-puzzle-task-seed-report.v1",
        "generated_at": generated_at,
        "fixture": _rel(FIXTURE_PATH),
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "success_pattern_lane_write_allowed": False,
            "solver_trace_generated": False,
            "failure_memory_generated": False,
        },
        "summary": summary,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _update_adoption(summary)
    print(json.dumps({"fixture": _rel(FIXTURE_PATH), "report": _rel(REPORT_PATH), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
