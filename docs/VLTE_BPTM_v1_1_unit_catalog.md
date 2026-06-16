# VLTE-BPTM v1.1 Pattern Unit Catalog

更新日: 2026-06-11

## 契約

catalog schema versionは`pattern-unit-catalog.v1`。
正式一覧は`thought_core/config/pattern_units.json`に置く。

| Unit ID | Label | 主なAction |
| --- | --- | --- |
| explore | Exploration | creative, explain, reply |
| build | Implementation | plan, reply, explain |
| verify | Verification | verify, caution, reply |
| summarize | Compression | summarize, reply |
| clarify | Clarification | ask, caution, reply |
| respond | Direct Response | reply, explain |

全Unitは`unit_type == unit_id`、`process_mode == horizontal`とする。
順序、label、keywords、action weights、channel schemaはレビュー可能な契約値である。

## 検証

- Unit IDの一意性
- Unit TypeとIDの一致
- keywordが非空文字列かつ大文字小文字を無視して一意
- action weightが有限数`0.0..1.0`
- action axisがv1 Action Vectorの正式軸に含まれる
- channel schemaが正式registryに存在する
- Vertical Unitを混在させない

独立fixtureは`tests/fixtures/v1_1_pattern_units.json`とする。

## 変更手順

Unit追加・削除・keyword・weight・channel schema変更は、次を同時に行う。

1. `pattern_units.json`更新
2. channel schemaとinhibition matrixの整合確認
3. v1.1 fixture更新
4. 代表入力と全テストによる回帰確認
5. catalog schemaまたはpipeline versionの変更判断
