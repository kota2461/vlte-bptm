"""Create V11 code-audit triage for P0 source recovery blockers.

This is diagnostic/roadmap metadata only. It does not mutate router behavior,
training data, fixtures, or sealed state.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "semantic_routing" / "baseline.py"
KNOWLEDGE_INDEX_PATH = ROOT / "semantic_routing" / "knowledge_index.py"
CACHE = ROOT / "semantic_routing" / "__pycache__"
OUTPUT_JSON = ROOT / "build" / "v11_code_audit_triage_v1.json"
OUTPUT_MD = ROOT / "build" / "v11_code_audit_triage_v1.md"
PROFILE_LITERAL_AUDIT_PATH = ROOT / "build" / "v11_profile_literal_patch_audit_v1.json"
ATTACHMENT_PATH = Path(
    r"C:\Users\kota\.codex\attachments\03e2a292-d2a8-4880-8d71-5ecf0739127e\pasted-text.txt"
)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _chosen_baseline_pyc() -> Path | None:
    candidates = sorted(
        (p for p in CACHE.glob("baseline.cpython-310.pyc.*") if p.stat().st_size > 50000),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def build_payload() -> dict[str, Any]:
    baseline_text = BASELINE_PATH.read_text(encoding="utf-8")
    knowledge_text = KNOWLEDGE_INDEX_PATH.read_text(encoding="utf-8")
    chosen_pyc = _chosen_baseline_pyc()
    baseline_loader_confirmed = all(
        token in baseline_text
        for token in ("marshal.loads", "exec(_CODE, globals())", "baseline.cpython-310.pyc")
    )
    hook_substring_confirmed = "hook.casefold() in haystack" in knowledge_text
    baseline_blocks_step2 = baseline_loader_confirmed
    pyc_info = None
    if chosen_pyc is not None:
        pyc_info = {
            "path": _rel(chosen_pyc),
            "sha256": _sha256(chosen_pyc),
            "size": chosen_pyc.stat().st_size,
            "mtime": chosen_pyc.stat().st_mtime,
        }
    profile_literal_audit = (
        json.loads(PROFILE_LITERAL_AUDIT_PATH.read_text(encoding="utf-8"))
        if PROFILE_LITERAL_AUDIT_PATH.exists()
        else None
    )
    profile_literal_finding = profile_literal_audit.get("finding") if profile_literal_audit else None
    findings = {
        "baseline_pyc_loader": {
            "priority": "P0",
            "confirmed": baseline_loader_confirmed,
            "file": _rel(BASELINE_PATH),
            "chosen_pyc": pyc_info,
            "risk": "router import depends on ignored __pycache__ bytecode and unreadable v7-v9 logic",
            "blocks_step2": baseline_blocks_step2,
            "recovery_status": "required" if baseline_loader_confirmed else "completed",
            "required_action": (
                "recover readable baseline source or replace loader with auditable source before repair-lane fixture work"
                if baseline_loader_confirmed
                else "keep source-recovered baseline under regression tests; do not restore pyc loader"
            ),
        },
        "literal_profile_patch_overfit": {
            "priority": "P0",
            "confirmed": bool(profile_literal_finding and profile_literal_finding.get("confirmed")),
            "file": _rel(PROFILE_LITERAL_AUDIT_PATH) if PROFILE_LITERAL_AUDIT_PATH.exists() else None,
            "risk": "v6-v9 profile layers used fixture-specific literal regex patches; this explains bridge/profile non-transfer when sealed wording changes",
            "blocks_step2": False,
            "required_action": "fold literal-profile overfit into Step 2 curriculum; replace per-sentence regex patches with abstract rules plus paraphrase transfer gates",
            "evidence": profile_literal_finding,
        },
        "hook_keyword_overfire_without_context": {
            "priority": "P0",
            "confirmed": hook_substring_confirmed,
            "file": _rel(KNOWLEDGE_INDEX_PATH),
            "risk": "retrieval hooks use substring matching without negation, metacontext, definition-intent, or local-current checks",
            "blocks_step2": False,
            "required_action": "add hook context guard and nonsealed false-positive fixture before relying on hook-derived risk/current signals",
        },
        "constraint_omission_fast_path": {
            "priority": "P1",
            "status": "blocked_by_source_recovery" if baseline_loader_confirmed else "trace_ready_after_source_recovery",
            "blocked_by": "baseline_pyc_loader" if baseline_loader_confirmed else None,
            "risk": "constraint omissions cannot be fully classified until marker firing and constraint merge paths are traced in source",
            "required_action": "after source recovery, compare marker firing versus constraint merge/clearing for omission cases",
        },
        "fixture_coverage_gap": {
            "priority": "P2",
            "status": "classification_required_before_claiming_full_scan_coverage",
            "minimum_relevant_unscanned_cases": 132,
            "case_sets": [
                {"path": "tests/fixtures/v7_router_repair_fixture_v1.json", "case_count": 72},
                {"path": "tests/fixtures/v5_critical_operations_fixture_v1.json", "case_count": 48},
                {"path": "tests/fixtures/v6_router_debate_candidate_fixture_v1.json", "case_count": 12},
            ],
            "required_action": "schema-bridge PLM-adjacent fixtures or extend block scanner loaders",
        },
    }
    blockers = [key for key, item in findings.items() if item.get("blocks_step2")]
    roadmap_override = (
        {
            "previous_next_action": "roadmap_v11_step2_create_repair_curriculum_plan",
            "next_action": "roadmap_v11_step1b_recover_baseline_source",
            "advance_to": "v11_p0_baseline_source_recovery",
            "blocks_repair_curriculum_plan": True,
        }
        if blockers
        else {
            "previous_next_action": "roadmap_v11_step1b_recover_baseline_source",
            "next_action": "roadmap_v11_step2_create_repair_curriculum_plan",
            "advance_to": "v11_repair_curriculum_plan",
            "blocks_repair_curriculum_plan": False,
        }
    )
    return {
        "schema_version": "v11-code-audit-triage.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "p0_baseline_source_recovery_required" if blockers else "step1b_baseline_source_recovery_completed",
        "source_report": {
            "attachment_available": ATTACHMENT_PATH.exists(),
            "attachment_path": str(ATTACHMENT_PATH),
        },
        "policy": {
            "diagnostic_only": True,
            "mutates_router": False,
            "writes_training_data": False,
            "opens_active_sealed_fixture": False,
            "uses_sealed_labels_for_tuning": False,
        },
        "findings": findings,
        "step2_blockers": blockers,
        "roadmap_override": roadmap_override,
        "recommended_actions": [
            {
                "id": "v11_p0_baseline_source_recovery",
                "priority": "P0",
                "action": "recover readable semantic_routing/baseline.py source from pyc/archive/temp patches or explicitly replace the runtime with auditable source",
                "done_when": "baseline.py no longer imports behavior through marshal/exec from __pycache__ and full pytest passes",
            },
            {
                "id": "v11_p0_literal_profile_generalization_guard",
                "priority": "P0",
                "action": "ban one-regex-per-failed-fixture repairs and require paraphrase/transfer validation for profile-derived fixes",
                "done_when": "V11 curriculum records literal-profile overfit and gates new repairs with naturalized paraphrase holdouts",
            },
            {
                "id": "v11_p0_hook_context_guard",
                "priority": "P0",
                "action": "add negation/metacontext/definition/local-current guard around knowledge-index hook matching",
                "done_when": "nonsealed hook-overfire false-positive fixture passes with zero overfire",
            },
            {
                "id": "v11_p1_constraint_omission_trace",
                "priority": "P1",
                "action": "trace constraint marker firing and merge/clearing after baseline source recovery",
                "done_when": "constraint omission is classified as marker coverage gap, merge bug, or suppression bug",
            },
            {
                "id": "v11_p2_fixture_schema_bridge",
                "priority": "P2",
                "action": "extend sample block scan to PLM-adjacent v5/v6/v7 fixture schema families",
                "done_when": "block scan covers at least the additional 132 router-relevant cases",
            },
        ],
    }


def _write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# V11 Code Audit Triage v1",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Policy",
        "",
        "- Diagnostic/roadmap metadata only; no router, training-data, fixture, or sealed-state mutation.",
        "- Sealed labels remain taxonomy-only and are not used for tuning.",
        "",
        "## Step2 Status",
        "",
        f"- status: {payload['status']}",
        f"- next_action: {payload['roadmap_override']['next_action']}",
        f"- blocks_repair_curriculum_plan: {str(payload['roadmap_override']['blocks_repair_curriculum_plan']).lower()}",
        f"- step2_blockers: {payload['step2_blockers']}",
        "",
        "## Findings",
        "",
        "| finding | priority | confirmed/status | blocks Step2 | required action |",
        "|---|---|---|---:|---|",
    ]
    for key, item in payload["findings"].items():
        state = item.get("confirmed", item.get("status"))
        lines.append(
            f"| {key} | {item['priority']} | {state} | {str(item.get('blocks_step2', False)).lower()} | {item['required_action']} |"
        )
    chosen = payload["findings"]["baseline_pyc_loader"].get("chosen_pyc")
    if chosen:
        lines.extend([
            "",
            "## Chosen Baseline Pyc",
            "",
            f"- path: `{chosen['path']}`",
            f"- sha256: `{chosen['sha256']}`",
            f"- size: {chosen['size']}",
        ])
    lines.extend([
        "",
        "## Recommended Actions",
        "",
    ])
    for action in payload["recommended_actions"]:
        lines.append(f"- {action['priority']} `{action['id']}`: {action['action']}")
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _write_markdown(payload)
    print(json.dumps({"status": payload["status"], "next_action": payload["roadmap_override"]["next_action"], "step2_blockers": payload["step2_blockers"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()