# Semantic Adapter 失敗診断 / レビュー誘導 (2026-06-13)

対象: `conversation_accumulation_v1_report.json`(adapter `deterministic_signal_extractor` v0.2、24件 batch-01)
目的: V2測定readiness gateの人間レビュー(0/40)を、盲目的な確認から**狙い撃ち**へ変える。
状態: 測定ブロック中。sealed v2(`pattern_language_sealed_v2.json`, 28件)は未開封・未測定を維持。

## 0. 前提と読み方

失敗12件はすべて plan側(`processing_plan.py`)ではなく、手前の **SemanticPacket 抽出器**
(`semantic_routing/baseline.py`)に起因する。plan は契約検証付きで正しく動作している。

各案件に2つのタグを付ける。

- **coverage** = 抽出器の網羅ギャップ。期待ラベルは争いがなく、レビューでは「ラベル正しい・
  抽出器が拾えていない」を確認するだけでよい。
- **policy** = 期待ラベル自体が未確定の方針判断を含む。レビューで**人間が批准/修正**すべき対象。
  ここを抽出器に合わせ込んではならない(下記ガードレール)。

### ガードレール(測定の健全性)

精度ゲート0.90は、抽出器をチューニングする対象と同じ accumulation 集合で測る。
24件 draft に抽出器を合わせ込むと (1) 未レビュー oracle への過適合、(2) ゲートに対して循環、
になる。**coverage 修正であっても、検証は人間レビュー済みデータ/新規ホールドアウトで行い、
この24 draft をフィッティング対象にしない。** policy 案件は批准が済むまで抽出器を変更しない。

## 1. クラスタA — no-match 0.45 フォールバック (7件 / coverage)

機構: intentマーカーがどれも一致しないと `_intent_scores` が `respond=0.45` を割り当てる
([baseline.py:418-419](../semantic_routing/baseline.py))。confidence<0.60 のため
`unknowns=["primary_intent"]` となり([baseline.py:511](../semantic_routing/baseline.py))、
plan は clarify へ退避する([processing_plan.py:341-365](../semantic_routing/processing_plan.py))。
結果、(a) intent取り違え と (b) economy→clarify の浅化が同時に起きる。

| id | category | expected | actual | 問題 |
| --- | --- | --- | --- | --- |
| accum-b01-001 | conversation_response | respond/economy | respond/clarify (0.45) | plan浅化 |
| accum-b01-003 | conversation_response | respond/economy | respond/clarify (0.45) | plan浅化 |
| accum-b01-005 | indirect_explanation | explain/economy | respond/clarify (0.45) | intent+plan |
| accum-b01-006 | indirect_explanation | explain/economy | respond/clarify (0.45) | intent+plan |
| accum-b01-008 | indirect_explanation | explain/economy | respond/clarify (0.45) | intent+plan |
| accum-b01-017 | temporal_disambiguation | respond/economy | respond/clarify (0.45) | plan浅化 |
| accum-b01-019 | temporal_disambiguation | respond/economy | respond/clarify (0.45) | plan浅化 |

レビュー判断: **ラベルは正しい**(挨拶・平易な質問は respond/economy、間接的な
「仕組みが分かりづらい」は explain)。承認推奨。設計上の含意は2点で、これは coverage 修正の
候補として記録する(今は変更しない):
1. respond/explain のマーカー網羅が会話的・間接的言い回しを取りこぼしている。
2. no-match の 0.45 が「確信ある平易応答」と「intent不明」を区別できず、両方 clarify に落ちる。
   この2状態の分離は将来の抽出器改修の論点。

## 2. クラスタB — verify/build 順序 (4件 / policy+coverage / **critical under-processing**)

機構: verify を build の前提として付与する条件が `MULTIPLE_INTENT_MARKER`(「その上で」
「and then」等)の発火に依存する([baseline.py:445](../semantic_routing/baseline.py))。
また併存時の build昇格も同マーカー依存([baseline.py:417](../semantic_routing/baseline.py))。
接続詞が無いと verify(優先度5)が build(4)に勝つ([baseline.py:31-39](../semantic_routing/baseline.py))。

