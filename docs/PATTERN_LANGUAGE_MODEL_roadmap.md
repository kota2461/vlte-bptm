# Pattern Language Model Roadmap

更新日: 2026-06-13

## Mission

生プロンプトから、思考制御に必要な最小限の意味信号だけを
`semantic-packet.v1`へ変換する。知識回答、処理予算、Core mode選択は行わない。

## PLM v0.0: Contract and Benchmark

Status: 完了

- `semantic-packet.v1` schemaを実装
- intent、情報不足、否定、制約、検証、時点依存、複合意図を定義
- 日英84件の独立fixtureを作成済み
- 7 intentを最低12件ずつ含める
- 隣接intentの対照pairを含める
- evidence offsetと`unknowns`を含む84件を人間レビュー済み
- sealed v1はreview開封によりconsumed、sealed v2へrotation済み
- train / validation / sealedを作成者・出典単位で分離

完了条件:

- schemaの未知field・型・範囲違反を拒否する
- fixture本文が現行sealed v2と重複しない
- critical signalの正解基準がレビュー可能である

## PLM v0.1: Baseline Adapters

Status: 一部実装済み

- 決定的な軽量signal extractorを実装済み
- 現行254件モデルを使うLegacy Adapter
- 小型LLM Semantic Adapterの比較実装
- 3方式を同一fixtureで比較する評価contractを実装済み
- adapter latency、token、costを記録

この段階では学習データを増やさない。まず、どのfieldが不足するかを確認する。

現状の可視56件ではbaseline v0.1が全指標1.0。ただし仕様由来fixtureへの
contract-fitであり、外部品質の証明ではない。後継sealed v2 28件は未測定。

完了条件:

- 各adapterが同じSemantic Packet schemaを返す
- 誤りをintent、constraint、missing information、risk、evidenceに分解できる
- LLM Adapterの出力を正解ラベルとして自動保存しない

## PLM v0.2: Targeted Learning

Status: candidate 0.2を期限付き蓄積中

- 2026-06-13にdeterministic adapter 0.2を候補固定
- 2026-06-20またはopen case 50件到達まで蓄積
- 初回batchは既存改善用18件と独立した24件
- active sealed v2は未測定・未reviewを維持
- 詳細: `CONVERSATION_ACCUMULATION_V1.md`

- v0.1の誤り上位だけを人間作例で補強
- 同義文追加より、否定・暗黙意図・複合依頼の対照例を優先
- multi-label signal抽出をRoute分類と分離
- grouped splitと近似重複検査を実装
- confidenceと`unknowns`の較正を行う

完了条件:

- critical signal recall 1.0を固定fixtureで満たす
- intent macro-F1とconstraint exact matchを報告する
- 未知表現で無理な確定をせず、再解析対象を識別できる

## PLM v0.3: Vocabulary Expansion

Status: conditional

Wikipedia等の外部文章は、v0.2のerror analysisで語彙・表記揺れが主要因と
確認された場合だけ使用する。

許可用途:

- 分野語彙と表記揺れ
- 長文中の対象箇所抽出
- 日本語・英語の文構造耐性

禁止:

- Wikipedia本文からRouteやriskラベルを自動生成
- 外部文章を人間レビューなしでapprovedへ投入
- 知識再現をPattern Language Modelの目的にする

完了条件:

- 外部データ追加前後を同じsealed fixtureで比較する
- 改善対象fieldと副作用を個別に報告する
- 効果がなければ外部データを採用しない

## Long-Term

- domain別adapter
- LLM Adapterとのselective cascade
- evidence spanの圧縮
- Failure Memory向けdanger signal

独立した思考モデルの研究は、本ロードマップの学習データと評価を流用せず、
別プロジェクトとして扱う。

## PLM V4: Failure Memory + Puzzle Learning

Status: active; V3 sealed measured/consumed, V4 failure-memory fixture and non-sealed replay created.

