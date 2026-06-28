"""Adopt V10 Thought Color bridge candidates as isolated rewrites.

The user approved the 72 primary_review bridge candidates for provisional
testing. Thought Color rows remain experiment-only boundary judgments; this
script rewrites their packet hints into short mainline semantic-packet samples,
keeps the fixture quarantined from training/gate use, and replays the current
router diagnostically.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso

SOURCE_SELECTION_PATH = ROOT / "build" / "v10_thought_color_bridge_candidate_selection_v1.json"
ISOLATED_BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "v10_thought_color_bridge_isolated_benchmark_v1.json"
ADOPTION_DECISION_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_adoption_decision_v1.json"
REPLAY_REPORT_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_replay_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v10_thought_color_bridge_isolated_worksheet_v1.md"

POLICY = {
    "source_scope": "thought_color_experiment_only",
    "source_mainline_training_allowed": False,
    "source_experiment_training_allowed": True,
    "sealed_fixtures_used_as_sources": False,
    "sealed_text_used": False,
    "sealed_labels_used": False,
    "bridge_selection_used_for_rewrite": True,
    "raw_thought_color_samples_direct_training_allowed": False,
    "isolated_rewrite_fixture_training_allowed": False,
    "isolated_replay_only": True,
    "human_review_confirmation_recorded": True,
    "same_cycle_promotion_allowed": False,
    "current_route_measurement_is_gate": False,
}

INTENT_ACTION = {
    "respond": "Answer the practical request",
    "explain": "Explain the concept at a general level",
    "clarify": "Ask the missing-context question",
    "build": "Draft the requested artifact",
    "verify": "Check the claim or plan",
    "summarize": "Summarize the decisions",
    "explore": "Compare the trade-offs",
}

TOPICS = (
    "a roadmap note",
    "a review worksheet",
    "a candidate fixture",
    "a release note",
    "a benchmark report",
    "a UI design note",
    "a model-routing memo",
    "a local project log",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def _expected_from_hint(hint: dict[str, Any]) -> dict[str, Any]:
    constraints = hint["constraints_hint"]
    information = hint["information_state_hint"]
    risk = hint["risk_hint"]
    return {
        "primary_intent": hint["primary_intent_hint"],
        "operations": hint["operations_hint"],
        "information_state": {
            "missing_required_information": bool(information["missing_required_information"]),
            "contains_unverified_claims": bool(information["contains_unverified_claims"]),
            "requires_current_information": bool(information["requires_current_information"]),
            "multiple_intents": bool(information["multiple_intents"]),
        },
        "constraints": {
            "response_length": constraints.get("response_length", "unspecified"),
            "formats": constraints.get("formats", []),
            "must": constraints.get("must", []),
            "must_not": constraints.get("must_not", []),
        },
        "risk": {
            "level": risk["level"],
            "flags": risk.get("flags", []),
        },
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


def _constraint_sentence(must: list[str]) -> str | None:
    if not must:
        return None
    fragments = []
    if "ask_first" in must:
        fragments.append("ask before answering if a required detail is missing")
    if "avoid_overclaim" in must:
        fragments.append("avoid overclaiming")
    if "supportive_tone" in must:
        fragments.append("keep a supportive tone")
    if "defer_or_verify" in must:
        fragments.append("defer or verify before giving a firm answer")
    if not fragments:
        fragments = [f"respect the {item} constraint" for item in must]
    return "Please " + ", and ".join(fragments) + "."


def _category_frame(category: str) -> str:
    return {
        "constraint_bridge": "The main issue is a response constraint boundary.",
        "information_state_bridge": "The main issue is missing or uncertain context.",
        "intent_boundary_bridge": "The wording is near another intent, but the main request must stay stable.",
        "operation_bridge": "The main issue is the terminal operation and operation order.",
        "risk_bridge": "The main issue is risk calibration without overfiring.",
    }[category]


def _rewrite_input(row: dict[str, Any], index: int) -> str:
    hint = row["semantic_packet_bridge_hint"]
    intent = hint["primary_intent_hint"]
    operations = hint["operations_hint"]
    information = hint["information_state_hint"]
    risk = hint["risk_hint"]
    must = hint["constraints_hint"].get("must", [])
    topic = TOPICS[(index - 1) % len(TOPICS)]

    sentences = [
        f"Bridge rewrite case {index:03d}.",
        _category_frame(row["bridge_category"]),
        f"{INTENT_ACTION[intent]} for {topic}.",
    ]

    if len(operations) > 1:
        sentences.append(f"Use this operation order: {', '.join(operations)}.")
    elif operations:
        sentences.append(f"Keep the terminal operation as {operations[0]}.")

    if information["missing_required_information"]:
        sentences.append("Important context is missing.")
    if information["contains_unverified_claims"]:
        sentences.append("The key claim is not verified yet.")
    if information["requires_current_information"]:
        sentences.append("Current external information is required.")
    if information["multiple_intents"]:
        sentences.append("There are multiple requested actions, so do not collapse them into one.")

    constraint = _constraint_sentence(must)
    if constraint:
        sentences.append(constraint)

    if risk["level"] != "low":
        sentences.append(f"Treat the risk level as {risk['level']}.")
    if risk.get("flags"):
        sentences.append(f"Risk flags: {', '.join(risk['flags'])}.")

    return " ".join(sentences)


def _build_cases(primary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    source_inputs = {_normalize(row["input"]) for row in primary_rows}
    for index, row in enumerate(primary_rows, start=1):
        rewritten_input = _rewrite_input(row, index)
        if _normalize(rewritten_input) in source_inputs:
            raise ValueError("rewritten input must not equal a Thought Color source input")
        cases.append(
            {
                "id": f"v10-thought-color-bridge-isolated-{index:03d}",
                "split": "validation",
                "source_group": "v10-thought-color-bridge-isolated-rewrite-nonsealed",
                "contrast_group": row["bridge_category"],
                "language": row.get("language", "en"),
                "input": rewritten_input,
                "expected": _expected_from_hint(row["semantic_packet_bridge_hint"]),
            }
        )
    return cases


def _case_results(benchmark_cases) -> list[dict[str, Any]]:
    results = []
    for case in benchmark_cases:
        prediction = route(case.input_text).packet
        expected = case.expected.as_dict()
        packet = prediction.as_dict()
        predicted = {
            "primary_intent": packet["intent_candidates"][0]["intent"],
            "operations": packet["operations"],
            "information_state": packet["information_state"],
            "constraints": packet["constraints"],
            "risk": packet["risk"],
        }
        fields = []
        if predicted["primary_intent"] != expected["primary_intent"]:
            fields.append("primary_intent")
        if predicted["operations"] != expected["operations"]:
            fields.append("operations")
        for signal in (
            "missing_required_information",
            "contains_unverified_claims",
            "requires_current_information",
            "multiple_intents",
        ):
            if predicted["information_state"][signal] != expected["information_state"][signal]:
                fields.append(signal)
        if predicted["constraints"] != expected["constraints"]:
            fields.append("constraints")
        if predicted["risk"] != expected["risk"]:
            fields.append("risk")
        results.append(
            {
                "case_id": case.case_id,
                "contrast_group": case.contrast_group,
                "fields": fields,
                "expected": expected,
                "predicted": predicted,
            }
        )
    return results


def build_outputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    selection = _load(SOURCE_SELECTION_PATH)
    primary_rows = selection["primary_review"]
    if selection["policy"]["source_mainline_training_allowed"] is not False:
        raise ValueError("Thought Color source must not be mainline training data")
    if len(primary_rows) != 72:
        raise ValueError("expected exactly 72 V10 bridge primary-review rows")
    if any(row["training_status"] != "not_training_data" for row in primary_rows):
        raise ValueError("bridge rows must be review-only before rewrite adoption")

    cases = _build_cases(primary_rows)
    now = reproducible_now_iso()
    benchmark_payload = {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": now,
        "authoring_method": (
            "User-approved V10 Thought Color bridge primary_review rows rewritten "
            "from packet hints into isolated non-sealed mainline samples; raw "
            "Thought Color inputs are not copied into the fixture."
        ),
        "review_status": "human_reviewed",
        "policy": (
            "Quarantined V10 bridge replay lane. Thought Color sources are experiment-only "
            "boundary judgments; raw rows are not direct training data. This isolated "
            "fixture is not trainable, not sealed, not gate evidence, and not same-cycle "
            "promotion evidence."
        ),
        "cases": cases,
    }

    benchmark = parse_plm_benchmark(benchmark_payload)
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    case_results = _case_results(benchmark.cases)
    category_counts = Counter(row["bridge_category"] for row in primary_rows)

    decision = {
        "schema_version": "v10-thought-color-bridge-isolated-adoption-decision.v1",
        "generated_at": now,
        "status": "adopted_for_isolated_provisional_replay",
        "review_status": "human_reviewed_for_isolated_rewrite",
        "adopted_count": len(primary_rows),
        "selected_candidate_ids": [row["id"] for row in primary_rows],
        "selected_source_sample_ids": [row["source_sample_id"] for row in primary_rows],
        "category_counts": dict(sorted(category_counts.items())),
        "source_selection": str(SOURCE_SELECTION_PATH.relative_to(ROOT)),
        "isolated_benchmark": str(ISOLATED_BENCHMARK_PATH.relative_to(ROOT)),
        "replay_report": str(REPLAY_REPORT_PATH.relative_to(ROOT)),
        "policy": POLICY,
    }

    replay_report = {
        "schema_version": "v10-thought-color-bridge-isolated-replay-report.v1",
        "generated_at": now,
        "status": "completed_with_provisional_scores",
        "source_selection": str(SOURCE_SELECTION_PATH.relative_to(ROOT)),
        "isolated_benchmark": str(ISOLATED_BENCHMARK_PATH.relative_to(ROOT)),
        "sealed_fixture_used": False,
        "current_route_measurement_is_gate": False,
        "isolated_rewrite_fixture_training_allowed": False,
        "summary": {
            "adopted_count": len(primary_rows),
            "category_counts": dict(sorted(category_counts.items())),
            "source_inputs_copied_verbatim": False,
        },
        "measurement": {key: value for key, value in measurement.items() if key != "errors"},
        "case_results": case_results,
        "next_step": "review_route_gaps_before_any_v10_training_or_gate_use",
    }
    replay_report["measurement"]["error_count"] = len(measurement["errors"])
    replay_report["measurement"]["error_field_counts"] = dict(
        sorted(Counter(field for error in measurement["errors"] for field in error["fields"]).items())
    )
    return decision, benchmark_payload, replay_report


def write_worksheet(decision: dict[str, Any], benchmark_payload: dict[str, Any], replay_report: dict[str, Any]) -> None:
    lines = [
        "# V10 Thought Color Bridge Isolated Worksheet v1",
        "",
        "These cases are rewritten bridge samples for provisional replay only.",
        "",
        "## Contract",
        "",
    ]
    for key, value in decision["policy"].items():
        lines.append(f"- {key}: {str(value).lower() if isinstance(value, bool) else value}")
    lines.extend(
        [
            "",
            "## Replay Summary",
            "",
            f"- adopted_count: {decision['adopted_count']}",
            f"- category_counts: {decision['category_counts']}",
            f"- current_route_measurement_is_gate: {str(replay_report['current_route_measurement_is_gate']).lower()}",
            f"- error_count: {replay_report['measurement']['error_count']}",
            f"- intent_accuracy: {replay_report['measurement']['intent_accuracy']}",
            f"- operation_exact_match: {replay_report['measurement']['operation_exact_match']}",
            f"- constraint_exact_match: {replay_report['measurement']['constraint_exact_match']}",
            f"- risk_exact_match: {replay_report['measurement']['risk_exact_match']}",
            "",
            "## Rewritten Cases",
            "",
            "| id | category | input | expected intent | expected operations | expected risk |",
            "|---|---|---|---|---|---|",
        ]
    )
    for case in benchmark_payload["cases"]:
        expected = case["expected"]
        text = case["input"].replace("|", "&#124;")
        lines.append(
            f"| {case['id']} | {case['contrast_group']} | {text} | "
            f"{expected['primary_intent']} | {','.join(expected['operations'])} | {expected['risk']['level']} |"
        )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    decision, benchmark_payload, replay_report = build_outputs()
    _write_json(ADOPTION_DECISION_PATH, decision)
    _write_json(ISOLATED_BENCHMARK_PATH, benchmark_payload)
    _write_json(REPLAY_REPORT_PATH, replay_report)
    write_worksheet(decision, benchmark_payload, replay_report)
    print(
        json.dumps(
            {
                "status": decision["status"],
                "adopted_count": decision["adopted_count"],
                "isolated_benchmark": str(ISOLATED_BENCHMARK_PATH.relative_to(ROOT)),
                "replay_report": str(REPLAY_REPORT_PATH.relative_to(ROOT)),
                "measurement": replay_report["measurement"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

