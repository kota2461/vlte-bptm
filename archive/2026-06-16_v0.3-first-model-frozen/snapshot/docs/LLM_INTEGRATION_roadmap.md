# LLM Integration Roadmap

更新日: 2026-06-12

## Mission

Pattern Language Model、Processing Router、既存Core、Runtime、外部LLM/toolを
接続し、最終品質・費用・遅延を同じ評価単位で測定する。

## Integration v0.0: Contracts

Status: 設計完了

- 正本: `SEMANTIC_ROUTING_ARCHITECTURE_v0_1.md`
- Semantic PacketとProcessing Planの境界を固定
- Legacy Pattern Routerを比較baselineとして保持
- sealed v2をLegacy評価専用として未開封維持
- 自動学習禁止を全adapterへ継承

## Integration v0.1: Shadow Bridge

Status: planned

```text
Raw Prompt
  -> Semantic Adapter
  -> Semantic Packet
  -> Processing Router
  -> Processing Plan
  -> Core bridge
```

- 現行回答経路と並列にPlanを生成
- Coreへ`processing_mode`とruntime budgetを渡すbridge
- Planはログのみで、回答経路を変更しない
- request digestで原文、Packet、Plan、runを結び付ける
- raw promptとLLM outputを評価DBへ永続化しない

完了条件:

- 既存Horizontal / Vertical / Hybridテストが変化しない
- shadow Planを100%再現できる
- PacketとPlanのschema違反時は現行経路へfallbackする

## Integration v0.2: Offline A/B

Status: planned

比較:

1. 現行raw prompt経路
2. Legacy Adapter + Processing Router
3. Pattern Language Model + Processing Router
4. LLM Semantic Adapter + Processing Router

測定:

- blind回答品質
- 総token
- LLM呼出回数
- tool / dispatch回数
- latency
- normalized cost
- fallback / clarify率

完了条件:

- 出力生成者と評価者を分離する
- quality floorを満たさない削減案を不採用にする
- 短文でadapter費用が上回るケースを別集計する

## Integration v0.3: Live Shadow

Status: future

- 実LLM backendでtimeout / cancel / retryを検証
- 現行回答とshadow Planの差を観測
- model/provider別token価格をversioned設定にする
- privacy-minimized aggregateだけを保存

完了条件:

- quality-cost policyを人間が承認
- cost削減の信頼区間を報告
- production rollback pointを作成

## Integration v0.4: Guarded Rollout

Status: future

1. economyの単純入力だけ新経路へ送る
2. standardを段階導入
3. verified / deepは独立評価後に導入
4. quality、fallback、latency、costの規定値割れでrollback

## Research Track

本番Integrationとは別に、次を長期研究として扱う。

- Failure Memory / Guard Router
- 成功・失敗・補正履歴からの思考制御モデル
- 独立したCore Instruction Bitcode

Research Trackの出力をproduction labelや自動policy更新へ直接使用しない。
