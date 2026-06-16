# 引継ぎレポート（2026-06-11 / セッション11）

## v1.6 Alpha

- pipeline version `1.6`
- package version `1.6.0a1`
- `independent-runtime-study-policy.v1`
- `independent-runtime-study.v1`
- `independent-runtime-study-report.v1`
- `runtime-selection-policy.v1`
- `response-accuracy-audit.v1`
- raw input / raw output非保存
- reviewer consent / independence gate
- case bootstrap confidence interval
- quadratic weighted kappa
- preference pair agreement
- Wilson interval
- quality-cost Pareto frontier
- input class別policy calibration
- policy自動有効化禁止
- 174 tests passed

## 現状精度

- Core / 代表fixture: `8/8`
- Core / Router境界fixture: `9/25`
- Pattern Router / 境界fixture raw: `25/25`
- Pattern Router / Core代表fixture raw: `5/8`
- Pattern Router holdout: `26/30`
- repeated CV: `0.768675`
- Pattern Router境界fixtureの学習DB完全一致: `11/25`
- semantic answer independent study: `0件`

結論: production response accuracyは未確立。

## Study Contract Fixture

- cases: 4
- reviewers: 3
- weighted kappa: `0.708609`
- preference pair agreement: `0.833333`
- runtime / majority preference agreement: `0.75`
- Vertical gain interval: `-0.133333..1.05`
- Hybrid gain interval: `-0.116667..1.433333`

synthetic contract fixtureのためpolicy evidenceには使用しない。
全input classのactive modeはHorizontalのまま。

## Evidence Gate

v1.6実装は完了しているが、次は外部状態が必要。

1. 独立評価者3名以上
2. input classごと最低20件
3. 選好率±0.10を保守的に測る場合は計97件
4. 実backend運用値
5. 人間によるversioned policy承認

CoreとPattern Routerはまだ統合しない。先にgrouped / sealed route評価を行う。
