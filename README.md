# VLTE-BPTM v1.6

自然言語入力を64bit Thought Codeへ変換し、Horizontal MeshでUnitを選択します。Vertical StackはUnit出力を逐次検証し、Hybrid Stack-Meshは予算内の複数Stackから安全な完了枝を選択します。v1.6では独立blind study契約、統計評価、選択policy校正、現行精度監査を追加しました。

v1.6はalphaです。評価基盤は実装済みですが、独立production evidenceは未収集で、
mode選択policyは未承認の`draft`です。

```text
input
  -> active_bits
  -> selected_units
  -> inhibition integration
  -> horizontal mesh
  -> optional vertical stack
  -> optional hybrid stack mesh
  -> action_vector
  -> llm_order
  -> optional external runtime executor
```

## 重要な境界

- Thought Codeの64bitは外部ルーティングキーです。
- Pattern Unitの`C=64`はUnit内部のfeature channel数です。
- Pattern Unitの`16×16`は意味座標ではなく活性バッファです。
- 既定はHorizontal Processingです。
- Vertical Stackは`--processing-mode vertical`で明示的に有効化します。
- Hybrid Stack-Meshは`--processing-mode hybrid`で有効化します。
- Pattern Unit一覧とchannel schemaは外部設定・独立fixtureで固定されています。
- Action VectorとLLM Orderは個別schema versionを持ちます。
- クラウドLLM出力の保存、自動学習、100×100マップは実装しません。

## 実行

```powershell
python -m thought_core --json "この設計をレビューしてください"
python -m thought_core --json --log-level INFO "この機能を実装してください"
python -m thought_core --threshold-profile light_v1 "こんにちは"
python -m thought_core --json --processing-mode vertical "この機能を実装してください"
python -m thought_core --json --processing-mode vertical --vertical-outputs-file build\vertical_outputs.json "この機能を実装してください"
python -m thought_core --json --processing-mode hybrid "設計案を比較して要約してください"
python -m thought_core --json --processing-mode hybrid --hybrid-outputs-file build\hybrid_outputs.json "設計案を比較して要約してください"
python -m thought_core.observation --input-file tests\fixtures\v1_0a_cases.json
python -m thought_core.observation --compare-profiles --input-file tests\fixtures\v1_0a_cases.json
python -m thought_core.observation --input-file tests\fixtures\v1_0a_cases.json --store data\observations.db
python -m thought_core.observation --list-store data\observations.db
python -m thought_core.runtime_evaluation --input-file tests\fixtures\v1_5_runtime_evaluation.json
python -m thought_core.independent_study --input-file tests\fixtures\v1_6_independent_study.json
python -m thought_core.accuracy_audit
```

インストール後は次のコマンドも利用できます。

```powershell
vlte-bptm --json "入力文"
vlte-observe --input-file inputs.json
vlte-runtime-eval --input-file runtime_evaluation.json
vlte-study-eval --input-file independent_study.json
vlte-accuracy-audit
```

Python API:

```python
from thought_core import process, run_with_executor

result = process("この設計をレビューしてください")
payload = result.as_dict()
print(payload["llm_order"])

session = run_with_executor(
    "この機能を実装してください",
    "vertical",
    adapter,
)
print(session.as_dict())
```

`run_with_executor`のUnit出力は公開session JSONへ含まれず、resume用checkpointに
のみ保持されます。

## JSON

主要フィールド:

```text
schema_version
pipeline_version
input
thought_code
active_bits
selected_units
horizontal_mesh
vertical_stack (vertical時のみ)
hybrid_stack_mesh (hybrid時のみ)
action_vector
llm_order
metrics
trace
diagnostics
```

`trace`には入力からLLM Orderまでの各処理段階が順番に記録されます。
Runtime Sessionは別schemaで、status、累積metrics、非公開出力を除いたcheckpoint、
最終Pipeline Stateを持ちます。

## テスト

```powershell
python -m pytest -q
```

代表入力は`tests/fixtures/v1_0a_cases.json`に固定されています。

## Pattern Lab

人間評価付きのルーター学習とPattern DBは、Coreから分離した`pattern_learning`パッケージで提供します。

