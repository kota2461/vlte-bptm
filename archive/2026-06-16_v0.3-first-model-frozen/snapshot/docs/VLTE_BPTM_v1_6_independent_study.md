# VLTE-BPTM v1.6 Independent Runtime Study and Policy Calibration

更新日: 2026-06-11

## 状態

v1.6 alphaの評価基盤は実装済み。独立した実評価者・実backendによる
production evidenceは未収集であり、Runtime Selection Policyは`draft`のままである。

## 目的

Horizontal / Vertical / Hybridを、回答生成者から独立した複数評価者が
blind評価し、品質差・費用差・評価者一致度・不確実性を同時に測定する。

評価結果から処理mode候補を提案できるが、自動的には有効化しない。

## Schema

- `independent-runtime-study-policy.v1`
- `independent-runtime-study.v1`
- `independent-runtime-study-report.v1`
- `runtime-selection-policy.v1`

既定policyは`thought_core/config/independent_study.json`、
未承認の選択policyは`thought_core/config/runtime_selection_policy.json`に置く。

## Privacy

study recordは次だけを保存する。

- pseudonymous reviewer ID
- input class
- candidate ID
- 5軸score
- preferred candidate ID
- latency / dispatch / normalized cost / fallback
- blind解除用candidate-to-mode対応

raw input、raw output、評価者名、自由記述はschema外であり、未知fieldとして拒否する。
保持期間は30日、明示consent必須、自動学習は禁止する。

## Blind Rubric

- correctness
- relevance
- completeness
- assumption control
- clarity

各scoreは整数`1..5`。各caseを最低3名が評価し、全候補を同じrubricで採点する。

## 統計

### 品質区間

caseごとの平均scoreを単位として、決定的seedによるpercentile bootstrapを行う。
reviewer×dimensionを独立sampleとして水増ししない。

### 評価者一致

- reviewer pairごとのquadratic weighted kappa
- preferred modeのpairwise agreement
- unanimous preference rate
- Runtime選択とreviewer多数決の一致率およびWilson区間

### Sample Size

- input classごとにpolicy検討最低20件
- 選好率を95%信頼水準・±0.10で測る保守的必要数は97件
- 品質差は観測されたcase間分散から必要件数を再推定

## Quality-Cost Frontier

次のすべてを使ってmodeのPareto frontierを計算する。

- quality: 最大化
- latency: 最小化
- dispatch count: 最小化
- estimated cost: 最小化
- fallback rate: 最小化

品質が高いだけでは採用しない。別modeが同等以上の品質で全運用値も良い場合、
そのmodeはdominatedとして除外する。

## Policy Gate

input classごとに品質平均が最大のmodeをprovisional candidateとするが、
次をすべて満たすまでactive modeは`horizontal`のままにする。

1. `evidence_origin=independent_blind_collection`
2. 全reviewerが回答生成から独立し、consent済み
3. classごとに20件以上
4. Horizontal比quality gainの95%下限が`0.25`以上
5. cost倍率が`2.5`以下
6. latency倍率が`3.0`以下
7. 人間review gateでversioned policyを承認

policyは`automatic_activation=false`を必須とし、承認前のclass mappingは空である。

## Contract Fixture

`tests/fixtures/v1_6_independent_study.json`は統計計算の参照fixtureであり、
synthetic contract dataである。

| Metric | Result |
| --- | ---: |
| Cases | 4 |
| Reviewers | 3 |
| Pairwise quadratic weighted kappa | 0.709 |
| Preference pair agreement | 0.833 |
| Runtime / majority preference agreement | 0.750 |
| Vertical quality gain 95% interval | -0.133 to 1.050 |
| Hybrid quality gain 95% interval | -0.117 to 1.433 |

両品質差とも0を跨ぎ、各input classは1件しかない。したがって採用根拠にはならず、
全classのactive modeはHorizontalのままである。

## 実行

```powershell
python -m thought_core.independent_study `
  --input-file tests\fixtures\v1_6_independent_study.json
```

## 未完了

- 独立評価者の募集とconsent取得
- classごと20件以上の実回答収集
- 実backendのtimeout / retry / cost測定
- policy承認

これらはローカル実装だけでは代替できないため、v1.6 evidence gateとして残す。
