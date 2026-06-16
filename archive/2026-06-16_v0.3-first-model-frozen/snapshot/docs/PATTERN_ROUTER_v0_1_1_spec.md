# Pattern Router v0.1.1 仕様

更新日: 2026-06-11

## 状態

実装済み。Pattern DBは166件、デプロイモデルは全承認データで学習する。

## 予測契約

- `route`: raw scoreのargmax。ルーター本体の分類結果
- `confidence`: raw scoreへsoftmaxを適用した最大値
- `calibrated_confidence`: 反復stratified k-foldの信頼性表から得る正答率推定
- `effective_route`: 閾値以下のraw routeを安全行動`clarify`へ変更した結果
- `low_confidence`: raw routeからfallbackが発火したことを示す

`route`と`effective_route`を混同しない。fallbackは正解Routeへの訂正ではなく、
回答を保留して聞き返す安全行動である。

## 較正契約

- 5-foldを5回反復し、各予測は当該入力を学習していないモデルで生成する
- 反復点数は独立サンプル数ではない
- 6個の等頻度ビンをPAVAで単調化する
- 各ビンの`max_confidence`を上限境界として検索し、ビン間ギャップを作らない
- 較正精度が0.5未満のビン上端を`decision_threshold`候補とする
- 30 patterns未満では較正とfallbackを無効化する

## 評価契約

必須指標:

- raw accuracy
- Route別precision / recall / F1
- macro-F1
- confusion matrix
- coverage
- selective accuracy
- abstention rate
- effective label accuracy（観測用。安全性の成功率ではない）

`tests/fixtures/pattern_router_cases_v1.json`は25件の回帰fixtureである。
改善過程で参照済みのため、未見性能を推定するfinal testには使用しない。

### fixture改訂履歴

- 2026-06-11 `clarify_target`の文面を改訂（契約変更・人間承認済み）。
  旧:「何を求める問題か確認してください」/ 新:「何を求める問題なのか
  分からないので確認してください」。旧文面は欠落の明示も「質問」も含まず、
  レビュー基準「文面から期待Routeが一意に判断できるか」を満たさない両義文
  だった（verify読みも成立する）。Round 1境界学習でverify側の「確認」例が
  増えた結果この両義性が顕在化し、エポック調整では回復しないことを確認した
  うえで、欠落明示を加えて意図を一意化した。「確認」の多義性チャレンジ自体は
  保持している。回帰契約のケースは一意ラベルで構成するという原則をfixture
  追加時の基準とする。

## 学習データ契約

`curriculum://route-boundaries-v1`の24件は次の対照を持つ。

- explore / respond
- clarify / verify
- explore / build

seedはpending候補を作るだけである。承認は明示的レビュー、モデル更新は
明示的`train`操作でのみ行う。クラウドLLM出力、自動疑似ラベル、却下候補は
学習対象にしない。

## 受け入れ値

2026-06-11モデル:

- sample count: 166
- measurement validation accuracy: 0.866667
- repeated CV accuracy: 0.768675
- decision threshold: 0.195214
- regression raw accuracy: 25/25
- regression effective label accuracy: 23/25
- regression coverage: 0.92
- regression selective accuracy: 1.00