```powershell
python -m pattern_learning init
python -m pattern_learning seed-demo
python -m pattern_learning seed-boundaries
python -m pattern_learning seed-boundaries-v2
python -m pattern_learning serve
```

評価UIは`http://127.0.0.1:8765`です。承認済みPatternが2Route以上に蓄積されたら、UIまたは次のコマンドで明示的に学習します。

```powershell
python -m pattern_learning train      # 候補モデルの学習
python -m pattern_learning promote    # ゲート合格時のみデプロイ昇格
python -m pattern_learning predict "この設計を検証してください"
$env:PYTHONPATH="."; python build\router_eval.py
```

詳細は`docs/PATTERN_LAB.md`を参照してください。

## 文書

- `docs/VLTE_BPTM_v1_0a.md`: 正本仕様
- `docs/VLTE_BPTM_v1_1_channel_schemas.md`: channel schema契約
- `docs/VLTE_BPTM_v1_1_unit_catalog.md`: 正式Unit一覧
- `docs/VLTE_BPTM_v1_1_output_schemas.md`: Action Vector / LLM Order契約
- `docs/VLTE_BPTM_v1_2_observation.md`: 非永続の観測レポート契約
- `docs/VLTE_BPTM_v1_2_privacy_store.md`: privacy縮約・保持・削除契約
- `docs/VLTE_BPTM_v1_2_horizontal_mesh.md`: Unit投票・優先度契約
- `docs/VLTE_BPTM_v1_3_vertical_stack.md`: 依存graph・出力契約・停止条件
- `docs/VLTE_BPTM_v1_4_hybrid_stack_mesh.md`: 候補選択・予算・Integrator
- `docs/VLTE_BPTM_v1_5_runtime_executor.md`: Executor・resume・blind評価
- `docs/VLTE_BPTM_v1_6_independent_study.md`: 独立評価・統計・policy校正
- `docs/VLTE_BPTM_v1_6_accuracy_audit.md`: 現状の応答精度調査
- `docs/VLTE_BPTM_v1_0a_design.md`: 実装設計
- `docs/VLTE_BPTM_v1_0a_review_response.md`: レビュー対応
- `docs/VLTE_BPTM_roadmap.md`: ロードマップ
- `docs/PATTERN_LAB.md`: 評価UI・Pattern DB・ルーター学習
- `docs/PATTERN_BOUNDARY_CURRICULUM_v2.md`: 境界作例の由来・レビュー・分割契約
- `docs/PATTERN_BOUNDARY_V2_UNTRAINED_ACCURACY.md`: v2候補の未学習精度
- `docs/EXTERNAL_REVIEW_REPORT_2026-06-11.md`: 外部AI・人間レビュー用の現状統合レポート
- `docs/PATTERN_ROUTER_v0_1_1_spec.md`: 現行ルーター・較正・評価契約
- `docs/PATTERN_ROUTER_v0_2_design.md`: 次期の独立評価設計
- `docs/SEMANTIC_ROUTING_ARCHITECTURE_v0_1.md`: 意味抽出・処理Router・Core・LLMの責務境界
- `docs/SEMANTIC_PACKET_v1.md`: 最小意味信号Packetのschema契約
- `docs/PROCESSING_PLAN_v1.md`: 処理経路・予算Planのschema契約
- `docs/PATTERN_LANGUAGE_MODEL_roadmap.md`: 最小意味信号抽出モデルのロードマップ
- `docs/PROCESSING_ROUTER_roadmap.md`: 処理経路・予算Routerのロードマップ
- `docs/LLM_INTEGRATION_roadmap.md`: Core・Runtime・LLM接続と品質費用評価
- `docs/HANDOVER_2026-06-11_session12.md`: 境界候補v2・DB状態・次の学習地点
- `docs/BIT_SYSTEMS_PROPOSALS_2026-07-02.md`: bitベース新システム12案の提案・批評・選定レポート
- `docs/ROUTE_CAM_v0_1_design.md`: SIG-64署名 + TCAM型ルート昇格 (route-cam.v1) の契約
- `docs/THOUGHT_JOURNAL_v0_1_design.md`: TSRターン間XORデルタジャーナルの契約

旧`thought_register`は移行比較用として残しています (Thought Journalは同
パッケージへの後方互換拡張)。
