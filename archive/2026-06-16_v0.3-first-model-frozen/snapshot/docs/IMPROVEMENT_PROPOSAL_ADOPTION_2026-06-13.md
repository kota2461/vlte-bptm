# Improvement Proposal Adoption Record

更新日: 2026-06-13

## 採用済み

### ProcessingPlanからVertical / Hybridへのbridge

Status: shadow実装済み

- `run_core_shadow()`が原文digest、Semantic Packet、Processing Planの整合を検証
- Planの`core_mode`をCoreの`processing_mode`へ接続
- Vertical時はPlanの`primary_route`をrootとして固定
- `build + unverified`は`verify -> build`順を保証
- 現行のproduction runtime自動切替はまだ有効化しない

理由:

Vertical Stack自体は既に存在していたが、Processing Routerとの接続が未実装だった。
新しい推定ロジックを増やさず、既存契約を実行可能にするため優先価値が高い。

### Route group inhibition

Status: 実装済み

- `inhibition-matrix.v2`でRoute groupを定義
- group間係数をUnit間係数へ展開
- 個別Unit overrideも維持
- 展開後の係数はv1.0aの既存値と完全一致

理由:

現在は各Routeに1 Unitが中心なので即時精度は変わらない。一方、将来Unitを追加しても
全組合せを手作業で増やさずに済み、挙動を変えずにスケーラビリティを得られる。

### Unit selection policyの外部化

Status: 観測基盤を実装済み、重みは据え置き

- `unit-selection-policy.v1`を追加
- routing overlap / channel affinity / keyword / biasを個別記録
- 重みの合計、範囲、thresholdを起動時に検証
- Pipeline diagnosticsとUnit Activationから寄与を確認可能

現在値:

```text
routing overlap   0.40
channel affinity  0.20
keyword           0.40
```

channel affinity増加を見送った理由:

現在のfeature channelはUTF-8 byteを決定的に投影した非意味的bufferである。
この状態でchannel比重を上げても意味理解の改善根拠にならず、hash相関を強める危険がある。
重み変更はcomponent別blind評価を取得してから行う。

## 条件付き保留

### Semantic Embedding

Status: benchmark review後にadapter比較

外部model導入は依存、model容量、初回取得、latency、ライセンス、offline動作を増やす。
まず人間review済みPLM benchmarkで次を比較する。

- keyword baseline
- Legacy Pattern Router
- 小型multilingual embedding補助
- 小型LLM Semantic Adapter

embedding出力を正解ラベルやThought Codeそのものにはしない。Semantic Packet候補の
補助scoreとしてのみ使用する。

### Dynamic Threshold Profile

Status: shadow signal設計待ち

現行は入力長、design marker、verify markerを既に使用している。未知token率には
tokenizer定義、感情強度には独立ラベルが必要であり、曖昧なheuristicをproduction
profileへ直結しない。

先に非制御のdiagnosticsとして記録し、profile別の品質差が確認できたsignalだけを
採用する。

### Boundary Curriculum拡張

Status: 現PLM benchmarkのhuman review完了後

候補:

- 政治、価値観、未来予測
- 日英混在
- 複合意図
- 皮肉、謙遜、遠回し表現

現在review中の84件fixtureを変更するとreview logのhash契約が切れるため、別versionの
draftとして作成する。現sealedへ後付けしない。

## 将来項目

- failure caseだけの選択的再学習
- Action Vector追加
- routing confidence説明

これらはFailure Memory schema、独立fixture、rollback gateを先に定義してから扱う。
