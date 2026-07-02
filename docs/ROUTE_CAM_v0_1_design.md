# Route CAM v0.1 (route-cam.v1) — SIG-64署名によるTCAM型ルート昇格

Status: 実装済み (adapter 0.3.2)、出荷storeは空。
背景と選定経緯は `docs/BIT_SYSTEMS_PROPOSALS_2026-07-02.md` §5.1。

## 1. 目的

margin gate (INTENT_GATE_MARGIN=0.20) が棄却する帯域では、marker不発の入力が
respond/economyの床へ落ちる。この帯の既知失敗を、**モデル重みに触れずに**
1件ずつ人間承認エントリで救済する経路を作る。背骨の小バッチ再学習が
held-outを悪化させた負の結果 (FINDINGS_role_split_v0 §4) への構造的回答:
CAMエントリの追加は重み経由の波及を持たない。

## 2. SIG-64署名 (`semantic_routing/signature.py`)

64bit。二層構造 (bit0-31=意味的 / bit32-63=非意味的・局所敏感):

```text
bits  0-6   intent one-hot (semantic-packet.v1 INTENTS順)
bits  7-10  information_state (missing / unverified / current / multiple)
bits 11-13  risk 温度計 (low=000, medium=001, high=011, critical=111)
bits 14-16  response_length 温度計 (unspecified=000 ... long=111)
bits 17-18  language (und=00, ja=01, en=10, mixed=11)
bits 19-21  operations flags (search / calculate / compare)
bits 22-26  temporal_kind one-hot — v0.4 Temporal Normalizer予約 (現在0)
bits 27-31  予約 (0)
bits 32-63  SimHash32 (text_features(text, 2048)の符号射影、
            BLAKE2b person=b"SIG64-simhash-v1")
```

- 温度計符号により、順序enumのハミング距離が段差に単調対応する
  (risk 1段差 = 距離1)。
- 原文は保持せず復元不能 (packet enum + 32bitスケッチのみ)。
  semantic-packet.v1のprivacy境界の内側。
- 決定的 (同一packet+text -> 同一署名)。

## 3. 照合と合成 (`semantic_routing/route_cam.py`)

```text
hit(entry)  <=>  popcount((SIG XOR entry.value) AND entry.care) <= entry.max_distance
複数hit: 最小距離 -> 高PLAN_RANK -> entry_id (決定的)
合成:    final_class = max_rank(baseline_plan.class, hit.plan_class)
```

- PLAN_RANK: economy=0 < standard=1 < deep=2 < verified=3 < clarify=4
  (role-splitの正準優先順を継承)。
- **昇格のみ**。baseline planが常に下限 (do-no-harm)。plan_class=economyの
  エントリはschemaレベルで拒否。
- 昇格時のplan本体は決定表と同じ非criticalテンプレートで再構成し、
  toolsはpacketから再導出。reason_codesに `route_cam_<entry_id>` を追記。

## 4. storeスキーマ (route-cam.v1)

```jsonc
{
  "schema_version": "route-cam.v1",
  "entries": [
    {
      "entry_id": "gate_miss_temporal_01",   // ^[a-z][a-z0-9_]{0,49}$
      "value": "0x0000000000020200",          // 64bit hex
      "care":  "0x0000000000060380",          // 0=don't care。全0は拒否
      "max_distance": 2,                       // 0..16
      "plan_class": "verified",                // economy不可
      "evidence_fixture": "build/intent_gate_calibration_v1.json#case-12",
      "intent_care_override": false,           // 省略可 (既定false)
      "notes": "..."                           // 省略可
    }
  ]
}
```

load時検証: schema_version / 未知フィールド拒否 / hex範囲 / entry_id一意 /
上限64エントリ (超過はエラー — 引き上げはレビュー変更でのみ)。

**intent-care guard**: `care` がbit0-6 (intent one-hot) を含む場合、
`intent_care_override: true` が無ければ拒否。CAMが照合される唯一の場面
(marker不発) では、署名のintent bitsはgate落ち学習モデルのtop-1で
汚染されているため、既定では信用しない。

## 5. adapter統合 (v0.3.2)

```text
extract_semantic_packet (markers-first、無変更)
  -> build_processing_plan (決定表、無変更)
  -> [store非空のときのみ] build_signature -> apply_route_cam
```

- 出荷store (`semantic_routing/config/route_cam_v1.json`) は空。
  空/欠損storeではplan・trace共にv0.3.1とbyte同一。
- store非空時のみtraceに `route_cam` (signature hex / entry_count / hit /
  distance / applied) を純観測で記録。
- 注入点: `route(text, route_cam=..., route_cam_path=...)`。

## 6. エントリ起票の運用規則 (これからの作業)

1. 起票元は実測失敗座標のみ: gate直下失敗 (margin 0.007-0.098のfallback帯) と
   弱カテゴリ (temporal / compound)。1エントリ = 1根拠fixture必須。
2. 追加ごとにheld-out + shadow評価を記録してから採用。
   careが緩い / max_distanceが大きいエントリは未知入力をshadowし得るため、
   「エントリ追加は副作用ゼロ」とは主張しない。
3. 評価はper-channel × per-classのgroup-holdout。fixture文面への過適合を
   防ぐ (fixture結合ルール禁止invariantと同型の懸念)。
4. sealed資産は使わない。campaignをgateにしない。

## 7. テスト (tests/test_route_cam.py, 14件)

署名の決定性・レイアウト・温度計単調性 / storeの検証 (intent-care guard、
economy拒否、cap、hex、一意性) / lookupの優先則 / 昇格のみの合成 /
空storeのbyte同一性 / route()経由の昇格とtrace。
