# VLTE-BPTM v1.2 Privacy-Minimized Observation Store

更新日: 2026-06-11

## 目的

観測レポートをローカルで比較可能にしつつ、少数集計・連続差分・
高cardinality項目から個別入力を推測するリスクを減らす。

この機能は完全匿名化、差分privacy、k-anonymityを保証しない。
`privacy-minimized local aggregate`として扱う。

policy schemaは`observation-privacy-policy.v1`、
storage schemaは`vlte-bptm.observation-store.v1`。

## 保存条件

- `--store`を指定した場合だけ保存する
- ローカルfilesystem上の`.db`だけを許可する
- UTC 24時間の固定bucket
- 1 bucketにつき書き込みは1回だけ
- 最低cohortは8 samples
- 3件未満のcellは保存しない
- exact sample countは保存せず、`8-15`などの帯へ変換する
- rateは保存しない
- 保持期間は30日
- 保存時に期限切れbucketを自動削除する

## 保存対象

- active bit frequency
- active bit count distribution
- selected Unit frequency
- selected Unit count distribution
- threshold profile frequency
- LLM Order mode frequency

各aggregateのcell名はbit index、正式Unit ID、正式profile名、正式mode名の
許可リストで検証する。任意文字列をcategoryとして保存できない。

## 保存禁止

- raw input、入力hash、routing key、Thought Code
- active bitsのsample単位配列
- selected Unitのsample単位配列
- Unit組合せ分布
- LLM出力、LLM Order本文、trace
- user/session/request識別子
- exact sample count、rate
- 自動学習や自動weight更新

## CLI

```powershell
python -m thought_core.observation `
  --input-file tests\fixtures\v1_0a_cases.json `
  --store data\observations.db

python -m thought_core.observation --list-store data\observations.db
python -m thought_core.observation --purge-store data\observations.db
```

同じUTC日へ再度保存すると拒否する。少数batchを後から加算すると
snapshot差分から属性を推測できるため、upsertは行わない。
`--store`指定時の標準出力も縮約済みrecordとし、詳細な非永続reportを
redirectやcommand logへ残さない。

## Access Boundary

- network APIや共有DB機能を提供しない
- DB fileの閲覧権限は実行OS userの管理責任とする
- POSIXでは作成fileをowner read/writeへ制限する
- Windows ACL、backup、disk encryptionはアプリ外の責任範囲
- 入力元JSON fileは保存層の管理対象外であり、利用者が別途管理する

## 削除

保存時の自動削除と`--purge-store`の明示削除を提供する。
SQLiteは`secure_delete=ON`を使用し、明示purgeで削除が発生した場合は
`VACUUM`を実行する。ただしfilesystem snapshotや外部backupの削除は保証しない。

設定は`thought_core/config/observation_privacy.json`、
独立fixtureは`tests/fixtures/v1_2_observation_privacy_policy.json`。
