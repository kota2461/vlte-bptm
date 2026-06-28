from pathlib import Path

ROOT = Path('.')

triage = ROOT / 'build' / 'create_v11_code_audit_triage.py'
text = triage.read_text(encoding='utf-8')
text = text.replace(
    'OUTPUT_MD = ROOT / "build" / "v11_code_audit_triage_v1.md"\nATTACHMENT_PATH = Path(',
    'OUTPUT_MD = ROOT / "build" / "v11_code_audit_triage_v1.md"\nPROFILE_LITERAL_AUDIT_PATH = ROOT / "build" / "v11_profile_literal_patch_audit_v1.json"\nATTACHMENT_PATH = Path(',
)
text = text.replace(
    '    findings = {\n        "baseline_pyc_loader": {',
    '    profile_literal_audit = (\n        json.loads(PROFILE_LITERAL_AUDIT_PATH.read_text(encoding="utf-8"))\n        if PROFILE_LITERAL_AUDIT_PATH.exists()\n        else None\n    )\n    profile_literal_finding = profile_literal_audit.get("finding") if profile_literal_audit else None\n    findings = {\n        "baseline_pyc_loader": {',
)
text = text.replace(
    '        },\n        "hook_keyword_overfire_without_context": {',
    '        },\n        "literal_profile_patch_overfit": {\n            "priority": "P0",\n            "confirmed": bool(profile_literal_finding and profile_literal_finding.get("confirmed")),\n            "file": _rel(PROFILE_LITERAL_AUDIT_PATH) if PROFILE_LITERAL_AUDIT_PATH.exists() else None,\n            "risk": "v6-v9 profile layers used fixture-specific literal regex patches; this explains bridge/profile non-transfer when sealed wording changes",\n            "blocks_step2": False,\n            "required_action": "fold literal-profile overfit into Step 2 curriculum; replace per-sentence regex patches with abstract rules plus paraphrase transfer gates",\n            "evidence": profile_literal_finding,\n        },\n        "hook_keyword_overfire_without_context": {',
)
text = text.replace(
    '            {\n                "id": "v11_p0_hook_context_guard",',
    '            {\n                "id": "v11_p0_literal_profile_generalization_guard",\n                "priority": "P0",\n                "action": "ban one-regex-per-failed-fixture repairs and require paraphrase/transfer validation for profile-derived fixes",\n                "done_when": "V11 curriculum records literal-profile overfit and gates new repairs with naturalized paraphrase holdouts",\n            },\n            {\n                "id": "v11_p0_hook_context_guard",',
)
triage.write_text(text, encoding='utf-8', newline='\n')

