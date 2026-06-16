# 引継ぎレポート (2026-06-11 / セッション8)

> この文書は履歴です。最新状態は
> `HANDOVER_2026-06-11_session9.md`を参照してください。

## 完了事項

- pipeline versionを`1.3`へ更新
- package versionを`1.3.0a1`へ更新
- `vertical-unit-stack.v1`を実装
- Unit dependency graphと`max_depth`を設定化
- cycle、未知Unit、self dependency、depth超過を拒否
- Unit別output contractを実装
- `build`前へ`verify` gateを自動挿入
- `verified_assumptions`と上位Unit assumptionsを照合
- 未解決clarification、contract failure、verification failure、
  unverified assumptionで後続dispatchを停止
- `vertical_outputs`再投入によるstateless逐次進行
- CLI `--processing-mode vertical`
- CLI `--vertical-outputs-file`
- Horizontal JSONと7段階traceの後方互換を維持
- Vertical時だけ`vertical_stack`と8段階traceを出力
- 116 tests passed
- Pattern Router固定25件 selective accuracy 1.0
- threshold profile代表8件 accuracy 1.0

## Vertical Flow

```text
Horizontal Mesh winner
  -> Vertical dependency plan
  -> dispatch next unit only
  -> validate returned output contract
  -> stop or dispatch next unit
```

build flow:

```text
verify -> build
```

初回LLM Order modeは`verify`。verify出力が通過した次回呼び出しで
modeが`build`になる。

## 重要な境界

CoreはUnitの意味内容を生成しない。外部executorの出力を検証し、
次に実行可能なUnitを決めるrouting/orchestration層である。

外部executorが実際に時系列どおり呼ばれたか、verify内容が真に正しいかまでは
証明しない。Unit outputの保存・自動学習・疑似ラベル化は行わない。

## 次の着手点

v1.4 Hybrid Stack-Mesh。

1. Horizontal候補からVertical対象を選ぶ基準
2. 複数Stack間のIntegrator契約
3. step数・depth・Unit数の計算予算
4. timeoutと停止条件
5. stack failure時のfallback
6. Horizontal onlyとの固定比較fixture

実装前に、HybridがHorizontal onlyより有用かを測る評価fixtureと予算上限を
先に固定する。
