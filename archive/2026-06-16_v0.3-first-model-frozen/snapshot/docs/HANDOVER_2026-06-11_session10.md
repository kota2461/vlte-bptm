# 引継ぎレポート（2026-06-11 / セッション10）

## 完了状態

- pipeline version `1.5`
- package version `1.5.0a1`
- `ExecutorAdapter`境界
- wall-clock timeoutとcancel通知
- retryable error / timeoutの限定retry
- retry間で同一idempotency key
- input digest・mode照合付きresume
- 完了Unitの再dispatch防止
- Unit出力をsession JSONへechoしないcheckpoint
- 累積latency、attempt、dispatch、推定cost unit
- blind 5軸runtime評価
- latency / dispatch / cost / fallback集計
- runtime選択・Hybrid winnerと人間選好の一致率
- raw output非保存・自動学習禁止
- 152 tests passed

## 参照評価

| Mode | Quality | Latency ms | Dispatch | Cost |
| --- | ---: | ---: | ---: | ---: |
| Horizontal | 3.75 | 98.75 | 1.0 | 1.0 |
| Vertical | 4.35 | 178.75 | 2.0 | 2.0 |
| Hybrid | 4.70 | 225.00 | 2.5 | 2.5 |

- Hybrid quality gain over Horizontal: `+0.95`
- runtime selection / human agreement: `0.75`
- Hybrid Stack winner / human agreement: `0.75`

参照fixtureは計算契約の検証用であり、本番品質の独立証拠ではない。

## 発見

1. Hybridは参照fixture上で品質が高いが、latencyとcostも増える。
2. runtime選択と人間選好は完全一致ではなく、校正対象が残る。
3. Python threadの待機はtimeoutできるが、backend停止にはadapterのcancel実装が必要。
4. resume用checkpointはUnit出力を含むため、公開session JSONから分離した。
5. 実出力を保存せず、blind scoreと運用集計だけを評価資産にできる。

## 次の着手点

v1.6 Independent Runtime Study and Policy Calibration:

1. 独立した複数評価者によるblind collection
2. 評価者間一致度とconfidence interval
3. quality-cost frontier
4. input class別のHorizontal / Vertical / Hybrid選択policy
5. timeout / retry / fallbackの実backend測定
6. 評価データのconsent・retention・削除契約

自動学習と自動priority更新は引き続き行わない。
