"""Create the V7 non-sealed curriculum design from aggregate taxonomy.

This is a planning artifact only. It uses the post-v6 aggregate taxonomy and
does not copy sealed v6 text or labels into curriculum examples.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "build"))

from v7_measurement_state import preserve_step8_measurement_state  # noqa: E402

TARGETS_PATH = ROOT / "build" / "v7_targets_and_roadmap_v1.json"
OUTPUT_JSON = ROOT / "build" / "v7_nonsealed_curriculum_plan_v1.json"
OUTPUT_MD = ROOT / "build" / "v7_nonsealed_curriculum_plan_v1.md"
V7_ROADMAP_PATH = ROOT / "docs" / "PLM_V7_ROADMAP.md"
MAIN_ROADMAP_PATH = ROOT / "docs" / "PATTERN_LANGUAGE_MODEL_roadmap.md"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


AXES = [
    {
        "id": "constraint_preservation",
        "priority": 1,
        "minimum_case_count": 18,
        "recommended_case_count": 24,
        "target_fields": ["constraints"],
        "target_metrics": ["constraint_exact_match"],
        "current_metric": 0.607143,
        "minimum_target": 0.821429,
        "expected_minimum_gain_cases": 6,
        "themes": [
            {
                "id": "response_length_preservation",
                "minimum_cases": 4,
                "examples_to_author": [
                    "short answer + non-build direct response",
                    "long explanation request that must not be shortened",
                    "medium summary with explicit scope",
                ],
            },
            {
                "id": "format_preservation",
                "minimum_cases": 4,
                "examples_to_author": [
                    "JSON-only summary",
                    "bullets-only checklist",
                    "no-table timeline summary",
                ],
            },
            {
                "id": "safety_style_constraints",
                "minimum_cases": 4,
                "examples_to_author": [
                    "preserve_neutrality on political/value topics",
                    "avoid_overclaim on future prediction",
                    "general_information_only for legal/license explanation",
                ],
            },
            {
                "id": "cite_sources_and_ask_first",
                "minimum_cases": 4,
                "examples_to_author": [
                    "current-information verification with cite_sources",
                    "ask_first before build when scope is missing",
                    "cite_sources not required for local filename/tag mentions",
                ],
            },
            {
                "id": "constraint_contrast_pairs",
                "minimum_cases": 2,
                "examples_to_author": [
                    "same keyword with and without formatting constraint",
                    "same topic with and without source requirement",
                ],
            },
        ],
    },
    {
        "id": "operation_sequence_repair",
        "priority": 1,
        "minimum_case_count": 18,
        "recommended_case_count": 24,
        "target_fields": ["operations"],
        "target_metrics": ["operation_exact_match"],
        "current_metric": 0.607143,
        "minimum_target": 0.821429,
        "expected_minimum_gain_cases": 6,
        "themes": [
            {
                "id": "clarify_then_build",
                "minimum_cases": 4,
                "examples_to_author": [
                    "create artifact but required columns missing",
                    "write plan but scope/audience missing",
                ],
            },
            {
                "id": "verify_then_search",
                "minimum_cases": 4,
                "examples_to_author": [
                    "latest/current official information",
                    "current legal/license or release reference with source requirement",
                ],
            },
            {
                "id": "explore_then_compare",
                "minimum_cases": 4,
                "examples_to_author": [
                    "compare approaches without choosing single best",
                    "brainstorm options and trade-offs",
                ],
            },
            {
                "id": "build_then_verify",
                "minimum_cases": 3,
                "examples_to_author": [
                    "draft output after checking assumptions",
                    "convert log after sanity check",
                ],
            },
            {
                "id": "verify_then_calculate",
                "minimum_cases": 3,
                "examples_to_author": [
                    "invoice/subtotal arithmetic verification",
                    "rate/budget calculation before report insertion",
                ],
            },
        ],
    },
    {
        "id": "critical_signal_recovery",
        "priority": 1,
        "minimum_case_count": 16,
        "recommended_case_count": 20,
        "target_fields": ["information_state"],
        "target_metrics": ["critical_signal_recall"],
        "current_metric": 0.357143,
        "minimum_target": 0.75,
        "expected_minimum_gain_cases": 6,
        "themes": [
            {
                "id": "unverified_claim_detection",
                "minimum_cases": 5,
                "examples_to_author": [
                    "supposedly/proposed/claimed statements",
                    "user-provided factual claim that needs verification",
                    "medical/legal claim with unsupported assertion",
                ],
            },
            {
                "id": "multiple_intent_detection",
                "minimum_cases": 5,
                "examples_to_author": [
                    "verify then build",
                    "summarize then compare",
                    "clarify then calculate",
                ],
            },
            {
                "id": "missing_information_detection",
                "minimum_cases": 3,
                "examples_to_author": [
                    "estimate without period",
                    "migration without target service",
                    "legal check without jurisdiction",
                ],
            },
            {
                "id": "current_information_split",
                "minimum_cases": 3,
                "examples_to_author": [
                    "true latest/current web information",
                    "local current folder/file status",
                    "word latest used as label or filename",
                ],
            },
        ],
    },
    {
        "id": "clarify_boundary_repair",
        "priority": 2,
        "minimum_case_count": 8,
        "recommended_case_count": 12,
        "target_fields": ["primary_intent", "information_state", "operations"],
        "target_metrics": ["intent_accuracy", "critical_signal_recall"],
        "current_metric": 0.25,
        "minimum_target": 0.75,
        "expected_minimum_gain_cases": 2,
        "themes": [
            {
                "id": "ask_first_before_action",
                "minimum_cases": 3,
                "examples_to_author": [
                    "before drafting ask missing scope",
                    "before migration ask tenant/service",
                ],
            },
            {
                "id": "missing_scope_vs_simple_question",
                "minimum_cases": 3,
                "examples_to_author": [
                    "simple definition should respond",
                    "task request missing target should clarify",
                ],
            },
            {
                "id": "high_risk_clarify_before_verify",
                "minimum_cases": 2,
                "examples_to_author": [
                    "legal/current request missing jurisdiction",
                    "medical safety request missing context",
                ],
            },
        ],
    },
    {
        "id": "risk_ladder_calibration",
        "priority": 2,
        "minimum_case_count": 6,
        "recommended_case_count": 8,
        "target_fields": ["risk"],
        "target_metrics": ["risk_exact_match"],
        "current_metric": 0.75,
        "minimum_target": 0.892857,
        "expected_minimum_gain_cases": 4,
        "themes": [
            {
                "id": "low_risk_contrast",
                "minimum_cases": 2,
                "examples_to_author": [
                    "AI/chat/medical/legal words used as labels",
                    "general explanation only, no advice or adjudication",
                ],
            },
            {
                "id": "medium_current_or_license",
                "minimum_cases": 2,
                "examples_to_author": [
                    "license permission with sources",
                    "current version/release verification",
                ],
            },
            {
                "id": "high_medical_legal",
                "minimum_cases": 2,
                "examples_to_author": [
                    "medical advice safety verification",
                    "current law/contract validity check",
                ],
            },
        ],
    },
    {
        "id": "intent_boundary_stability",
        "priority": 2,
        "minimum_case_count": 6,
        "recommended_case_count": 8,
        "target_fields": ["primary_intent"],
        "target_metrics": ["intent_accuracy"],
        "current_metric": 0.75,
        "minimum_target": 0.892857,
        "expected_minimum_gain_cases": 4,
        "themes": [
            {
                "id": "respond_vs_build",
                "minimum_cases": 2,
                "examples_to_author": [
                    "what is X should respond",
                    "add X to README/table should build",
                ],
            },
            {
                "id": "explain_vs_build",
                "minimum_cases": 1,
                "examples_to_author": [
                    "why/how explanation without artifact request",
                ],
            },
            {
                "id": "clarify_vs_respond_build_verify",
                "minimum_cases": 2,
                "examples_to_author": [
                    "missing info routes to clarify",
                    "complete task routes to build/verify",
                ],
            },
            {
                "id": "explore_vs_respond",
                "minimum_cases": 1,
                "examples_to_author": [
                    "multiple alternatives/tradeoffs should explore",
                ],
            },
        ],
    },
]


def build_payload() -> dict[str, Any]:
    targets = _load_json(TARGETS_PATH)
    minimum_total = sum(axis["minimum_case_count"] for axis in AXES)
    recommended_total = sum(axis["recommended_case_count"] for axis in AXES)
    return {
        "schema_version": "v7-nonsealed-curriculum-plan.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "designed_fixture_next",
        "source": _rel(TARGETS_PATH),
        "policy": {
            "sealed_v6_text_used": False,
            "sealed_v6_labels_used": False,
            "aggregate_taxonomy_only": True,
            "human_review_required": True,
            "draft_lanes_are_diagnostic_only": True,
            "same_cycle_promotion_allowed": False,
        },
        "baseline": targets["baseline"],
        "targets": targets["targets"],
        "required_case_counts": {
            "minimum_total": minimum_total,
            "recommended_total": recommended_total,
            "from_v7_targets_minimum": targets["nonsealed_curriculum_requirements"][
                "minimum_case_count"
            ],
            "from_v7_targets_recommended": targets[
                "nonsealed_curriculum_requirements"
            ]["recommended_case_count"],
        },
        "target_delta": {
            "intent_accuracy": 0.142857,
            "critical_signal_recall": 0.392857,
            "operation_exact_match": 0.214286,
            "constraint_exact_match": 0.214286,
            "risk_exact_match": 0.142857,
            "sealed_error_count_reduction": 13,
        },
        "axes": AXES,
        "authoring_rules": [
            "author fresh non-sealed prompts; do not paraphrase sealed v6 cases",
            "pair positive and negative contrasts for keyword-heavy risk/current cases",
            "include Japanese, English, and mixed-language cases",
            "separate low-risk mention/use cases from actual risk-bearing cases",
            "mark candidate rows as draft until human review",
            "do not use draft/candidate lanes as gate evidence",
        ],
        "acceptance_gates_before_v7_rotation": {
            "visible_plm_exact_required": True,
            "v6_required_nonsealed_lanes_exact_required": True,
            "v7_curriculum_exact_minimum": 0.95,
            "v7_critical_signal_recall_minimum": 0.9,
            "v7_constraint_exact_match_minimum": 0.9,
            "v7_operation_exact_match_minimum": 0.9,
            "v7_risk_exact_match_minimum": 0.9,
            "sealed_overlap_count_required": 0,
        },
        "next_action": "roadmap_v7_step3_create_nonsealed_fixture_and_candidate_replay",
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# V7 Non-Sealed Curriculum Plan v1",
        "",
        "## Policy",
        "",
        "- sealed_v6_text_used: false",
        "- sealed_v6_labels_used: false",
        "- aggregate_taxonomy_only: true",
        "- human_review_required: true",
        "- draft_lanes_are_diagnostic_only: true",
        "",
        "## Case Counts",
        "",
        "| Type | Count |",
        "|---|---:|",
        f"| minimum_total | {payload['required_case_counts']['minimum_total']} |",
        f"| recommended_total | {payload['required_case_counts']['recommended_total']} |",
        "",
        "## Improvement Targets",
        "",
        "| Metric | Required Gain |",
        "|---|---:|",
    ]
    for metric, value in payload["target_delta"].items():
        lines.append(f"| {metric} | {value} |")
    lines.extend(["", "## Required Themes", "", "| Priority | Axis | Minimum | Recommended | Themes |", "|---:|---|---:|---:|---|"])
    for axis in payload["axes"]:
        theme_ids = ", ".join(theme["id"] for theme in axis["themes"])
        lines.append(
            f"| {axis['priority']} | {axis['id']} | {axis['minimum_case_count']} | {axis['recommended_case_count']} | {theme_ids} |"
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "`tests\\fixtures\\v7_router_repair_fixture_v1.json` should be authored from this plan as a non-sealed draft fixture, then replayed diagnostically before human review/adoption.",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _update_v7_roadmap() -> None:
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | next |",
        "| 2 | v7_nonsealed_curriculum_design | `build\\v7_nonsealed_curriculum_plan_v1.json` | completed |",
    )
    roadmap = roadmap.replace(
        "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | pending |",
        "| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\\fixtures\\v7_router_repair_fixture_v1.json` | next |",
    )
    section = (
        "## Step 2 Output\n\n"
        "`build\\v7_nonsealed_curriculum_plan_v1.json` defines the V7 "
        "non-sealed repair curriculum: 72 minimum cases, 96 recommended "
        "cases, six repair axes, authoring rules, and pre-rotation gates. "
        "It uses only aggregate V6 taxonomy and excludes sealed text/labels."
    )
    if "## Step 2 Output" in roadmap:
        head, _ = roadmap.split("## Step 2 Output", 1)
        roadmap = head.rstrip() + "\n\n" + section + "\n"
    else:
        roadmap = roadmap.rstrip() + "\n\n" + section + "\n"
    V7_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")


def _update_main_roadmap(payload: dict[str, Any]) -> None:
    marker = "## PLM V7: Constraint And Critical Signal Recovery"
    main = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    section = f"""
{marker}

