# PLM V6 Roadmap: Boundary Calibration And Sealed Rotation

Updated: 2026-06-24

## Contract

- Sealed v5 is consumed and may be used only as measurement taxonomy.
- Sealed v5 input text and labels must not be copied into training, review, or non-sealed fixtures.
- V6 tuning uses visible/human-reviewed non-sealed lanes plus diagnostic draft lanes only as diagnostics.
- Draft/candidate lanes are not gate evidence.
- Same-cycle promotion remains disallowed.
- A fresh sealed v6 fixture must be generated and rotated before the next adjudicating measurement.

## Baseline

| Metric | V5 sealed |
|---|---:|
| intent_accuracy | 0.750000 |
| critical_signal_recall | 0.375000 |
| operation_exact_match | 0.678571 |
| constraint_exact_match | 0.821429 |
| risk_exact_match | 0.892857 |
| sealed_error_count | 18 |

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | backup_checkpoint | `archive\2026-06-24_v6-nonsealed-exact-pre-roadmap-gate` | completed |
| 2 | current_state_report | `build\v6_current_state_report_v1.json` | completed |
| 3 | nonsealed_replay_gate | `build\v6_nonsealed_replay_gate_report_v1.json` | completed |
| 4 | sealed_v6_rotation_review | `build\v6_sealed_rotation_review_v1.json` | completed |
| 5 | sealed_v6_rotation | `tests\fixtures\pattern_language_sealed_v6.json` | completed |
| 6 | sealed_v6_one_time_measurement | `build\pattern_language_sealed_v6_measurement_report.json` | completed |
| 7 | post_v6_measurement_taxonomy | `build\v7_targets_and_roadmap_v1.json` | completed |

## Step 4 Output

`build\v6_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v6_rotation`. It confirms that the V6 non-sealed replay gate passed, no active sealed fixture is present, and `pattern_language_sealed_v5.json` is consumed. It does not create, open, or measure `pattern_language_sealed_v6.json`.

## Step 5 Fixture Constraints

- 28 sealed cases, four per intent.
- No exact text overlap with prior benchmark/sealed fixtures.
- No exact text overlap with V6 required non-sealed gate lanes.
- No exact text overlap with V6 diagnostic non-sealed lanes.
- Measure once, then mark consumed before any tuning based on the result.

## Step 5 Output

`build\v6_sealed_rotation_report_v1.json` created `tests\fixtures\pattern_language_sealed_v6.json` as the active unopened sealed fixture. It has 28 cases, predecessor `pattern_language_sealed_v5.json`, measured `False`, reviewed `False`, and sha256 `2e3059cf9360b641fc25e7e29bd6eb79cf6e33a8c5a0b176eefd402c7adbc80c`. Step 6 is the one-time sealed v6 measurement.

## Step 6 Output

`build\pattern_language_sealed_v6_measurement_report.json` measured the active sealed v6 fixture once and consumed it. Result: intent_accuracy 0.750000, critical_signal_recall 0.357143, operation_exact_match 0.607143, constraint_exact_match 0.607143, risk_exact_match 0.750000, errors 23. Sealed labels remain measurement-only. Step 7 is post-v6 measurement taxonomy and fresh successor planning before any tuning.

## Step 7 Output

`build\v7_targets_and_roadmap_v1.json` and `docs\PLM_V7_ROADMAP.md` convert the consumed sealed v6 result into aggregate taxonomy, V7 targets, non-sealed curriculum requirements, and the fresh sealed v7 rotation plan. Sealed v6 text and labels remain excluded from training.
