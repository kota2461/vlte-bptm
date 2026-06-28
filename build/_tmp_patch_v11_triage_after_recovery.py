from pathlib import Path

path = Path("build/create_v11_code_audit_triage.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    '''    hook_substring_confirmed = "hook.casefold() in haystack" in knowledge_text
    pyc_info = None
''',
    '''    hook_substring_confirmed = "hook.casefold() in haystack" in knowledge_text
    baseline_blocks_step2 = baseline_loader_confirmed
    pyc_info = None
''',
)
text = text.replace(
    '''            "risk": "router import depends on ignored __pycache__ bytecode and unreadable v7-v9 logic",
            "blocks_step2": True,
            "required_action": "recover readable baseline source or replace loader with auditable source before repair-lane fixture work",
''',
    '''            "risk": "router import depends on ignored __pycache__ bytecode and unreadable v7-v9 logic",
            "blocks_step2": baseline_blocks_step2,
            "recovery_status": "required" if baseline_loader_confirmed else "completed",
            "required_action": (
                "recover readable baseline source or replace loader with auditable source before repair-lane fixture work"
                if baseline_loader_confirmed
                else "keep source-recovered baseline under regression tests; do not restore pyc loader"
            ),
''',
)
text = text.replace(
    '''            "status": "explained_not_located",
            "blocked_by": "baseline_pyc_loader",
            "risk": "constraint omissions cannot be traced to source until v7-v9 profile logic is readable",
            "required_action": "after source recovery, compare marker firing versus constraint merge/clearing for omission cases",
''',
    '''            "status": "blocked_by_source_recovery" if baseline_loader_confirmed else "trace_ready_after_source_recovery",
            "blocked_by": "baseline_pyc_loader" if baseline_loader_confirmed else None,
            "risk": "constraint omissions cannot be fully classified until marker firing and constraint merge paths are traced in source",
            "required_action": "after source recovery, compare marker firing versus constraint merge/clearing for omission cases",
''',
)
text = text.replace(
    '''    blockers = [key for key, item in findings.items() if item.get("blocks_step2")]
    return {
''',
    '''    blockers = [key for key, item in findings.items() if item.get("blocks_step2")]
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
''',
)
text = text.replace(
    '''        "status": "p0_baseline_source_recovery_required" if blockers else "no_step2_blockers_detected",
''',
    '''        "status": "p0_baseline_source_recovery_required" if blockers else "step1b_baseline_source_recovery_completed",
''',
)
text = text.replace(
    '''        "roadmap_override": {
            "previous_next_action": "roadmap_v11_step2_create_repair_curriculum_plan",
            "next_action": "roadmap_v11_step1b_recover_baseline_source",
            "advance_to": "v11_p0_baseline_source_recovery",
            "blocks_repair_curriculum_plan": bool(blockers),
        },
''',
    '''        "roadmap_override": roadmap_override,
''',
)
path.write_text(text, encoding="utf-8")
print("patched")