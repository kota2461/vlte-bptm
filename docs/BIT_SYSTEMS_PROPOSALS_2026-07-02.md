# bitベース新システム提案レポート — 構造分析から実装まで (2026-07-02)

TSR (thought_register) と全派生系 (VLTE-BPTM v1.6 / semantic_routing /
pattern_learning / role-split detectors / layered-thought-color / debate_lab)
の構造を精読し、「0/1のbit単位を基底表現とする新システム」を4つの専門レンズで
12案生成、辛口批評で選別した。**採用1件・修正付き有望5件・不成立6件**。
上位2案 (SIG-64 Route CAM / TDJ Thought Journal) は本レポートと同時に
最小実装済み (§5)。

生成・批評は多エージェントワークフロー (読解6 + 提案4レンズ + 批評4、
計14エージェント) で実施した。

## 1. 読み取った構造の骨格

系譜は「64bitの意味の扱い」を軸に読める:

```text
TSR (thought_register)      64bit = 全bit命名済みの意味的レジスタ
                            (Drive/Affect/Cognition/Action x 16bit)
  -> VLTE-BPTM (thought_core)  64bit = 非意味的ルーティングキーへ反転
                            (BLAKE2b、Mesh/Stack/Hybrid)
    -> semantic_routing     bit列を捨てenum契約へ (semantic-packet.v1、
                            markers-first + margin gate 0.20)
      -> role-split          9ヘッド + monotone join (max/OR)
      -> thought-color       19bit = base11 + stance3 + operation3 + intensity2
```

全系に共通する設計規律 (提案の制約条件):
自動学習禁止 / human-approvedラベルのみ / 凍結config + schema_version +
load時検証 / do-not-regress fixture / sealed分離 / 原文非保存のprivacy境界 /
決定性 (同一入力 -> 同一出力)。

## 2. 提案が狙った構造的欠落

ドキュメントに明記済みの欠落・負の結果:

| # | 欠落 | 出典 |
|---|------|------|
| G1 | TSRのintensityは判定に一切効かない (表示専用) | thought_register/state.py |
| G2 | resolverの主要分岐がdead code (SAFE_REFUSAL等をencoderが立てない) | thought_register/encoder.py |
| G3 | 全系が単一ターン純関数 (状態の近さの概念が無い) | 各仕様書 |
| G4 | margin gateのスカラー1点トレードオフ (junk棄却 vs pos_coverage 12pt) | build/intent_gate_calibration_v1.json |
| G5 | 背骨の小バッチ再学習は負の結果 (k-fold +0.5ppでもheld-out悪化) | experiments/2026-06-19_role-split-detectors/FINDINGS |
| G6 | role-splitのde-escalation 18 (弱learnedアームがgateで沈黙) | 同上 |

## 3. 12案の一覧と判定

| レンズ | 提案 | 判定 | 一言 |
|--------|------|------|------|
| ISA | SIG-64 思考TLB (TCAM Route CAM) | **keep** | G4/G5への構造的回答。実装済 (§5.1) |
| 符号理論 | TDJ (XORデルタ思考ジャーナル) | revise→実装 | G3/G2。消費側規則を同時実装 (§5.2) |
| ISA | TIC-64 (思考割り込みコントローラ) | revise | bit位置=優先度はレイアウトと衝突。順列テーブル外部化が条件 |
| 神経 | BSQM相当は分散レンズ参照 / STR (スパイキングレジスタ) | revise | 定数driveでは力学が退化。時変drive+encoder拡張が前提 |
| 分散 | BSQM (Bit-Sliced Quorum Mesh) | revise | 票源単位 (実質2-3) で数え直す条件付きでG6に有望 |
| 分散 | LATREG (TSRレジスタCRDT同期) | revise | epoch跨ぎjoinの形式化と実在シナリオ接地が条件 |
| 神経 | EpiSTDP (ターン間Hebbian連想) | revise | STR依存。名称のSTDP主張は撤回要 |
| 符号理論 | NEBR (Bloomレジスタ) | revise | プレーン容量2桁不足 + 評価がtrain-test漏洩 |
| 符号理論 | SSD (シンドローム復号ルータ) | revise(実質drop) | 受信語が常に有効符号語でノイズ経路が無い |
| ISA | TµC-152 (マイクロコードISA) | revise(実質drop) | モードFIFOはVertical Stackが上位互換。強度ビットプレーンのみ部品価値 |
| 神経 | HALT-WTA (ホメオスタシス閾値) | 実質drop | 決定性・自動調整禁止・markers-firstと正面衝突 |
| 分散 | MTL (Merkleトレース台帳) | **drop** | ローカルファイルは台帳外で読める。sealed one-shot主張が不成立 |

## 4. 見送り理由の要点 (再挑戦の条件)

- **MTL**: 「読んだ/読んでいない」の第三者検証は、信頼できる外部読取り監視か
  append-onlyの外部ログ無しには暗号学的に不可能。blind評価の割付事前コミット
  だけなら既存のSHA-256 digestパターンで足りる。
- **HALT-WTA**: 判定閾値が判定履歴で動く時点で「同一入力→同一plan」が破れる。
  復活させるならオフライン較正レポート生成器として
  intent-model-deployment-gate.v1の枠 (版管理+人間承認+固定fixture回帰) に載せる。
- **SSD**: marker層と学習層に**独立の完全情報語**を推定させ、2語のXORを
  誤りベクトルとして有効構成辞書への有界距離復号を行う再設計なら成立余地。
  線形符号[64,32]の看板は降ろすこと。
- **NEBR**: プレーンサイズを実測distinct n-gram数から導出し、負例の構築用と
  測定用を非交差分割してから。