targets = ROOT / 'build' / 'create_v11_targets_and_roadmap.py'
text = targets.read_text(encoding='utf-8')
text = text.replace(
    'CODE_AUDIT_TRIAGE_PATH = ROOT / "build" / "v11_code_audit_triage_v1.json"\nREADINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"',
    'CODE_AUDIT_TRIAGE_PATH = ROOT / "build" / "v11_code_audit_triage_v1.json"\nPROFILE_LITERAL_AUDIT_PATH = ROOT / "build" / "v11_profile_literal_patch_audit_v1.json"\nREADINESS_PATH = ROOT / "build" / "plm_measurement_readiness_review.json"',
)
text = text.replace(
    'def _taxonomy(diagnostic: dict[str, Any]) -> dict[str, Any]:\n    summary = diagnostic["failure_mode_summary"]',
    'def _taxonomy(diagnostic: dict[str, Any], profile_literal_audit: dict[str, Any] | None = None) -> dict[str, Any]:\n    summary = diagnostic["failure_mode_summary"]',
)
text = text.replace(
    '    focus_by_id = {item["id"]: item for item in diagnostic["focus_areas"]}\n    return {',
    '    focus_by_id = {item["id"]: item for item in diagnostic["focus_areas"]}\n    literal_finding = profile_literal_audit.get("finding", {}) if profile_literal_audit else {}\n    return {',
)
text = text.replace(
    '            "definition_request_build_overroute": {\n                "priority": 2,\n                "transition_count": summary["intent_transitions"].get("respond->build", 0),\n                "pattern": "one-sentence definition or meaning requests can be over-routed to build",\n                "interpretation": "respond/build boundary needs a narrow definition-request guard before broader build routing",\n                "first_action": "add definition-request contrast to intent boundary plan",\n                "repair_lane": "intent_boundary_repair_lane",\n            },\n        },',
    '            "definition_request_build_overroute": {\n                "priority": 2,\n                "transition_count": summary["intent_transitions"].get("respond->build", 0),\n                "pattern": "one-sentence definition or meaning requests can be over-routed to build",\n                "interpretation": "respond/build boundary needs a narrow definition-request guard before broader build routing",\n                "first_action": "add definition-request contrast to intent boundary plan",\n                "repair_lane": "intent_boundary_repair_lane",\n            },\n            "literal_profile_patch_overfit": {\n                "priority": 1,\n                "confirmed": bool(literal_finding.get("confirmed")),\n                "regex_literal_count": literal_finding.get("total_regex_literal_count_in_profile_inspection"),\n                "fixture_like_regex_literal_count": literal_finding.get("total_fixture_like_regex_literal_count"),\n                "interpretation": "v6-v9 repair profiles were largely per-fixture literal regex patches, so isolated nonsealed exactness did not transfer to sealed v10 wording",\n                "first_action": "convert repair examples into abstract marker/context rules and require naturalized paraphrase transfer checks",\n                "repair_lane": "bridge_transfer_validation_lane",\n            },\n        },',
)
text = text.replace(
    'def _repair_lanes(diagnostic: dict[str, Any]) -> dict[str, Any]:\n    summary = diagnostic["failure_mode_summary"]',
    'def _repair_lanes(diagnostic: dict[str, Any], profile_literal_audit: dict[str, Any] | None = None) -> dict[str, Any]:\n    summary = diagnostic["failure_mode_summary"]',
)
text = text.replace(
    '    gap = diagnostic["bridge_transfer_diagnostic"]["distribution_gap"]\n    return {',
    '    gap = diagnostic["bridge_transfer_diagnostic"]["distribution_gap"]\n    literal_finding = profile_literal_audit.get("finding", {}) if profile_literal_audit else {}\n    return {',
)
text = text.replace(
    '                "source_evidence": gap,\n                "required_sample_shape": ["template_vs_naturalized_pair", "ja_en_distribution_pair", "heldout_style_probe"],',
    '                "source_evidence": {\n                    "bridge_distribution_gap": gap,\n                    "literal_profile_patch_overfit": literal_finding,\n                },\n                "required_sample_shape": ["template_vs_naturalized_pair", "ja_en_distribution_pair", "heldout_style_probe", "same_semantics_different_surface_form"],',
)
text = text.replace(
    '            "do_not_expand_fixtures_before_constraint_omission_and_hook_overfire_audit",\n        ],',
    '            "do_not_expand_fixtures_before_constraint_omission_and_hook_overfire_audit",\n            "do_not_add_one_regex_per_failed_fixture_sentence",\n            "do_not_accept_isolated_fixture_1_0_without_paraphrase_transfer",\n        ],',
)
text = text.replace(
    '    code_audit_triage = _load_json(CODE_AUDIT_TRIAGE_PATH) if CODE_AUDIT_TRIAGE_PATH.exists() else None\n    readiness = _load_json(READINESS_PATH)',
    '    code_audit_triage = _load_json(CODE_AUDIT_TRIAGE_PATH) if CODE_AUDIT_TRIAGE_PATH.exists() else None\n    profile_literal_audit = _load_json(PROFILE_LITERAL_AUDIT_PATH) if PROFILE_LITERAL_AUDIT_PATH.exists() else None\n    readiness = _load_json(READINESS_PATH)',
)
text = text.replace(
    '            "code_audit_triage": _rel(CODE_AUDIT_TRIAGE_PATH) if CODE_AUDIT_TRIAGE_PATH.exists() else None,\n            "readiness_review": _rel(READINESS_PATH),',
    '            "code_audit_triage": _rel(CODE_AUDIT_TRIAGE_PATH) if CODE_AUDIT_TRIAGE_PATH.exists() else None,\n            "profile_literal_patch_audit": _rel(PROFILE_LITERAL_AUDIT_PATH) if PROFILE_LITERAL_AUDIT_PATH.exists() else None,\n            "readiness_review": _rel(READINESS_PATH),',
)
text = text.replace(
    '        "taxonomy": _taxonomy(diagnostic),\n        "repair_lanes": _repair_lanes(diagnostic),',
    '        "taxonomy": _taxonomy(diagnostic, profile_literal_audit),\n        "repair_lanes": _repair_lanes(diagnostic, profile_literal_audit),\n        "profile_literal_patch_audit": profile_literal_audit,',
)
text = text.replace(
    '            "hook_overfire_audit_required": True,\n            "baseline_source_recovery_required": bool(code_audit_triage and code_audit_triage.get("step2_blockers")),',
    '            "hook_overfire_audit_required": True,\n            "literal_profile_dependency_scan_required": True,\n            "baseline_source_recovery_required": bool(code_audit_triage and code_audit_triage.get("step2_blockers")),',
)
targets.write_text(text, encoding='utf-8', newline='\n')

# Fix typo in audit script forbidden shortcut.
audit_script = ROOT / 'build' / 'create_v11_profile_literal_patch_audit.py'
text = audit_script.read_text(encoding='utf-8')
text = text.replace('"do_not_hide literal fixture patches inside profile helpers"', '"do_not_hide_literal_fixture_patches_inside_profile_helpers"')
audit_script.write_text(text, encoding='utf-8', newline='\n')