# Thought Journal v0.1 (TDJ) — ターン間XORデルタと多重索引再訪検出

Status: 実装済み (thought_register拡張、journal=None既定でbyte同一)。
背景と選定経緯は `docs/BIT_SYSTEMS_PROPOSALS_2026-07-02.md` §5.2。

## 1. 目的

TSR v0.1の明記済み限界2つへの最小侵襲の回答:
- 「単一ターンのみ・状態のターン間持続なし」
- 「CONTINUITY_DRIVE / REPAIR_DRIVE / RETRIEVE_MEMORY等がencoderから未使用」

思考状態空間に**ハミング計量**を導入する初めての層。既存の時間方向は
RuntimeCheckpointのSHA-256同一性照合のみで「状態の近さ」の概念が無かった。

## 2. データ構造 (`thought_register/journal.py`)

ターンごとに2系統の64bit語を記録:

```text
encoded[t]   encoder直後 (journal注入・resolve前) — 再訪/継続の比較用
committed[t] resolve後の確定状態                   — デルタ/ループ判定用
delta[t]     committed[t] XOR committed[t-1]       — 可逆 (XOR折り畳みで復元)
index[4]     encoded状態の4層×16bitブロック完全一致ハッシュ表
```

**なぜ2系統か**: resolverはANSWER_POSSIBLE経由でFINAL_ANSWERを足すため、
「今のエンコード状態」と「過去の確定状態」を比較すると距離0の再訪が原理的に
成立しない。比較は常にlike-for-like (encoded同士 / committed同士)。

## 3. 検出 (全て純bit演算)

```text
近傍:   4本の16bitキー表 -> 候補 -> XOR+popcountで距離確定。
        鳩の巣原理: 距離<=3なら必ず1ブロック完全一致 = O(1)・再現率保証。
        距離4以上は近似 (全ブロック不一致なら見えない — テストで境界を固定)。
再訪:   過去のencoded状態と距離0
継続:   (encoded_now XOR encoded_prev) AND 0x00000000FFFFFFFF == 0
        (Drive+Affect層が不変)
ループ: 直近2遷移のdeltaが共に 非0 かつ ACTION_MASK(bits48-63)内
        (文脈が止まったままAction層だけが振動)
```

4層×16bitのレジスタレイアウトと索引分割が一致するのはTSRの意味的設計に
固有の構造的利点 (非意味的なVLTE ThoughtCodeではブロック一致に解釈が無い)。

## 4. フィードバックと消費側 (挙動が実際に変わる)

検出結果は通常のレジスタbitとして注入され (sources付き)、既存パイプラインを
流れる:

| 検出 | 注入bit | 消費側 (新規) | 観測される挙動 |
|------|---------|---------------|----------------|
| 再訪 | RETRIEVE_MEMORY (journal.revisit) | mode_selector新分岐 | mode `recall` + 専用instruction |
| ループ | REPAIR_DRIVE + CONTRADICTION_DETECTED (journal.loop) | resolver新規則 loop_repair | FINAL_ANSWERをclear、ASK_QUESTIONをset |
| 継続 | CONTINUITY_DRIVE (journal.continuity) | (消費側なし・状態dumpで観測) | — |

- `recall` のカスケード位置は **safe_refusal > verify > recall > build > ...**。
  提案批評は「verify手前」を示唆したが、再訪した検証依頼は検証し続けるべき
  (do-no-harm) というsafety-first原則を優先して verify の下に置いた。
  テスト `test_revisited_verification_still_verifies` で固定。
- ループ警報は自己抑制的: 修復bitが確定状態に入ると次遷移がaction-onlyで
  なくなり、警報は再発火しない (テストで固定)。
- 新resolver規則・新モードはencoderが立てないbitのみを条件とするため、
  単一ターン経路 (journal無し) では到達不能 = 既存挙動はbyte同一。

## 5. engine統合

```text
process(user_input, journal=None):
  encode -> [journalあり: feedback注入 + trace "journal_feedback"]
         -> resolve -> select_mode -> build_order
         -> [journalあり: journal.append(encoded, committed)]
```

- journal=None (既定) は従来と同一のtrace列・同一の出力。
- journalは (user_input, journal履歴) の純関数として決定的。
- CLI: `python -m thought_register --session [--json] "turn0" "turn1" ...`
  (--json時は turns[] + journal dump)。

## 6. privacy境界

ジャーナルは64bit語 (encoded/committed/delta) のみを保持。入力文・回答文は
一切保存しない。セッションスコープであり、training corpusへの永続化は
行わない (自動学習禁止invariantの内側)。

## 7. スコープの正直な注記 (v0.1 encoder上の限界)

encoderは8規則のOR組合せしか状態を生成しないため、到達可能状態は実質
2^8オーダー。したがって:
- 再訪検出が効くのは「同型入力の再来」であり、汎用的な意味再訪ではない
- ハミング近傍検索の工学的価値 (O(1)保証) はencoderが豊かになってから立つ
- 評価主張は「到達可能状態数の実測」と「Action層振動の人工再現」に限定する

## 8. テスト (tests/test_thought_journal.py, 11件)

journal無しのtrace同一性 / 空journal初回ターンの判定同一性 / デルタ可逆性 /
鳩の巣距離3保証と距離4限界 / 語の範囲検証 / 再訪→recall /
検証依頼の再訪はverify維持 / ループ→ASK_QUESTION+FINAL_ANSWER clear /
継続→CONTINUITY_DRIVE / ループ警報の自己抑制 / CLI --session JSON。
