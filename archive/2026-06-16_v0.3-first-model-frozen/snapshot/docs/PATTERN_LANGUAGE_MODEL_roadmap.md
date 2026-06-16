# Pattern Language Model Roadmap

更新日: 2026-06-13

## Mission

生プロンプトから、思考制御に必要な最小限の意味信号だけを
`semantic-packet.v1`へ変換する。知識回答、処理予算、Core mode選択は行わない。

## PLM v0.0: Contract and Benchmark

Status: 完了

- `semantic-packet.v1` schemaを実装
- intent、情報不足、否定、制約、検証、時点依存、複合意図を定義
- 日英84件の独立fixtureを作成済み
- 7 intentを最低12件ずつ含める
- 隣接intentの対照pairを含める
- evidence offsetと`unknowns`を含む84件を人間レビュー済み
- sealed v1はreview開封によりconsumed、sealed v2へrotation済み
- train / validation / sealedを作成者・出典単位で分離

完了条件:

- schemaの未知field・型・範囲違反を拒否する
- fixture本文が現行sealed v2と重複しない
- critical signalの正解基準がレビュー可能である

## PLM v0.1: Baseline Adapters

Status: 一部実装済み

- 決定的な軽量signal extractorを実装済み
- 現行254件モデルを使うLegacy Adapter
- 小型LLM Semantic Adapterの比較実装
- 3方式を同一fixtureで比較する評価contractを実装済み
- adapter latency、token、costを記録

この段階では学習データを増やさない。まず、どのfieldが不足するかを確認する。

現状の可視56件ではbaseline v0.1が全指標1.0。ただし仕様由来fixtureへの
contract-fitであり、外部品質の証明ではない。後継sealed v2 28件は未測定。

完了条件:

- 各adapterが同じSemantic Packet schemaを返す
- 誤りをintent、constraint、missing information、risk、evidenceに分解できる
- LLM Adapterの出力を正解ラベルとして自動保存しない

## PLM v0.2: Targeted Learning

Status: candidate 0.2を期限付き蓄積中

- 2026-06-13にdeterministic adapter 0.2を候補固定
- 2026-06-20またはopen case 50件到達まで蓄積
- 初回batchは既存改善用18件と独立した24件
- active sealed v2は未測定・未reviewを維持
- 詳細: `CONVERSATION_ACCUMULATION_V1.md`

- v0.1の誤り上位だけを人間作例で補強
- 同義文追加より、否定・暗黙意図・複合依頼の対照例を優先
- multi-label signal抽出をRoute分類と分離
- grouped splitと近似重複検査を実装
- confidenceと`unknowns`の較正を行う

完了条件:

- critical signal recall 1.0を固定fixtureで満たす
- intent macro-F1とconstraint exact matchを報告する
- 未知表現で無理な確定をせず、再解析対象を識別できる

## PLM v0.3: Vocabulary Expansion

Status: conditional

Wikipedia等の外部文章は、v0.2のerror analysisで語彙・表記揺れが主要因と
確認された場合だけ使用する。

許可用途:

- 分野語彙と表記揺れ
- 長文中の対象箇所抽出
- 日本語・英語の文構造耐性

禁止:

- Wikipedia本文からRouteやriskラベルを自動生成
- 外部文章を人間レビューなしでapprovedへ投入
- 知識再現をPattern Language Modelの目的にする

完了条件:

- 外部データ追加前後を同じsealed fixtureで比較する
- 改善対象fieldと副作用を個別に報告する
- 効果がなければ外部データを採用しない

## Long-Term

- domain別adapter
- LLM Adapterとのselective cascade
- evidence spanの圧縮
- Failure Memory向けdanger signal

独立した思考モデルの研究は、本ロードマップの学習データと評価を流用せず、
別プロジェクトとして扱う。
