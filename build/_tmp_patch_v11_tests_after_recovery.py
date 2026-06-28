from pathlib import Path

# Update triage tests.
path = Path("tests/test_v11_code_audit_triage.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "def test_v11_code_audit_triage_records_p0_baseline_loader_blocker() -> None:",
    "def test_v11_code_audit_triage_records_completed_baseline_source_recovery() -> None:",
)
text = text.replace(
    '    assert report["status"] == "p0_baseline_source_recovery_required"',
    '    assert report["status"] == "step1b_baseline_source_recovery_completed"',
)
text = text.replace(
    '    assert baseline["confirmed"] is True\n    assert baseline["blocks_step2"] is True',
    '    assert baseline["confirmed"] is False\n    assert baseline["blocks_step2"] is False\n    assert baseline["recovery_status"] == "completed"',
)
text = text.replace(
    '    assert report["step2_blockers"] == ["baseline_pyc_loader"]',
    '    assert report["step2_blockers"] == []',
)
text = text.replace(
    '    assert constraint["status"] == "explained_not_located"\n    assert constraint["blocked_by"] == "baseline_pyc_loader"',
    '    assert constraint["status"] == "trace_ready_after_source_recovery"\n    assert constraint["blocked_by"] is None',
)
text = text.replace(
    '    assert "p0_baseline_source_recovery_required" in completed.stdout\n    assert "roadmap_v11_step1b_recover_baseline_source" in completed.stdout',
    '    assert "step1b_baseline_source_recovery_completed" in completed.stdout\n    assert "roadmap_v11_step2_create_repair_curriculum_plan" in completed.stdout',
)
text = text.replace(
    '''    assert report["roadmap_override"] == {
        "previous_next_action": "roadmap_v11_step2_create_repair_curriculum_plan",
        "next_action": "roadmap_v11_step1b_recover_baseline_source",
        "advance_to": "v11_p0_baseline_source_recovery",
        "blocks_repair_curriculum_plan": True,
    }''',
    '''    assert report["roadmap_override"] == {
        "previous_next_action": "roadmap_v11_step1b_recover_baseline_source",
        "next_action": "roadmap_v11_step2_create_repair_curriculum_plan",
        "advance_to": "v11_repair_curriculum_plan",
        "blocks_repair_curriculum_plan": False,
    }''',
)
path.write_text(text, encoding="utf-8")

# Update targets/roadmap tests.
path = Path("tests/test_v11_targets_and_roadmap.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    '    assert payload["status"] == "step1_post_v10_value_diff_transfer_taxonomy_completed_p0_source_recovery_next"',
    '    assert payload["status"] == "step1_post_v10_value_diff_transfer_taxonomy_completed_step2_curriculum_next"',
)
text = text.replace(
    '        "baseline_source_recovery_required": True,',
    '        "baseline_source_recovery_required": False,',
)
old = '''def test_v11_roadmap_is_rerouted_to_p0_source_recovery_before_curriculum() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["pre_step2_blockers"] == ["baseline_pyc_loader"]
    assert payload["code_audit_triage"]["status"] == "p0_baseline_source_recovery_required"
    assert [step["status"] for step in payload["roadmap"]] == [
        "completed",
        "next",
        "blocked",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
    ]
    assert [step["name"] for step in payload["roadmap"]] == [
        "post_v10_value_diff_transfer_taxonomy",
        "v11_p0_baseline_source_recovery",
        "v11_repair_curriculum_plan",
        "v11_value_diff_repair_fixture_and_candidate_replay",
        "v11_bridge_transfer_validation_set",
        "v11_router_generalization_changes",
        "v11_nonsealed_replay_gate",
        "sealed_v11_rotation_review",
        "sealed_v11_rotation",
        "sealed_v11_one_time_measurement",
    ]
    assert payload["next_action"] == "roadmap_v11_step1b_recover_baseline_source"
    assert payload["roadmap_decision"] == {
        "can_advance": True,
        "advance_to": "v11_p0_baseline_source_recovery",
        "blocked_reasons": [],
    }
'''
new = '''def test_v11_roadmap_advances_to_curriculum_after_source_recovery() -> None:
    payload = _load(TARGETS_PATH)

    assert payload["pre_step2_blockers"] == []
    assert payload["code_audit_triage"]["status"] == "step1b_baseline_source_recovery_completed"
    assert [step["status"] for step in payload["roadmap"]] == [
        "completed",
        "next",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
        "pending",
    ]
    assert [step["name"] for step in payload["roadmap"]] == [
        "post_v10_value_diff_transfer_taxonomy",
        "v11_repair_curriculum_plan",
        "v11_value_diff_repair_fixture_and_candidate_replay",
        "v11_bridge_transfer_validation_set",
        "v11_router_generalization_changes",
        "v11_nonsealed_replay_gate",
        "sealed_v11_rotation_review",
        "sealed_v11_rotation",
        "sealed_v11_one_time_measurement",
    ]
    assert payload["next_action"] == "roadmap_v11_step2_create_repair_curriculum_plan"
    assert payload["roadmap_decision"] == {
        "can_advance": True,
        "advance_to": "v11_repair_curriculum_plan",
        "blocked_reasons": [],
    }
'''
if old not in text:
    raise SystemExit("old roadmap test block not found")
text = text.replace(old, new)
text = text.replace(
    '    assert "step1_post_v10_value_diff_transfer_taxonomy_completed_p0_source_recovery_next" in completed.stdout',
    '    assert "step1_post_v10_value_diff_transfer_taxonomy_completed_step2_curriculum_next" in completed.stdout',
)
text = text.replace(
    '    assert "## P0 Code Audit Override" in roadmap\n    assert "roadmap_v11_step1b_recover_baseline_source" in roadmap\n    assert "v11_repair_curriculum_plan" in roadmap\n    assert "blocked" in roadmap',
    '    assert "## P0 Code Audit Status" in roadmap\n    assert "roadmap_v11_step2_create_repair_curriculum_plan" in roadmap\n    assert "v11_repair_curriculum_plan" in roadmap\n    assert "baseline source recovery completed" in roadmap',
)
text = text.replace(
    '    assert "advance_to=v11_p0_baseline_source_recovery" in main_roadmap',
    '    assert "advance_to=v11_repair_curriculum_plan" in main_roadmap',
)
path.write_text(text, encoding="utf-8")
print("patched")