Primary roadmap: `docs/PLM_V4_ROADMAP.md`
Adoption registry: `build/v4_failure_memory_adoption_v1.json`
Review worksheet: `build/v4_failure_memory_review_worksheet_v1.md`
Failure fixture: `tests/fixtures/v4_failure_memory_fixture_v1.json`
Replay report: `build/v4_failure_memory_replay_v1.json`
Guard/relabel report: `build/v4_guard_relabel_implementation_report.json`
Puzzle seed fixture: `tests/fixtures/v4_puzzle_task_seed_v1.json`
Puzzle seed report: `build/v4_puzzle_task_seed_report.json`
Puzzle solver trace: `build/v4_puzzle_solver_trace_v1.json`
Puzzle failure memory: `tests/fixtures/v4_puzzle_failure_memory_v1.json`
Puzzle failure report: `build/v4_puzzle_failure_memory_report.json`
V4 candidate eval report: `build/v4_candidate_eval_report.json`
V4 sealed rotation report: `build/v4_sealed_rotation_report.json`
Sealed v4 fixture: `tests/fixtures/pattern_language_sealed_v4.json`
Sealed v4 measurement: `build/pattern_language_sealed_v4_measurement_report.json`

V4 uses pre-V3 non-sealed suspect/rejected/candidate material as Failure Memory input, not as direct success-pattern training. Step 5 exposes reviewed guard/relabel hints in route trace without rewriting packets. Step 6 adds a strict puzzle task schema and 12 non-sealed seed tasks. Step 7 records 12 solver traces, with 10 successes and 2 failures written only to Puzzle Failure Memory. Step 8 evaluates the V4 candidate on non-sealed lanes, rotates `pattern_language_sealed_v4.json`, and the subsequent one-time sealed v4 measurement consumes it with 15 errors. Puzzle learning is included as a separate failure-memory lane after the first human review pass.

Target minimums:

- intent_accuracy >= 0.90
- critical_signal_recall >= 0.85
- operation_exact_match >= 0.90
- constraint_exact_match >= 0.92
- risk_exact_match >= 0.95
- sealed_error_count <= 4
- critical_underprocessing == 0

## PLM V5: Critical Signal Recovery

Status: V5 Step 7 sealed v5 measurement completed; sealed v5 consumed; minimum not met; V6 rotation required before tuning.

Primary roadmap: `docs/PLM_V5_ROADMAP.md`
Targets and taxonomy: `build/v5_targets_and_roadmap_v1.json`
Non-sealed curriculum plan: `build/v5_nonsealed_curriculum_plan_v1.json`
Critical operations fixture draft: `tests/fixtures/v5_critical_operations_fixture_v1.json`
Critical operations report: `build/v5_critical_operations_fixture_report_v1.json`
Router generalization report: `build/v5_router_generalization_report.json`
Non-sealed replay gate report: `build/v5_nonsealed_replay_gate_report.json`
Sealed v5 rotation report: `build/v5_sealed_rotation_report.json`
Sealed v5 fixture: `tests/fixtures/pattern_language_sealed_v5.json`
Sealed v5 measurement: `build/pattern_language_sealed_v5_measurement_report.json`
Baseline measurement: `build/pattern_language_sealed_v4_measurement_report.json`

V5 uses sealed v4 measurement only as taxonomy. Sealed v4 text and labels are not training data. Step 4 router generalization replayed the 48-case non-sealed critical operations fixture at 1.0 across intent, critical signals, operations, constraints, and risk as a diagnostic non-gate check. Step 5 non-sealed replay gate passed, and Step 6 rotated a fresh sealed v5 fixture. Step 7 measured sealed v5 once and consumed it: intent_accuracy 0.750000, critical_signal_recall 0.375000, operation_exact_match 0.678571, constraint_exact_match 0.821429, risk_exact_match 0.892857, errors 18. V5 minimum was not met; sealed labels remain measurement-only and the immediate priority is V6 error taxonomy plus fresh sealed rotation before any tuning.

Target minimums:

- intent_accuracy >= 0.928571
- critical_signal_recall >= 0.875
- operation_exact_match >= 0.892857
- constraint_exact_match >= 0.928571
- risk_exact_match >= 0.964286
- sealed_error_count <= 6
- critical_signal_miss_count <= 2
- critical_underprocessing == 0

## PLM V6: Boundary Calibration And Sealed Rotation

Status: V6 Step 6 sealed v6 measurement completed; sealed v6 consumed; Step 7 post-v6 measurement taxonomy and successor planning next.

Primary roadmap: `docs/PLM_V6_ROADMAP.md`
Current state report: `build/v6_current_state_report_v1.json`
Non-sealed replay gate report: `build/v6_nonsealed_replay_gate_report_v1.json`
Sealed v6 rotation review: `build/v6_sealed_rotation_review_v1.json`
Sealed v6 rotation report: `build/v6_sealed_rotation_report_v1.json`
Sealed v6 fixture: `tests/fixtures/pattern_language_sealed_v6.json`
Sealed v6 measurement: `build/pattern_language_sealed_v6_measurement_report.json`
Step 6 summary: `build/v6_step6_measurement_summary.md`

