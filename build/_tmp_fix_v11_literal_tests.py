import re
from pathlib import Path

path = Path('tests/test_v11_targets_and_roadmap.py')
text = path.read_text(encoding='utf-8')
text = re.sub(
    r'    assert modes\["intent_mismatch"\]\["transitions"\] == \{\n.*?\n    \}',
    '''    assert modes["intent_mismatch"]["transitions"] == {
        "clarify->explore": 1,
        "clarify->respond": 1,
        "clarify->verify": 1,
        "explain->verify": 1,
        "respond->build": 2,
    }''',
    text,
    count=1,
    flags=re.S,
)
text = re.sub(
    r'    assert repair\["forbidden_shortcuts"\] == \[\n.*?\n    \]',
    '''    assert repair["forbidden_shortcuts"] == [
        "do_not_tune_from_sealed_v10_text_or_labels",
        "do_not_repeat_bridge_only_isolated_1_0_as_mainline_gate",
        "do_not_merge_intent_boundary_and_field_exactness_repairs",
        "do_not_use_generated_answer_only_samples_as_direct_semantic_labels",
        "do_not_expand_fixtures_before_constraint_omission_and_hook_overfire_audit",
        "do_not_add_one_regex_per_failed_fixture_sentence",
        "do_not_accept_isolated_fixture_1_0_without_paraphrase_transfer",
    ]''',
    text,
    count=1,
    flags=re.S,
)
text = re.sub(
    r'        "hook_overfire_audit_required": True,\n        "baseline_source_recovery_required": False,',
    '        "hook_overfire_audit_required": True,\n        "literal_profile_dependency_scan_required": True,\n        "baseline_source_recovery_required": False,',
    text,
    count=1,
)
path.write_text(text, encoding='utf-8', newline='\n')