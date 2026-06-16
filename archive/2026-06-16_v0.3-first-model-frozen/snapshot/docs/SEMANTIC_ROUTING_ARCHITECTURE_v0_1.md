# Semantic Routing Architecture v0.1

更新日: 2026-06-12

## 目的

生プロンプトの言語理解、処理経路の選択、思考Unitの実行、最終回答生成を
分離する。Routerを知識モデルや回答モデルへ肥大化させず、品質を保ちながら
LLM・tool・dispatchの費用を必要な入力へだけ配分する。

この設計は現行254件Pattern RouterとCore v1.6を置き換えず、その外側に
新しい契約境界を追加する。

## 全体構造

```text
Raw Prompt
  |
  v
Semantic Adapter
  |- Pattern Language Model (通常経路)
  |- LLM Semantic Adapter (低確信時だけ)
  `- Legacy Pattern Router Adapter (比較・移行用)
  |
  v
Semantic Packet
  |
  v
Processing Router
  |
  v
Processing Plan
  |
  v
VLTE-BPTM Core
  |- Horizontal Mesh
  |- Vertical Stack
  `- Hybrid Stack-Mesh
  |
  v
Runtime / Tools / Answer LLM
  |
  v
Answer
```

### 基本原則

1. Pattern Language Modelは答えを生成しない。
2. Processing Routerは生プロンプトを解釈しない。
3. Coreは意味内容を生成せず、Unitと実行順序を構成する。
4. Answer LLMが知識推論と文章生成を担当する。
5. 不確実性は隠さず、再解析・clarify・高い処理クラスへ送る。
6. 出力や評価結果を自動学習へ使用しない。

## コンポーネント境界

### Pattern Language Model

責務:

- 主要求と副要求の候補化
- 否定、制約、情報不足、検証要求、時点依存の抽出
- 原文根拠位置と不明項目の記録
- `Semantic Packet`の生成

非責務:

- 一般知識の記憶
- 回答本文の生成
- model/tool/Core modeの選択
- 最終的な安全判断

「Language Model」という名称だが、LLMの縮小版を目指さない。対象は
思考制御に必要な最小の意味信号だけである。

### Processing Router

責務:

- `Semantic Packet`から処理クラスを選ぶ
- Core mode、model class、tool、予算、fallbackを決める
- 選択理由をmachine-readableなreason codeで残す

非責務:

- 生プロンプトの語彙・文法解析
- Semantic Packetの意味を書き換えること
- 回答内容の生成
- 学習データの自動追加

v0.1では決定表によるpolicy routerとし、学習型Routerにはしない。

### VLTE-BPTM Core

現行のHorizontal / Vertical / Hybridを再利用する。Processing Planから
`processing_mode`と予算を受け、既存のAction Vector、LLM Order、Unit output
contract、停止条件を実行する。

shadow bridgeでは原文digest、Semantic Packet、Processing Planのroute整合を
再検証してからCoreを呼ぶ。Vertical PlanではPlanのprimary routeをrootへ固定し、
未検証buildを`verify -> build`の依存順で実行する。

### Answer LLM

原文と検証済みProcessing Planを受け取る。Semantic Packetだけから原文を
復元させない。回答LLMはCoreの命令、tool結果、Unit output contractに従う。

## Semantic Packet

schema: `semantic-packet.v1`

実装契約は`SEMANTIC_PACKET_v1.md`を正本とする。

```json
{
  "schema_version": "semantic-packet.v1",
  "request_digest": "SHA-256",
  "adapter": {
    "kind": "pattern_model",
    "version": "0.1"
  },
  "language": "ja",
  "intent_candidates": [
    {"intent": "verify", "confidence": 0.82},
    {"intent": "respond", "confidence": 0.14}
  ],
  "operations": ["verify"],
  "information_state": {
    "missing_required_information": false,
    "contains_unverified_claims": true,
    "requires_current_information": true,
    "multiple_intents": false
  },
  "constraints": {
    "response_length": "short",
    "formats": [],
    "must": ["cite_sources"],
    "must_not": []
  },
  "risk": {
    "level": "medium",
    "flags": ["current_information"]
  },
  "evidence": [
    {
      "signal": "verification_request",
      "start": 8,
      "end": 20
    }
  ],
  "unknowns": [],
  "conflicts": [],
  "confidence": 0.82
}
```

### 値域

初期intent:

```text
respond, explain, clarify, build, verify, summarize, explore
```

`unknown`を禁止しない。判断不能を誤った確定値へ変換するより、
`unknowns`と低い`confidence`を返す。

### 原文との関係

Processing Routerへ原文本文は渡さない。Integration層が次を検証する。

- `request_digest`が原文と一致
- evidence offsetが原文範囲内
- evidenceのsignal typeがschema上有効
- adapter出力に未知fieldがない