Step 6 measured sealed v6 once and consumed it: intent_accuracy 0.750000, critical_signal_recall 0.357143, operation_exact_match 0.607143, constraint_exact_match 0.607143, risk_exact_match 0.750000, errors 23. Sealed labels remain measurement-only; rotation is required before tuning based on this result.

## PLM V7: Constraint And Critical Signal Recovery

Status: V7 Step 8 sealed v7 measurement completed; sealed v7 consumed; minimum not met; V8 taxonomy and fresh rotation required before tuning.

Primary roadmap: `docs/PLM_V7_ROADMAP.md`
Targets and taxonomy: `build/v7_targets_and_roadmap_v1.json`
Curriculum plan: `build/v7_nonsealed_curriculum_plan_v1.json`
Draft repair fixture: `tests/fixtures/v7_router_repair_fixture_v1.json`
Candidate replay report: `build/v7_router_repair_fixture_replay_v1.json`
Router generalization report: `build/v7_router_generalization_report_v1.json`
Non-sealed replay gate report: `build/v7_nonsealed_replay_gate_report_v1.json`
Sealed v7 rotation review: `build/v7_sealed_rotation_review_v1.json`
Sealed v7 rotation report: `build/v7_sealed_rotation_report_v1.json`
Sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`
Sealed v7 summary: `build/v7_step8_measurement_summary.md`

The V7 one-time sealed measurement scored intent_accuracy 0.785714, critical_signal_recall 0.642857, operation_exact_match 0.714286, constraint_exact_match 0.750000, risk_exact_match 0.785714, with errors 16. The fixture is consumed and sealed labels remain measurement-only; use this result for V8 taxonomy and fresh rotation planning, not same-cycle tuning.

## PLM V11: Value-Diff Recovery And Bridge Transfer Repair

Status: V11 Step 1 taxonomy and Step 1b baseline source recovery are completed; Step 2 repair curriculum planning is next.

Primary roadmap: `docs/PLM_V11_ROADMAP.md`
Targets and taxonomy: `build/v11_targets_and_roadmap_v1.json`
Post-v10 diagnostic: `build/v11_post_v10_measurement_diagnostic_v1.json`
Baseline sealed v10 measurement: `build/pattern_language_sealed_v10_measurement_report.json`

V11 uses sealed v10 measurement only as aggregate taxonomy/value-diff evidence. Sealed v10 text and labels are not training data. V10 measured intent_accuracy 0.785714, critical_signal_recall 0.400000, operation_exact_match 0.642857, constraint_exact_match 0.535714, risk_exact_match 0.678571, errors 23. V11 splits repair into intent-boundary, critical-signal, field-exactness, hook-overfire, and bridge-transfer validation lanes. Code audit triage confirms the pyc-loader baseline has been replaced by source-recovered, regression-tested runtime code; Step 2 is unblocked. Roadmap decision: can_advance=true, advance_to=v11_repair_curriculum_plan.

## PLM V10: Bridge Generalization And Exactness Recovery

Status: V10 Step 6 sealed v10 measurement completed; sealed v10 consumed; V11 taxonomy and fresh rotation required before tuning.

Primary roadmap: `docs/PLM_V10_ROADMAP.md`
Targets and taxonomy: `build/v10_targets_and_roadmap_v1.json`
Thought Color bridge decision: `build/v10_thought_color_bridge_isolated_adoption_decision_v1.json`
Thought Color bridge replay: `build/v10_thought_color_bridge_isolated_replay_report_v1.json`
V10+ learning lanes: router_judgment_lane and separated answer_prototype_lane are recorded in `build/v10_targets_and_roadmap_v1.json`
Mainline replay gate: `build/v10_mainline_replay_gate_report_v1.json`
Sealed v10 rotation review: `build/v10_sealed_rotation_review_v1.json`
Sealed v10 rotation report: `build/v10_sealed_rotation_report_v1.json`
Sealed v10 fixture: `tests/fixtures/pattern_language_sealed_v10.json`
Sealed v10 measurement: `build/pattern_language_sealed_v10_measurement_report.json`
Sealed v10 summary: `build/v10_step6_measurement_summary.md`
Post-v10 diagnostic: `build/v11_post_v10_measurement_diagnostic_v1.json`
Baseline sealed v9 measurement: `build/pattern_language_sealed_v9_measurement_report.json`

V10 uses sealed v9 measurement only as aggregate taxonomy. Sealed v9 text and labels are not training data. Thought Color bridge sources are not direct mainline training data; the accepted use is router generalization plus non-sealed replay. V10+ adopts two future lanes: router judgment as the primary mainline boundary-learning lane, and answer-only prototypes as a separated probe-generation lane. V9 measured intent_accuracy 0.892857, critical_signal_recall 0.857143, operation_exact_match 0.821429, constraint_exact_match 0.642857, risk_exact_match 0.750000, errors 17. Roadmap decision: can_advance=true, advance_to=v11_post_v10_measurement_taxonomy.

## PLM V8: Recovery Gate And Fresh Rotation

Status: V8 Step 8 sealed v8 measurement completed; sealed v8 consumed; V9 taxonomy and fresh rotation required before tuning.

Primary roadmap: `docs/PLM_V8_ROADMAP.md`
Targets and taxonomy: `build/v8_targets_and_roadmap_v1.json`
Recovery priority selection: `build/v8_recovery_debate_candidate_priority_selection_v1.json`
Approved priority replay: `build/v8_recovery_priority_review_provisional_test_report_v1.json`
Non-sealed replay gate report: `build/v8_nonsealed_replay_gate_report_v1.json`
Sealed v8 rotation review: `build/v8_sealed_rotation_review_v1.json`
Sealed v8 rotation report: `build/v8_sealed_rotation_report_v1.json`
Sealed v8 measurement: `build/pattern_language_sealed_v8_measurement_report.json`
Sealed v8 summary: `build/v8_step8_measurement_summary.md`
Baseline sealed v7 measurement: `build/pattern_language_sealed_v7_measurement_report.json`

V8 uses sealed v7 measurement only as aggregate taxonomy. Sealed v7 text and labels are not training data. V7 measured intent_accuracy 0.785714, critical_signal_recall 0.642857, operation_exact_match 0.714286, constraint_exact_match 0.750000, risk_exact_match 0.785714, errors 16. Step 8 measured sealed v8 once and consumed it: intent_accuracy 0.928571, critical_signal_recall 0.833333, operation_exact_match 0.785714, constraint_exact_match 0.785714, risk_exact_match 0.785714, errors 14. Sealed labels remain measurement-only; use this result for V9 taxonomy and fresh rotation planning, not same-cycle tuning.

## PLM V9: Exactness Recovery And Fresh Rotation

Status: V9 Step 8 sealed v9 measurement completed; sealed v9 consumed; V10 taxonomy and fresh rotation required before tuning.

Primary roadmap: `docs/PLM_V9_ROADMAP.md`
Targets and taxonomy: `build/v9_targets_and_roadmap_v1.json`
Candidate selection: `build/v9_accumulated_log_candidate_selection_v1.json`
Primary review replay: `build/v9_accumulated_primary_review_replay_report_v1.json`
Constraint/operation extension replay: `build/v9_constraint_operation_extension_replay_report_v1.json`
Non-sealed replay gate report: `build/v9_nonsealed_replay_gate_report_v1.json`
Sealed v9 rotation review: `build/v9_sealed_rotation_review_v1.json`
Sealed v9 rotation report: `build/v9_sealed_rotation_report_v1.json`
Sealed v9 fixture: `tests/fixtures/pattern_language_sealed_v9.json`
Sealed v9 measurement: `build/pattern_language_sealed_v9_measurement_report.json`
Sealed v9 summary: `build/v9_step8_measurement_summary.md`
Baseline sealed v8 measurement: `build/pattern_language_sealed_v8_measurement_report.json`

V9 uses sealed v8 measurement only as aggregate taxonomy. Sealed v8 text and labels are not training data. V8 measured intent_accuracy 0.928571, critical_signal_recall 0.833333, operation_exact_match 0.785714, constraint_exact_match 0.785714, risk_exact_match 0.785714, errors 14. Step 8 measured sealed v9 once and consumed it: intent_accuracy 0.892857, critical_signal_recall 0.857143, operation_exact_match 0.821429, constraint_exact_match 0.642857, risk_exact_match 0.750000, errors 17. Use this result for V10 taxonomy and fresh rotation planning, not same-cycle tuning.
