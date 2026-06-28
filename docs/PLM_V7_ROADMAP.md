# PLM V7 Roadmap: Constraint And Critical Signal Recovery

Updated: 2026-06-24

## Contract

- Sealed v6 is consumed and may be used only as measurement taxonomy.
- Sealed v6 text and labels must not be copied into training, review, or non-sealed fixtures.
- V7 work must use non-sealed curriculum and human-reviewed replay surfaces.
- Same-cycle promotion remains disallowed.
- A fresh sealed v7 fixture is required before the next adjudicating measurement.

## Baseline And Targets

| Metric | V6 sealed | V7 minimum | V7 stretch |
|---|---:|---:|---:|
| intent_accuracy | 0.750000 | 0.892857 | 0.928571 |
| critical_signal_recall | 0.357143 | 0.750000 | 0.875000 |
| operation_exact_match | 0.607143 | 0.821429 | 0.892857 |
| constraint_exact_match | 0.607143 | 0.821429 | 0.892857 |
| risk_exact_match | 0.750000 | 0.892857 | 0.928571 |
| sealed_error_count | 23 | <= 10 | <= 6 |

## Error Taxonomy

| Field | Count |
|---|---:|
| constraints | 11 |
| information_state | 8 |
| operations | 11 |
| primary_intent | 7 |
| risk | 7 |

## Focus Areas

1. constraint_preservation: response length, format, neutrality, cite-sources, no-table, and guard constraints are not retained consistently
1. operation_sequence_repair: multi-step routes such as clarify+build, verify+search, explore+compare, and build+verify collapse to a single action
1. critical_signal_recovery: unverified claims and multiple intent signals are under-detected
2. clarify_boundary_repair: missing information and ask-first cases are redirected to respond, build, or verify too quickly
2. risk_ladder_calibration: low-risk contrast, medium current/license, and high medical/legal cases need steadier severity separation
2. intent_boundary_stability: respond/build, explain/build, clarify/respond, clarify/build, build/verify, and explore/respond boundaries remain fragile

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | post_v6_measurement_taxonomy | `build\v7_targets_and_roadmap_v1.json` | completed |
| 2 | v7_nonsealed_curriculum_design | `build\v7_nonsealed_curriculum_plan_v1.json` | completed |
| 3 | v7_nonsealed_fixture_and_candidate_replay | `tests\fixtures\v7_router_repair_fixture_v1.json` | completed |
| 4 | v7_router_generalization_changes | `build\v7_router_generalization_report_v1.json` | completed |
| 5 | v7_nonsealed_replay_gate | `build\v7_nonsealed_replay_gate_report_v1.json` | completed |
| 6 | sealed_v7_rotation_review | `build\v7_sealed_rotation_review_v1.json` | completed |
| 7 | sealed_v7_rotation | `tests\fixtures\pattern_language_sealed_v7.json` | completed |
| 8 | sealed_v7_one_time_measurement | `build\pattern_language_sealed_v7_measurement_report.json` | completed |

## Step 5 Output

`build\v7_nonsealed_replay_gate_report_v1.json` passed as a non-sealed replay gate. Required human-reviewed/protection lanes passed 6/6 with 0 errors. Diagnostic lanes, including the draft V7 router repair fixture, passed 4/4 with 0 errors. The V7 draft fixture remains non-gate evidence until human review; sealed v6 text and labels remain excluded. Step 6 is now sealed V7 rotation review.

## Step 6 Output

`build\v7_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v7_rotation`. It confirms that the V7 non-sealed replay gate passed, `pattern_language_sealed_v6.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v7.json` has not been created. This review does not create, open, or measure sealed v7. Step 7 is now sealed V7 rotation.

## Step 7 Output

`build\v7_sealed_rotation_report_v1.json` created `tests\fixtures\pattern_language_sealed_v7.json` as the active unopened sealed fixture. Step 8 is the one-time sealed v7 measurement.

## Step 8 Output

`build\pattern_language_sealed_v7_measurement_report.json` measured the active sealed v7 fixture once and consumed it. V7 minimum was not met; V8 taxonomy/rotation is required before tuning.

## Step 9 Output

`build\v8_targets_and_roadmap_v1.json` and `docs\PLM_V8_ROADMAP.md` convert the consumed sealed v7 result into aggregate V8 taxonomy, record the human-approved V8 non-sealed replay gate, and set Step 6 as sealed V8 rotation review. Sealed v7 text and labels remain excluded from training.