- **TµC-152の部品**: 強度ビットプレーン (2bit飽和カウンタ + POPCNT閾値テスト)
  はG1への最小回答として単体で再提案可 (STR実装時の前提部品)。

## 5. 実装済み: 推奨上位2案

### 5.1 SIG-64 Route CAM (route-cam.v1) — adapter v0.3.2

**何か**: semantic packetのenum群をbit0-31に意味的符号化 (one-hot +
温度計符号)、bit32-63に既存hashed n-gram特徴のSimHashを載せた64bit署名
(SIG-64) を作り、don't-careマスク付きTCAM照合
`popcount((SIG XOR value) AND care) <= max_distance` で
人間承認済みエントリを引く。ヒットは**処理クラスの昇格のみ** (PLAN_RANKの
max-join)。降格は構造的に不可能。

**位置**: `adapter.route()` の決定表の**後段**。baseline planが常に下限。
markers-first原則は不変 (packetの抽出には一切触れない)。

**規律との整合**:
- エントリ追加はモデル重みに触れない → G5 (小バッチ再学習の負の結果) への回答
- 1エントリ = 1根拠fixture必須、店舗は凍結JSON + schema_version + load時検証
- intent bits (0-6) は既定don't-care (CAM照合が起きる唯一の場面=marker不発時、
  そのbitはgate落ち学習モデルのtop-1で汚染されるため)。
  `intent_care_override: true` で明示opt-inのみ許可
- 空store (出荷状態) はv0.3.1とbyte同一 (traceにroute_camキーも出ない)
- エントリ上限64 (cap超過はエラー。引き上げはレビュー変更でのみ)

**ファイル**: `semantic_routing/signature.py` / `semantic_routing/route_cam.py` /
`semantic_routing/config/route_cam_v1.json` (空) / `docs/ROUTE_CAM_v0_1_design.md`

**次の運用ステップ (未実施)**:
1. gate直下失敗例 (margin 0.007-0.098のfallback 5/9) と弱カテゴリ
   (temporal 3/6, compound 7/11) から初期エントリを人間が1件ずつ起票
2. エントリごとにheld-out + shadow評価 (エントリのcareが緩いと将来入力を
   shadowするため「副作用ゼロ」を主張しない)
3. 評価はper-channel × per-classのgroup-holdout。k-fold単独判断禁止

### 5.2 TDJ Thought Journal — thought_register v0.1拡張

**何か**: TSRの64bit状態をターン間XORデルタ列として持ち越し、4層×16bitの
多重索引 (鳩の巣原理: 距離3以内なら必ず1ブロック完全一致 → O(1)近傍検索) で
再訪・ループ・継続を純bit演算で検出、通常のレジスタbitとして注入する。

**二系統の比較** (実装上の要点): 再訪・継続は**エンコード直後の状態同士**で
比較 (like-for-like。resolverが足すFINAL_ANSWERと混ぜると距離0再訪が原理的に
不成立)。ループはresolve後の**確定状態のデルタ**で判定 (Action層のみの振動)。

**消費側規則 (批評の必須指摘に対応)** — 注入bitが実際に挙動を変える:
- 再訪 → RETRIEVE_MEMORY → 新モード `recall` (mode_selectorでverifyの**下**、
  buildの上。批評はverify手前を示唆したが、再訪した検証依頼は検証し続ける
  べきというsafety-first原則を優先して逸脱)
- ループ → REPAIR_DRIVE + CONTRADICTION_DETECTED → resolverの新規則
  `loop_repair` がFINAL_ANSWERをclearしASK_QUESTIONをset
- 継続 → CONTINUITY_DRIVE (状態dumpで観測可能)

**後方互換**: `process(text)` はbyte同一 (journal=Noneが既定)。注入bit
(REPAIR_DRIVE等) はencoderが立てないため、新resolver規則も単一ターン経路では
到達不能。CLIは `--session` で複数ターン実行。

**スコープの正直な注記**: v0.1 encoderは8規則のOR組合せしか状態を生成しない
ため、到達可能状態は実質2^8オーダー。再訪検出は「同型入力の再来」に効く段階
であり、汎用的な意味再訪はencoderが豊かになってから。評価主張はこの範囲に限定。

**ファイル**: `thought_register/journal.py` + engine/resolver/mode_selector/
order_builder/demoの結線 / `docs/THOUGHT_JOURNAL_v0_1_design.md`

### 5.3 検証結果

```text
python -m pytest -q  ->  345 passed (回帰0)
  既存320 (うち5件はワークツリーにbuild成果物・pattern_lab.dbが無いことによる
  環境要因の失敗で、本体からのコピーで解消。変更をstashしても同一失敗を確認済)
  新規25 (test_route_cam.py 14 + test_thought_journal.py 11)
```

新規テストの主な固定点: 空CAM storeのbyte同一性 / 昇格のみ (降格不可) /
温度計符号の距離単調性 / intent-care guard / journal無しのtrace同一性 /
鳩の巣距離3保証と距離4の限界 / 再訪→recall / 検証依頼の再訪はverify維持 /
ループ→ASK_QUESTION / ループ警報の自己抑制。

## 6. 次の一手 (優先順)

1. **SIG-64初期エントリ起票** — 収集済みのgate落ち座標から。サンプル収集は
   継続 (レビュー優先度をverify/risk難サンプルに寄せると、role-split真価測定
   セットとCAMエントリ原料の両方に同じ承認作業が効く)
2. **TIC-64の縮退版** — 優先度順列テーブル外部化 + 注入APIのみ (ネスト削除)。
   「encoderが立てないbitを注入してsafe_refusal到達」fixtureが受入ゲート
3. **BSQM** — 票源単位quorumに再設計してからrole-split実験dirで
4. 背骨再学習は引き続き凍結 (大バッチ + 完全文ラベルが揃うまで)
