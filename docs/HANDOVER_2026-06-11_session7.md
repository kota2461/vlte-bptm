# 引継ぎレポート (2026-06-11 / セッション7)

> この文書は履歴です。最新状態は
> `HANDOVER_2026-06-11_session8.md`を参照してください。

## 完了事項

- v1.2 privacy永続化契約を実装
- `observation-privacy-policy.v1`
- `vlte-bptm.observation-store.v1`
- 明示`--store`指定時だけローカルSQLiteへ保存
- UTC日次immutable bucket
- minimum cohort 8、minimum cell count 3
- exact sample countをcohort帯へ変換
- rateとselected Unit組合せを非保存
- aggregate名とcell名を固定allowlistで検証
- raw input、hash、Thought Code、LLM出力、識別子を拒否
- 30日保持、自動purge、明示purge、`secure_delete`、`VACUUM`
- package versionを`1.2.0a2`へ更新
- 101 tests passed
- Pattern Router固定25件 selective accuracy 1.0を維持

## 発見と対処

生入力を保存しないだけでは、少数集計や連続snapshotの差分から個別sampleの
属性を推測できる。次の対処を契約へ追加した。

1. 最低8件未満は永続化しない
2. 同じUTC日への追記・更新を禁止する
3. 3件未満のcellを保存しない
4. exact sample countとrateを保存しない
5. 高cardinalityなUnit組合せを保存しない

この方式は完全匿名化や差分privacyを保証しない。ローカル集計の復元リスクを
低減する設計である。

## CLI

```powershell
python -m thought_core.observation `
  --input-file tests\fixtures\v1_0a_cases.json `
  --store data\observations.db

python -m thought_core.observation --list-store data\observations.db
python -m thought_core.observation --purge-store data\observations.db
```

## 次の着手点

v1.3 Vertical Unit Stackの実装前設計。

1. `input_dependencies`の参照形式
2. Unitごとの`output_contract`
3. `max_depth`と循環依存拒否
4. 中間verify Unitの挿入条件
5. 誤前提伝播の検出と停止理由
6. Horizontal pipelineとの後方互換境界

実装前に、依存graphのfixtureと失敗時のLLM Order契約を先に固定する。
