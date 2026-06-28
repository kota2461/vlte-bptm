"""Create a V11 audit for literal-regex profile patch overfit.

This records a root-cause finding from the baseline pyc recovery inspection:
v6-v9 profile layers were largely fixture-specific regex patches, not a robust
general routing model. The report is diagnostic metadata only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INSPECTION_PATH = ROOT / "build" / "baseline_pyc_recovery_inspection_v1.json"
DISASSEMBLY_PATH = ROOT / "build" / "baseline_pyc_recovery_disassembly_v1.txt"
OUTPUT_JSON = ROOT / "build" / "v11_profile_literal_patch_audit_v1.json"
OUTPUT_MD = ROOT / "build" / "v11_profile_literal_patch_audit_v1.md"

PROFILE_FUNCTIONS = [
    "_v7_generalization_profile",
    "_v8_recovery_profile",
    "_v9_primary_review_profile",
    "_v9_constraint_operation_extension_profile",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        found: list[str] = []
        for item in value:
            found.extend(_collect_strings(item))
        return found
    if isinstance(value, dict):
        found: list[str] = []
        for item in value.values():
            found.extend(_collect_strings(item))
        return found
    return []


def _looks_like_regex_literal(value: str) -> bool:
    markers = ("\\b", "(?<", "(?!", ".*", "\\d", "\\w", "|", "[", "]")
    return any(marker in value for marker in markers)


def _looks_fixture_specific(value: str) -> bool:
    if not _looks_like_regex_literal(value):
        return False
    stripped = value.replace("\\b", "").replace("\\-", "-").replace("\\/", "/")
    alpha_words = [part for part in stripped.replace(".", " ").replace("?", " ").split() if any(ch.isalpha() for ch in part)]
    return len(alpha_words) >= 3


def _function_report(name: str, function: dict[str, Any]) -> dict[str, Any]:
    strings = _collect_strings(function.get("consts", []))
    regex_literals = [item for item in strings if _looks_like_regex_literal(item)]
    fixture_like = [item for item in regex_literals if _looks_fixture_specific(item)]
    names = set(function.get("names", []))
    return {
        "firstlineno": function.get("firstlineno"),
        "instruction_count": function.get("instruction_count"),
        "docstring": strings[0] if strings else None,
        "string_constant_count": len(strings),
        "regex_literal_count": len(regex_literals),
        "fixture_like_regex_literal_count": len(fixture_like),
        "uses_regex_evidence_helper": "_any_regex_evidence" in names,
        "uses_direct_re_search": "search" in names and "re" in names,
        "uses_v9_override": "_v9_override" in names,
        "example_regex_literals": regex_literals[:8],
    }


def build_payload() -> dict[str, Any]:
    inspection = _load_json(INSPECTION_PATH)
    functions = inspection["functions"]
    profiles = {
        name: _function_report(name, functions[name])
        for name in PROFILE_FUNCTIONS
        if name in functions
    }
    total_fixture_like = sum(item["fixture_like_regex_literal_count"] for item in profiles.values())
    total_regex = sum(item["regex_literal_count"] for item in profiles.values())
    decompilation = {
        "status": "partial_only",
        "automatic_decompilation_failed_functions": 3,
        "automatic_decompilation_attempted_functions": 6,
        "known_failure_reason": "dictionary/set comprehension opcodes were not handled by the external decompiler scan",
        "policy": "do not treat partial decompile as authoritative source; use source recovery plus regression oracle",
    }
    return {
        "schema_version": "v11-profile-literal-patch-audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "literal_profile_patch_overfit_confirmed",
        "policy": {
            "diagnostic_only": True,
            "mutates_router": False,
            "writes_training_data": False,
            "opens_active_sealed_fixture": False,
            "uses_sealed_labels_for_tuning": False,
        },
        "sources": {
            "pyc_inspection": str(INSPECTION_PATH.relative_to(ROOT)).replace("\\", "/"),
            "pyc_disassembly": str(DISASSEMBLY_PATH.relative_to(ROOT)).replace("\\", "/"),
            "external_decompile_review": "user-provided decompile scan summary",
        },
        "finding": {
            "id": "literal_profile_patch_overfit",
            "priority": "P0",
            "confirmed": True,
            "summary": "v6-v9 profile layers are dominated by specific literal-regex repair patches rather than general routing logic",
            "root_cause_for_v10_transfer_gap": True,
            "total_regex_literal_count_in_profile_inspection": total_regex,
            "total_fixture_like_regex_literal_count": total_fixture_like,
            "evidence": {
                "v9_primary_review_docstring": profiles.get("_v9_primary_review_profile", {}).get("docstring"),
                "v9_extension_docstring": profiles.get("_v9_constraint_operation_extension_profile", {}).get("docstring"),
                "profiles": profiles,
            },
        },
        "decompilation": decompilation,
        "v11_implications": {
            "step2_curriculum_rule": "repair samples must be converted into abstract marker/context rules plus paraphrase transfer checks, not copied as per-fixture literal regexes",
            "required_gate_additions": [
                "naturalized_paraphrase_holdout",
                "same_semantics_different_surface_form",
                "literal_regex_dependency_scan",
                "nonsealed_replay_plus_transfer_gap_report",
            ],
            "forbidden_shortcuts": [
                "do_not_add_one_regex_per_failed_fixture_sentence",
                "do_not_accept_isolated_fixture_1_0_without_paraphrase_transfer",
                "do_not_treat_partial_decompile_as_complete_source_recovery",
                "do_not_hide_literal_fixture_patches_inside_profile_helpers",
            ],
        },
        "next_action": "fold_into_v11_step2_repair_curriculum_plan",
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    finding = payload["finding"]
    lines = [
        "# V11 Profile Literal Patch Audit v1",
        "",
        f"Generated: {payload['generated_at']}",
        f"status: `{payload['status']}`",
        "",
        "## Root Cause",
        "",
        finding["summary"],
        "",
        f"- root_cause_for_v10_transfer_gap: `{finding['root_cause_for_v10_transfer_gap']}`",
        f"- total_regex_literal_count_in_profile_inspection: `{finding['total_regex_literal_count_in_profile_inspection']}`",
        f"- total_fixture_like_regex_literal_count: `{finding['total_fixture_like_regex_literal_count']}`",
        "",
        "## Profile Evidence",
        "",
        "| function | docstring | regex literals | fixture-like regex literals | mechanism |",
        "|---|---|---:|---:|---|",
    ]
    for name, item in finding["evidence"]["profiles"].items():
        mechanisms = []
        if item["uses_regex_evidence_helper"]:
            mechanisms.append("_any_regex_evidence")
        if item["uses_direct_re_search"]:
            mechanisms.append("re.search")
        if item["uses_v9_override"]:
            mechanisms.append("_v9_override")
        lines.append(
            f"| {name} | {item['docstring']} | {item['regex_literal_count']} | {item['fixture_like_regex_literal_count']} | {', '.join(mechanisms)} |"
        )
    lines.extend([
        "",
        "## Decompilation Status",
        "",
        f"- status: `{payload['decompilation']['status']}`",
        f"- failed/attempted functions: `{payload['decompilation']['automatic_decompilation_failed_functions']}/{payload['decompilation']['automatic_decompilation_attempted_functions']}`",
        f"- known failure reason: {payload['decompilation']['known_failure_reason']}",
        "",
        "## V11 Implications",
        "",
        f"- step2_curriculum_rule: {payload['v11_implications']['step2_curriculum_rule']}",
        "- required_gate_additions:",
    ])
    for item in payload["v11_implications"]["required_gate_additions"]:
        lines.append(f"  - {item}")
    lines.append("- forbidden_shortcuts:")
    for item in payload["v11_implications"]["forbidden_shortcuts"]:
        lines.append(f"  - {item}")
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _write_markdown(payload)
    print(json.dumps({"status": payload["status"], "next_action": payload["next_action"], "fixture_like_regex_literal_count": payload["finding"]["total_fixture_like_regex_literal_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()