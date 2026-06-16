# 引継ぎレポート (2026-06-11 / セッション9)

## 完了事項

- pipeline versionを`1.4`へ更新
- package versionを`1.4.0a1`へ更新
- `hybrid-stack-mesh.v1`を実装
- control候補優先、fallback候補分離
- root score 0.75相対閾値、minimum score 0.12
- root scoreと依存候補scoreを合算して予算順位を決定
- 依存rootの重複Stack起動を防止
- 最大2 Stack、合計3 step、depth 2
- 1 API callにつき1 Unitだけdispatch
- Stack別のoutput namespace
- primary failure後にcompleted alternativeを採用
- 全Stack failure時の安全fallback
- Unit output本文をPipeline JSONへechoしない
- CLI `--processing-mode hybrid`
- CLI `--hybrid-outputs-file`
- 固定評価branch recall: Horizontal 0.60 / Hybrid 1.00
- 固定評価budget compliance 1.00
- 133 tests passed

## Hybrid Flow

```text
Horizontal candidates
  -> candidate threshold
  -> dependency coverage score
  -> 2 Stack / 3 step budget
  -> dispatch one unit
  -> validate namespaced output
  -> continue, integrate, or fallback
```

## 重要な発見

単独verifyのscoreが高い場合、単純なroot score順では`verify -> build`を持つ
build Stackが予算から落ちる。選択順位だけは依存候補scoreを合算し、
相対閾値はroot自身のscoreへ適用することで、過剰な候補除外を避けた。

固定評価の改善は候補枝coverageであり、回答品質の改善証明ではない。

## 次の着手点

v1.5 Runtime Evaluation and Executor Boundary。

1. 外部executor adapter
2. wall-clock timeout / cancel / retry
3. idempotencyとresume
4. blind answer-quality rubric
5. latency / dispatch数 / 推定費用
6. Hybrid winnerと人間評価の一致率

実出力の保存・自動学習は引き続き行わない。
