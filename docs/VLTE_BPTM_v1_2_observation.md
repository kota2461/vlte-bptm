# VLTE-BPTM v1.2 Observation Report

更新日: 2026-06-11

## 範囲

入力をmemory内で集計する非永続レポートと、明示指定時だけ利用する
privacy-minimized local storeを提供する。
report schema versionは`vlte-bptm.observation-report.v1`。

```powershell
python -m thought_core.observation `
  --input-file tests\fixtures\v1_0a_cases.json
```

インストール後:

```powershell
vlte-observe --input-file inputs.json
```

入力ファイルは文字列、または`input`フィールドを持つobjectのJSON配列。

全threshold profile比較:

```powershell
python -m thought_core.observation `
  --compare-profiles `
  --input-file tests\fixtures\v1_0a_cases.json
```

比較schemaは`vlte-bptm.threshold-profile-report.v1`。

## 集計項目

- active bit indexごとの出現数・sample比率
- active bit count分布
- selected Unitごとの出現数・sample比率
- selected Unit組合せ分布
- selected Unit count分布
- threshold profile分布
- LLM Order mode分布

## 保存禁止境界

レポートへ次を含めない。

- raw input
- LLM出力
- 完全文のhashや復元可能な識別子
- 自動学習・自動weight更新の指示

`llm_order_mode_frequency`はCoreが生成したmode名の集計であり、
外部LLMの応答内容ではない。

通常は標準出力へ返すだけで保存しない。`--store`を明示した場合のみ、
`observation-privacy-policy.v1`に従って縮約した日次aggregateをSQLiteへ保存する。
詳細は`VLTE_BPTM_v1_2_privacy_store.md`を参照する。

## 契約

`privacy`:

```json
{
  "raw_input_stored": false,
  "llm_output_stored": false,
  "automatic_learning": false
}
```

独立fixtureは`tests/fixtures/v1_2_observation_schema.json`。

## 永続化

```powershell
python -m thought_core.observation `
  --input-file tests\fixtures\v1_0a_cases.json `
  --store data\observations.db
```

最低8件、UTC日次immutable bucket、3件未満cell抑制、30日保持とする。
raw input、exact sample count、rate、Unit組合せは保存しない。

## 後続評価

- 独立評価セットによるthreshold profileの再判断
- 複数bucket間の統計比較
- 異常判定baselineの版管理

## 初回Profile比較

代表8 fixtureでの結果:

| Profile | 平均active bits | expected mode accuracy |
| --- | ---: | ---: |
| auto | 16.25 | 1.0 |
| light_v1 | 9.25 | 1.0 |
| normal_v1 | 15.875 | 1.0 |
| design_v1 | 23.125 | 1.0 |
| deep_verify_v1 | 30.5 | 1.0 |

全profileでselected Unit countは各入力1件、expected mode accuracyは1.0だった。
差は想定どおりbit密度に現れたが、8件は調整根拠として少ないため係数・guardを
変更しない。比較レポートは`automatic_adjustment:false`を固定する。
