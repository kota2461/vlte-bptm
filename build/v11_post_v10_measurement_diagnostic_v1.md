# V11 Post-V10 Measurement Diagnostic v1

This diagnostic inspects consumed sealed v10 only as post-measurement taxonomy. It is not training data and is not a replay gate.

## Metric Regression

| Metric | V9 | V10 | Delta |
|---|---:|---:|---:|
| intent_accuracy | 0.892857 | 0.785714 | -0.107143 |
| critical_signal_recall | 0.857143 | 0.400000 | -0.457143 |
| operation_exact_match | 0.821429 | 0.642857 | -0.178572 |
| constraint_exact_match | 0.642857 | 0.535714 | -0.107143 |
| risk_exact_match | 0.750000 | 0.678571 | -0.071429 |

## Failure Modes

- mode_counts: `{'intent_correct_field_mismatch': 17, 'intent_mismatch': 6}`
- critical_signal_misses: `{'contains_unverified_claims': 1, 'missing_required_information': 3, 'multiple_intents': 5}`
- intent_transitions: `{'clarify->explore': 1, 'clarify->respond': 1, 'clarify->verify': 1, 'explain->verify': 1, 'explore->respond': 1, 'respond->build': 1}`

## Bridge Transfer Gap

- bridge_template_overfit_risk: `True`
- language_shift: `{'bridge': {'en': 72}, 'sealed_v10': {'en': 14, 'ja': 14}}`
- style_marker_delta_sealed_minus_bridge: `{'synthetic_bridge_prefix_rate': -1.0, 'terminal_operation_phrase_rate': -0.888889, 'main_issue_phrase_rate': -0.861111, 'boundary_word_rate': -0.25, 'ask_before_phrase_rate': -0.505953, 'japanese_script_rate': 0.5, 'average_char_length': -215.811}`

## V11 Focus Areas

1. value_level_diff_instrumentation: field-level errors hide whether failures are value vocabulary drift or routing logic defects
1. clarify_boundary_collapse: clarify recall collapsed and clarify cases dispersed across respond, verify, and explore
1. multiple_intent_under_detection: multiple_intents is the largest critical-signal miss after v10
1. bridge_non_transfer: isolated bridge replay was exact, but sealed v10 regressed on all five metrics
2. intent_correct_field_mismatch_lane: cases with correct primary intent still miss constraints/risk/operations and need a separate exactness lane

## Decision

- next_action: `roadmap_v11_step1_build_taxonomy_from_value_diff_and_transfer_gap`