Status: V7 Step 2 non-sealed curriculum design completed; Step 3 fixture authoring and candidate replay next.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`
Baseline sealed v6 measurement: `build/pattern_language_sealed_v6_measurement_report.json`

The V7 curriculum plan requires {payload['required_case_counts']['minimum_total']} minimum / {payload['required_case_counts']['recommended_total']} recommended non-sealed cases across constraint preservation, operation sequence repair, critical signal recovery, clarify boundary repair, risk ladder calibration, and intent boundary stability. It uses only aggregate V6 taxonomy; sealed v6 text and labels remain excluded.
""".strip()
    if marker in main:
        head, _ = main.split(marker, 1)
        main = head.rstrip() + "\n\n" + section + "\n"
    else:
        main = main.rstrip() + "\n\n" + section + "\n"
    MAIN_ROADMAP_PATH.write_text(main, encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    _write_json(OUTPUT_JSON, payload)
    _write_markdown(payload)
    _update_v7_roadmap()
    _update_main_roadmap(payload)
    targets = _load_json(TARGETS_PATH)
    roadmap = V7_ROADMAP_PATH.read_text(encoding="utf-8")
    main_doc = MAIN_ROADMAP_PATH.read_text(encoding="utf-8")
    targets, roadmap, main_doc = preserve_step8_measurement_state(ROOT, targets, roadmap, main_doc)
    _write_json(TARGETS_PATH, targets)
    V7_ROADMAP_PATH.write_text(roadmap, encoding="utf-8", newline="\n")
    MAIN_ROADMAP_PATH.write_text(main_doc, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "output": _rel(OUTPUT_JSON),
                "worksheet": _rel(OUTPUT_MD),
                "minimum_total": payload["required_case_counts"]["minimum_total"],
                "recommended_total": payload["required_case_counts"]["recommended_total"],
                "next_action": payload["next_action"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