| id | category | expected | actual | critical | 問題 |
| --- | --- | --- | --- | --- | --- |
| accum-b01-009 | verify_then_build | build/verified/vertical | build/standard/horizontal | ✔ | 検証ゲート脱落→build浅化 |
| accum-b01-011 | verify_then_build | build/verified/vertical | verify/verified/vertical | ✔ | verifyで停止、buildに未到達 |
| accum-b01-012 | verify_then_build | build/verified/vertical | verify/verified/vertical | ✔ | 同上 |
| accum-b01-013 | mixed_language | build/verified/vertical | verify/verified/vertical | ✔ | 同上 |

**critical under-processing** とは「思考モジュールが必要より浅く処理する」状態で、
ゲートは0件許容。安全性に直結するため最重要。ただし期待ラベルは**方針判断を含む**:

> **方針論点 B-1**: 接続詞のない「主張/数値 → build」(009)は、verify前提を伴う
> verified/vertical を*必須*とすべきか? それとも build/standard も許容か?
> (= 思考モジュールはどこまで自発的に検証を差し込むべきか)

> **方針論点 B-2**: verify と build が併存する依頼で、primary はどちらか?
> 期待ラベルは「build(成果物)が primary、verify は前提」。この優先順位を批准するか?
> 批准するなら現行の優先度表(verify>build)と矛盾するため、抽出器側の順序規則を
> 「sequenced/implied verify は build に従属させる」へ改める設計変更が要る。

レビュー判断: **まず B-1/B-2 を批准/修正してからでないと、この4件は測定 ground truth に
ならない。** 批准後に限り、抽出器の順序規則を coverage+policy 修正として設計する
(接続詞依存の撤廃)。critical なので最優先で人間判断を仰ぐ。

## 3. クラスタC — compound 優先度 (1件 / policy)

機構: summarize(優先度6)が build(4)に勝つ([baseline.py:31-39](../semantic_routing/baseline.py))。

| id | category | expected | actual | 問題 |
| --- | --- | --- | --- | --- |
| accum-b01-024 | compound_intent | build/deep/hybrid | summarize/economy/horizontal | intent取り違え+浅化 |

> **方針論点 C-1**: 「要約 + 構築」併存で primary はどちらか? 期待は build。
> B-2 と同じ「成果物優先」原則なら build。批准するなら優先度表の再設計が要る
> (summarize を build より上に置く現行重みの根拠を問い直す)。

レビュー判断: C-1 を批准/修正。B-2 と合わせて「複合依頼の primary 決定原則」を
一度きちんと決めると、B・C 両方の抽出器修正方針が定まる。

## 4. レビュー手順(推奨)

1. **クラスタA 7件**: ラベル妥当性を確認して承認(coverage、争いなし)。
2. **方針論点 B-1 / B-2 / C-1 を先に決定**(複合依頼と自発的検証の原則)。これが
   クラスタB・Cのラベル批准の前提。
3. B(4件)・C(1件)を批准後ラベルで承認/修正。
4. 残りの draft(成功側12件含む)も同基準でレビューし、**40件の人間承認**に到達させる。
5. 承認集合が固まったら、accuracy gate / critical-underprocessing gate を**抽出器を変えずに**
   再測定。ここで初めて「現行抽出器の真の到達点」が分かる。
6. その後に抽出器修正を設計する場合、検証は承認済み集合 + 新規ホールドアウトで行い、
   この24 draft をフィッティング対象にしない。sealed v2 は readiness gate 通過まで未開封。

## 5. 集計

- 失敗12件: クラスタA=7(coverage)、B=4(policy+coverage, critical)、C=1(policy)。
- critical under-processing 4件はすべてクラスタB(verify/build 順序)。
- 方針批准が必要な案件: 5件(B 4 + C 1)、論点は B-1 / B-2 / C-1 の3つ。
- coverage のみ(ラベル承認可): 7件。
- ゲート再測定とsealed v2開封は、40件承認 + accuracy/critical ゲート充足が前提。
