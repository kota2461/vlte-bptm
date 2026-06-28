# PLM V8 Roadmap: Recovery Gate And Fresh Rotation

Updated: 2026-06-25

## Contract

- Sealed v7 is consumed and may be used only as aggregate taxonomy.
- Sealed v7 text and labels must not be copied into training, review, or non-sealed fixtures.
- V8 uses human-approved non-sealed recovery samples and a separate non-sealed replay gate.
- Same-cycle promotion remains disallowed.
- A fresh sealed v8 fixture is required before the next adjudicating measurement.

## Baseline And Targets

| Metric | V7 sealed | V8 minimum | V8 stretch |
|---|---:|---:|---:|
| intent_accuracy | 0.785714 | 0.892857 | 0.928571 |
| critical_signal_recall | 0.642857 | 0.857143 | 0.928571 |
| operation_exact_match | 0.714286 | 0.857143 | 0.928571 |
| constraint_exact_match | 0.750000 | 0.857143 | 0.928571 |
| risk_exact_match | 0.785714 | 0.892857 | 0.928571 |
| sealed_error_count | 16 | <= 8 | <= 5 |

## Error Taxonomy

| Field | Count |
|---|---:|
| constraints | 7 |
| information_state | 6 |
| operations | 8 |
| primary_intent | 6 |
| risk | 6 |

## Focus Areas

1. clarify_missing_info_recovery: missing inputs and ask-first requests still drift into build or verify too early
1. operation_terminal_sequence: terminal actions and multi-step requests need stable operation order
1. constraint_false_positive_balance: format and tone constraints must be preserved without over-firing risk or verify
2. risk_ladder_boundary: AI, legal, and medical terms need low/medium/high separation by actual user intent
2. current_search_split: current-looking local context must not become unnecessary web/current routing
2. paraphrase_and_mixed_language_robustness: the same boundary should hold under paraphrase and mixed Japanese/English phrasing
2. unverified_claim_guard: vendor, legal, and report claims should trigger verification only when a claim is actually asserted

## Roadmap

| Step | Name | Output | Status |
|---:|---|---|---|
| 1 | post_v7_measurement_taxonomy | `build\v8_targets_and_roadmap_v1.json` | completed |
| 2 | v8_recovery_debate_stock | `debate_lab\topics_v8_recovery_100.json` | completed |
| 3 | v8_recovery_candidate_priority_selection | `build\v8_recovery_debate_candidate_priority_selection_v1.json` | completed |
| 4 | v8_priority_review_adoption_and_replay | `build\v8_recovery_priority_review_provisional_test_report_v1.json` | completed |
| 5 | v8_nonsealed_replay_gate | `build\v8_nonsealed_replay_gate_report_v1.json` | completed |
| 6 | sealed_v8_rotation_review | `build\v8_sealed_rotation_review_v1.json` | completed |
| 7 | sealed_v8_rotation | `tests\fixtures\pattern_language_sealed_v8.json` | completed |
| 8 | sealed_v8_one_time_measurement | `build\pattern_language_sealed_v8_measurement_report.json` | completed |

## Step 5 Output

`build\v8_nonsealed_replay_gate_report_v1.json` passed after human approval of the V8 priority review set. It confirms the prior V7 non-sealed gate, replays the 30-case V8 approved benchmark exactly, and keeps the earlier provisional replay marked as non-gate evidence. Step 6 is sealed V8 rotation review.

## Step 6 Output

`build\v8_sealed_rotation_review_v1.json` reports `eligible_for_fresh_sealed_v8_rotation`. It confirms that the V8 non-sealed replay gate passed, `pattern_language_sealed_v7.json` is consumed, no active sealed fixture exists, and `pattern_language_sealed_v8.json` has not been created. This review does not create, open, or measure sealed v8. Step 7 is now sealed V8 rotation.

## Step 7 Output

`build\v8_sealed_rotation_report_v1.json` created `tests\fixtures\pattern_language_sealed_v8.json` as the active unopened sealed fixture. Step 8 is the one-time sealed v8 measurement.

## Step 8 Output

`build\pattern_language_sealed_v8_measurement_report.json` measured the active sealed v8 fixture once and consumed it. Results: intent_accuracy `0.928571`, critical_signal_recall `0.833333`, operation_exact_match `0.785714`, constraint_exact_match `0.785714`, risk_exact_match `0.785714`, errors `14`. Sealed labels remain measurement-only and V9 taxonomy/rotation is required before tuning.

## Step 9 Output

`build\v9_targets_and_roadmap_v1.json` and `docs\PLM_V9_ROADMAP.md` convert the consumed sealed v8 result into aggregate V9 taxonomy, record the human-approved V9 non-sealed recovery lanes, and set the next action to the V9 non-sealed replay gate or sealed V9 rotation review depending on gate status. Sealed v8 text and labels remain excluded from training.