Routerは検証済みPacketと、文字数などの非意味的Input Envelopeだけを受ける。

## Processing Plan

schema: `processing-plan.v1`

実装契約は`PROCESSING_PLAN_v1.md`を正本とする。

```json
{
  "schema_version": "processing-plan.v1",
  "primary_route": "verify",
  "processing_class": "verified",
  "core_mode": "vertical",
  "model_class": "standard",
  "tools": ["web_search"],
  "budgets": {
    "max_dispatches": 2,
    "max_output_tokens": 700,
    "timeout_ms": 12000,
    "estimated_cost_units": 2.0
  },
  "fallback": "clarify",
  "reason_codes": [
    "verification_requested",
    "current_information_required"
  ]
}
```

### 処理クラス

| Class | 主用途 | Core | LLM / tool |
| --- | --- | --- | --- |
| `economy` | 明確な短い質問・単純要約 | horizontal | small、toolなし |
| `standard` | 通常説明・計画 | horizontalまたはvertical | standard |
| `verified` | 検証、時点依存、未検証前提 | vertical | verify/tool優先 |
| `deep` | 複合意図、複数案、重要枝比較 | hybrid | standard/large |
| `clarify` | 必須情報不足 | horizontal | 質問だけ |

### 初期policy

- 必須情報不足 -> `clarify`
- 明示的検証、時点依存、高risk -> `verified`
- 複数intentまたは複数重要枝 -> `deep`
- 単純respond / summarize -> `economy`
- buildは未検証前提があれば`verified`、なければ`standard`
- Packet低確信または矛盾あり -> LLM Semantic Adapterで一度だけ再解析
- 再解析後も不明 -> `clarify`または`verified`

現行のRouter単体実装は防御的に低confidence、unknown、conflictを`clarify`
へ送る。LLM Semantic Adapterによる再解析はIntegration層の次段階で実装する。

## Adapter選択とコスト

全入力をLLMで二重解析すると、短い入力では費用が増える。初期実装は
次の段階式とする。

```text
軽量Pattern Language Model
  |- 高確信 -> Processing Router
  `- 低確信 / conflict -> 小型LLM Semantic Adapter -> Processing Router
```

コスト削減はSemantic Adapter自体ではなく、不要な大型LLM、tool、
Vertical / Hybrid dispatch、長文生成を止めることで得る。

## Legacy Pattern Routerの扱い

現行254件モデルは`Raw Prompt -> Route`の比較baselineとして凍結する。
新しいProcessing Routerへ役割変更しない。

移行中はLegacy Adapterとして、予測RouteとoperatorをSemantic Packetの候補へ
変換できる。ただし制約、情報不足、risk、evidenceを十分に抽出できないため、
Pattern Language Model完成の代替とはしない。

sealed v2はLegacy Pattern Router評価用の未開封fixtureとして維持する。
新アーキテクチャの学習・設計・調整には使用しない。

## Failure Memoryの位置

Failure MemoryはPattern Language Modelの成功ラベルへ混ぜない。

```text
Semantic Packet
  -> Processing Router
  -> provisional Processing Plan
  -> Guard / Failure Memory
  -> corrected Processing Plan
```

v0.1では未実装とし、別schemaと独立fixtureを定義してから追加する。

## 評価の分離

### Pattern Language Model

- primary intent macro-F1
- critical signal recall
- constraint exact match
- evidence offset validity
- unknown / conflictの適切率
- confidence calibration

### Processing Router

- Processing Plan exact match
- critical under-processing rate
- unnecessary escalation rate
- model/tool/Core mode別の選択精度
- 予算遵守率

### End-to-End

- blind回答品質
- 総input/output token
- LLM呼出回数
- tool / dispatch回数
- latency
- normalized cost
- fallback / clarify率

成功条件は「Route精度最大化」ではなく、回答品質の最低基準を維持しながら
平均費用と遅延を下げることである。

## 導入境界

1. 最初はshadow modeでProcessing Planを記録するだけにする。
2. 現行経路の実回答を変更しない。
3. offline fixtureでunder-processingがないことを確認する。
4. 独立blind評価後に`economy`だけ実制御を許可する。
5. `verified` / `deep`の自動選択は別gateで承認する。
6. 自動学習とWikipedia大量投入は行わない。

## v0.1完了条件

1. Semantic PacketとProcessing Planのschemaがfixtureで固定される
2. Pattern Language ModelとProcessing Routerを独立してテストできる
3. Routerが生プロンプトなしで決定的にPlanを返す
4. 既存CoreへPlanを渡すbridgeがshadow modeで動く
5. 現行254件モデルとsealed v2が変更されない
6. 品質・費用・遅延を同一runで比較できる
