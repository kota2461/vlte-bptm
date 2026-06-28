# V11 Profile Literal Patch Audit v1

Generated: 2026-01-01T00:00:00+00:00
status: `literal_profile_patch_overfit_confirmed`

## Root Cause

v6-v9 profile layers are dominated by specific literal-regex repair patches rather than general routing logic

- root_cause_for_v10_transfer_gap: `True`
- total_regex_literal_count_in_profile_inspection: `274`
- total_fixture_like_regex_literal_count: `189`

## Profile Evidence

| function | docstring | regex literals | fixture-like regex literals | mechanism |
|---|---|---:|---:|---|
| _v7_generalization_profile | Non-sealed V7 repair signals generalized from draft replay taxonomy. | 149 | 83 | _any_regex_evidence |
| _v8_recovery_profile | Non-sealed V8 recovery signals from priority-review replay gaps. | 67 | 48 | _any_regex_evidence |
| _v9_primary_review_profile | User-approved V9 primary-review 34-row non-sealed repair signals. | 34 | 34 | re.search, _v9_override |
| _v9_constraint_operation_extension_profile | User-approved V9 extension focused on constraint/operation exactness. | 24 | 24 | re.search, _v9_override |

## Decompilation Status

- status: `partial_only`
- failed/attempted functions: `3/6`
- known failure reason: dictionary/set comprehension opcodes were not handled by the external decompiler scan

## V11 Implications

- step2_curriculum_rule: repair samples must be converted into abstract marker/context rules plus paraphrase transfer checks, not copied as per-fixture literal regexes
- required_gate_additions:
  - naturalized_paraphrase_holdout
  - same_semantics_different_surface_form
  - literal_regex_dependency_scan
  - nonsealed_replay_plus_transfer_gap_report
- forbidden_shortcuts:
  - do_not_add_one_regex_per_failed_fixture_sentence
  - do_not_accept_isolated_fixture_1_0_without_paraphrase_transfer
  - do_not_treat_partial_decompile_as_complete_source_recovery
  - do_not_hide_literal_fixture_patches_inside_profile_helpers
