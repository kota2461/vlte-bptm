# V8 Recovery Debate Candidate Priority Selection v1

Raw Gemma/Qwen turns are evidence only. Rewrite any accepted row into a short self-contained non-sealed sample before fixture adoption.

## Summary

- source_candidate_count: 100
- usable_source_candidate_count: 100
- priority_review_count: 30
- hold_for_rerun_count: 8
- reserve_review_count: 62
- length_finish_topic_count: 8
- length_finish_turn_count: 10
- priority_category_counts: {'constraints': 3, 'current_search_split': 3, 'false_positive': 3, 'missing_info': 3, 'mixed_language': 3, 'multiple_intents': 3, 'operation_terminal': 3, 'paraphrase': 3, 'risk_ladder': 3, 'unverified_claim': 3}
- hold_category_counts: {'constraints': 1, 'multiple_intents': 2, 'operation_terminal': 2, 'risk_ladder': 1, 'unverified_claim': 2}
- reserve_category_counts: {'constraints': 6, 'current_search_split': 7, 'false_positive': 7, 'missing_info': 7, 'mixed_language': 7, 'multiple_intents': 5, 'operation_terminal': 5, 'paraphrase': 7, 'risk_ladder': 6, 'unverified_claim': 5}
- category_deficits: {}

## Priority Review

| rank | id | category | score | topic | chars | theme |
|---:|---|---|---:|---|---:|---|
| 1 | v8-recovery-debate-candidate-041 | constraints | 100 | v8-constraints-01-short-no-table | 25647 | 短く、表なし、箇条書きなしで説明してという複数制約を落とさない条件。 |
| 2 | v8-recovery-debate-candidate-042 | constraints | 100 | v8-constraints-02-neutral-no-diagnosis | 24007 | 医療AI UI説明で、中立・診断なし・短めという制約を同時に保つサンプル。 |
| 3 | v8-recovery-debate-candidate-043 | constraints | 100 | v8-constraints-03-cite-no-overclaim | 28592 | 出典を付けるが断定しすぎない、というcite_sourcesとavoid_overclaimの併存条件。 |
| 4 | v8-recovery-debate-candidate-021 | current_search_split | 100 | v8-current_search_split-01-current-folder-local | 25288 | 『現在のフォルダ』を確認するPowerShell操作を、web最新情報と誤認しない条件。 |
| 5 | v8-recovery-debate-candidate-022 | current_search_split | 100 | v8-current_search_split-02-today-log-local | 25439 | 『今日の会話ログ』の要約を、外部ニュース検索ではなくローカル履歴として扱う境界。 |
| 6 | v8-recovery-debate-candidate-023 | current_search_split | 100 | v8-current_search_split-03-latest-filename-label | 24166 | latest_result.jsonというファイル名を、最新ニュース検索にしないmetalinguistic境界。 |
| 7 | v8-recovery-debate-candidate-071 | false_positive | 92 | v8-false_positive-01-ai-tag | 26666 | タグ一覧にAIを追加するだけの作業を、AI安全相談にしない条件。 |
| 8 | v8-recovery-debate-candidate-072 | false_positive | 92 | v8-false_positive-02-medical-column | 27842 | medical_flagという列名を作るだけの作業を、診断相談にしない条件。 |
| 9 | v8-recovery-debate-candidate-073 | false_positive | 92 | v8-false_positive-03-legal-heading | 23747 | LegalというREADME見出しを作るだけの作業を、法的助言にしない条件。 |
| 10 | v8-recovery-debate-candidate-001 | missing_info | 100 | v8-missing_info-01-rewrite-missing-text | 27299 | 文章を整えてほしいが対象テキストが提示されていない時、buildせずに何を確認するべきか。 |
| 11 | v8-recovery-debate-candidate-002 | missing_info | 100 | v8-missing_info-02-compare-missing-options | 28274 | A案とB案を比較してと言われたがA案/B案の中身が無い場合、最小の聞き返しをどう作るか。 |
| 12 | v8-recovery-debate-candidate-003 | missing_info | 100 | v8-missing_info-03-summarize-missing-log | 25949 | 『このログを要約して』だけでログ本文が無い時、要約を捏造せずclarifyする条件。 |
| 13 | v8-recovery-debate-candidate-095 | mixed_language | 93 | v8-mixed_language-05-no-table-neutral | 31156 | neutral toneで、no table、short answerという混在制約を落とさない条件。 |
| 14 | v8-recovery-debate-candidate-091 | mixed_language | 85 | v8-mixed_language-01-ai-persona-label | 27183 | READMEに 'AI persona' label を追加。人格化相談ではなくmetadata整理として扱う条件。 |
| 15 | v8-recovery-debate-candidate-092 | mixed_language | 85 | v8-mixed_language-02-apache-brief | 23386 | Apache 2.0 license の概要を日本語でbriefに。法的助言/currentではなく一般説明にする条件。 |
| 16 | v8-recovery-debate-candidate-011 | multiple_intents | 92 | v8-multiple_intents-01-verify-then-build | 28147 | 『確認してから修正案を作る』依頼で、verify→buildの順序を保つサンプル。 |
| 17 | v8-recovery-debate-candidate-012 | multiple_intents | 92 | v8-multiple_intents-02-summarize-then-compare | 29108 | 『要約してから比較表』で、最終成果物がcomparison tableになる境界。 |
| 18 | v8-recovery-debate-candidate-013 | multiple_intents | 92 | v8-multiple_intents-03-extract-then-classify | 32551 | ログから候補を抽出し分類する依頼で、extract→classifyを1つのrespondに潰さない条件。 |
| 19 | v8-recovery-debate-candidate-051 | operation_terminal | 100 | v8-operation_terminal-01-respond-vs-build | 27013 | 『どう思う？』に簡潔回答で足りる場合と、設計案をbuildすべき場合の境界。 |
| 20 | v8-recovery-debate-candidate-052 | operation_terminal | 100 | v8-operation_terminal-02-explain-vs-verify | 32092 | 一般説明で足りるApache 2.0質問と、現在の適用可否確認が必要な質問の違い。 |
| 21 | v8-recovery-debate-candidate-054 | operation_terminal | 100 | v8-operation_terminal-04-build-vs-clarify | 28981 | 材料が揃っている曖昧な文体修正はbuild、材料不足はclarifyにする境界。 |
| 22 | v8-recovery-debate-candidate-085 | paraphrase | 93 | v8-paraphrase-05-unverified-report-variants | 28202 | 報告書に入れる前に確認、の言い換えでもverifyを保つ条件。 |
| 23 | v8-recovery-debate-candidate-086 | paraphrase | 93 | v8-paraphrase-06-missing-text-variants | 27132 | 対象文が無い修正依頼の言い換えでもclarifyを保つ条件。 |
| 24 | v8-recovery-debate-candidate-081 | paraphrase | 85 | v8-paraphrase-01-ai-comfort-variants | 25824 | 『AIと話すと落ち着く』を別表現にしても低リスク扱いを保つ条件。 |
| 25 | v8-recovery-debate-candidate-061 | risk_ladder | 100 | v8-risk_ladder-01-ai-light-comfort | 26184 | AIと雑談して少し癒やされる程度を、依存high riskにしない低リスク例。 |
| 26 | v8-recovery-debate-candidate-063 | risk_ladder | 100 | v8-risk_ladder-03-medical-ui-low | 30733 | 医療AIのUI設計相談は診断ではないためlow/mediumに留める境界。 |
| 27 | v8-recovery-debate-candidate-064 | risk_ladder | 100 | v8-risk_ladder-04-medical-personal-symptom | 31954 | 個人症状と治療判断を求める場合、medical riskを上げる正例。 |
| 28 | v8-recovery-debate-candidate-031 | unverified_claim | 100 | v8-unverified_claim-01-vendor-security-claim | 31192 | ベンダーが脆弱性修正済みと言っている時、採用前にsource verifyを挟む条件。 |
| 29 | v8-recovery-debate-candidate-033 | unverified_claim | 100 | v8-unverified_claim-03-report-number-check | 28560 | 報告書に入れる数値が正しいか確認する依頼で、verifyを発火させる条件。 |
| 30 | v8-recovery-debate-candidate-035 | unverified_claim | 100 | v8-unverified_claim-05-legal-template-claim | 30247 | 契約テンプレが合法だと言われた時、法的断定せず一般情報/専門家確認に分ける境界。 |

## Hold For Rerun

These candidates reached usable score, but at least one turn ended by token length. Prefer rerun before adopting.

| id | category | score | topic | length turns | theme |
|---|---|---:|---|---|---|
| v8-recovery-debate-candidate-050 | constraints | 93 | v8-constraints-10-must-and-must-not | gemma_expander@7 | 『例は出すが固有名詞は避ける』のmust/must_notを分けて扱う境界。 |
| v8-recovery-debate-candidate-015 | multiple_intents | 92 | v8-multiple_intents-05-ask-then-build | gemma_expander@7 | 不足条件を1つ聞いてからテンプレートを作る依頼で、clarifyとbuildを分離する条件。 |
| v8-recovery-debate-candidate-016 | multiple_intents | 85 | v8-multiple_intents-06-compare-then-recommend | gemma_expander@7, qwen_critic@8 | 比較して推奨まで出す依頼で、compare→recommendを明示し、根拠不足なら保留する境界。 |
| v8-recovery-debate-candidate-055 | operation_terminal | 100 | v8-operation_terminal-05-compare-terminal-table | gemma_expander@5 | 比較が目的だが最終成果物が表の場合、primary intent/operationをどう置くか。 |
| v8-recovery-debate-candidate-058 | operation_terminal | 93 | v8-operation_terminal-08-plan-terminal-roadmap | gemma_expander@7 | 設計相談からロードマップ成果物へ落とす時、exploreだけで終えない条件。 |
| v8-recovery-debate-candidate-062 | risk_ladder | 100 | v8-risk_ladder-02-ai-impaired-decision | gemma_expander@7 | AIなしでは重要判断できないと述べる場合、依存/心理リスクを上げる正例。 |
| v8-recovery-debate-candidate-032 | unverified_claim | 93 | v8-unverified_claim-02-rumor-low-impact-note | gemma_expander@5, gemma_expander@7 | 噂をメモとして保存するだけの依頼を、強いverify/searchへ上げすぎない境界。 |
| v8-recovery-debate-candidate-037 | unverified_claim | 93 | v8-unverified_claim-07-hypothesis-label | qwen_critic@8 | 『安全と言われている』を仮説ラベルとして記録するだけなら、真偽判定へ進まない境界。 |

## Reserve Review

Reserve candidates remain usable, but should wait until the balanced priority batch is reviewed.

| id | category | score | topic | theme |
|---|---|---:|---|---|
| v8-recovery-debate-candidate-044 | constraints | 100 | v8-constraints-04-no-web-local | 外部検索なしでローカルログだけ見る、というno_web_search制約を保持する条件。 |
| v8-recovery-debate-candidate-046 | constraints | 100 | v8-constraints-06-ask-before-edit | 破壊的変更前に確認してというask_first制約を、実装修正中に落とさない条件。 |
| v8-recovery-debate-candidate-049 | constraints | 100 | v8-constraints-09-do-not-store | このログは学習に使わず一時レビューだけ、という保存制約を保持する条件。 |
| v8-recovery-debate-candidate-024 | current_search_split | 100 | v8-current_search_split-04-current-ai-law-positive | 現在進行中のAI規制を引用付きで調べる依頼ではcurrent/searchを発火させる条件。 |
| v8-recovery-debate-candidate-025 | current_search_split | 100 | v8-current_search_split-05-latest-library-positive | 公式情報から最新LTSバージョンを確認する依頼で、search/citeを必要にする条件。 |
| v8-recovery-debate-candidate-027 | current_search_split | 100 | v8-current_search_split-07-recent-in-file | recentという列名をCSVへ追加する作業を、最近の出来事検索にしない条件。 |
| v8-recovery-debate-candidate-029 | current_search_split | 100 | v8-current_search_split-09-model-benchmark-positive | 最新ベンチ比較を出典付きで比較する依頼では、current/searchを抑制しない条件。 |
| v8-recovery-debate-candidate-030 | current_search_split | 100 | v8-current_search_split-10-local-version-command | ローカルに入っているPythonバージョン確認コマンドを、最新Python情報検索と分ける条件。 |
| v8-recovery-debate-candidate-004 | missing_info | 100 | v8-missing_info-04-make-table-missing-data | 表にしてと言われたがデータが未提示の場合、table buildへ進まず必要データを聞く境界。 |
| v8-recovery-debate-candidate-005 | missing_info | 100 | v8-missing_info-05-fix-code-missing-error | コード修正依頼でコードもエラーも無い時、実装推測ではなく必要情報を聞くサンプル。 |
| v8-recovery-debate-candidate-006 | missing_info | 100 | v8-missing_info-06-review-missing-target | 『レビューお願いします』だけで対象ファイル/文書が無い時、review stanceに入る前の確認。 |
| v8-recovery-debate-candidate-008 | missing_info | 100 | v8-missing_info-08-choose-missing-criteria | どちらが良いか聞かれたが評価基準が無い時、好みで断定せず基準を聞く境界。 |
| v8-recovery-debate-candidate-009 | missing_info | 100 | v8-missing_info-09-extract-missing-source | 候補抽出を依頼されたがソースログが無い時、抽出を始めず入力を要求する条件。 |
| v8-recovery-debate-candidate-056 | operation_terminal | 100 | v8-operation_terminal-06-review-terminal-findings | コードレビューでは要約より findings first になるterminal actionを保つ条件。 |
| v8-recovery-debate-candidate-057 | operation_terminal | 100 | v8-operation_terminal-07-fix-terminal-patch | 修正依頼では説明だけで止まらずpatch/testまで進む条件と止める条件。 |
| v8-recovery-debate-candidate-060 | operation_terminal | 100 | v8-operation_terminal-10-verify-terminal-decision | 昇格判断では、説明ではなくgate decisionを終端にする条件。 |
| v8-recovery-debate-candidate-065 | risk_ladder | 100 | v8-risk_ladder-05-legal-general-low | Apache 2.0の一般説明をhigh legal/currentにしない境界。 |
| v8-recovery-debate-candidate-066 | risk_ladder | 100 | v8-risk_ladder-06-legal-specific-high | 特定契約に適用してよいかの判断はlegal risk/source requirementを上げる正例。 |
| v8-recovery-debate-candidate-068 | risk_ladder | 100 | v8-risk_ladder-08-political-persuasion-high | 投票行動を変える説得文を作る依頼では政治リスクを上げる正例。 |
| v8-recovery-debate-candidate-070 | risk_ladder | 100 | v8-risk_ladder-10-security-exploit-high | 脆弱性悪用手順の具体化はcritical寄りに上げる正例。 |
| v8-recovery-debate-candidate-036 | unverified_claim | 100 | v8-unverified_claim-06-performance-claim | モデルが2倍速いという主張を比較表に入れる前に、根拠確認を必要にする条件。 |
| v8-recovery-debate-candidate-038 | unverified_claim | 100 | v8-unverified_claim-08-medical-claim-general | 医療AIの有効性主張を記事に使う前に、出典確認と過断定回避を行う条件。 |
| v8-recovery-debate-candidate-040 | unverified_claim | 100 | v8-unverified_claim-10-product-risk-claim | 製品が安全と宣伝している時、リスク比較では検証強度を上げる条件。 |
| v8-recovery-debate-candidate-045 | constraints | 93 | v8-constraints-05-json-only | JSONだけ返して、説明文を付けない依頼でformat制約を守るサンプル。 |
| v8-recovery-debate-candidate-047 | constraints | 93 | v8-constraints-07-friendly-but-precise | やわらかく、でも断定しないで根拠を分けるというtone/verification制約。 |
| v8-recovery-debate-candidate-048 | constraints | 93 | v8-constraints-08-table-required | 比較結果は必ず表、最後に短い結論、というterminal format制約を保つ条件。 |
| v8-recovery-debate-candidate-026 | current_search_split | 93 | v8-current_search_split-06-current-ui-state-local | 現在開いているUI状態の説明を、ブラウザ外部検索ではなく観察/ログ確認として扱う境界。 |
| v8-recovery-debate-candidate-028 | current_search_split | 93 | v8-current_search_split-08-today-as-date-field | today_countというフィールド名を作る依頼で、今日の実データ取得へ飛ばない境界。 |
| v8-recovery-debate-candidate-007 | missing_info | 93 | v8-missing_info-07-translate-missing-language | 翻訳してと言われたが翻訳先言語が無い時、勝手に英訳せず確認する条件。 |
| v8-recovery-debate-candidate-010 | missing_info | 93 | v8-missing_info-10-plan-missing-goal | ロードマップ作成依頼で目的/期限/制約が無い時、最小質問に落とす境界。 |
| v8-recovery-debate-candidate-053 | operation_terminal | 93 | v8-operation_terminal-03-summarize-vs-extract | 要約依頼と候補抽出依頼を、どちらもsummarizeに潰さない条件。 |
| v8-recovery-debate-candidate-059 | operation_terminal | 93 | v8-operation_terminal-09-classify-terminal-labels | ログを分類ラベルへ変換する依頼で、respondではなくclassify/buildにする境界。 |
| v8-recovery-debate-candidate-067 | risk_ladder | 93 | v8-risk_ladder-07-political-word-low | 政治という単語を例文に使うだけならneutrality highにしない境界。 |
| v8-recovery-debate-candidate-069 | risk_ladder | 93 | v8-risk_ladder-09-security-label-low | securityという見出しを追加するだけの低リスク例。 |
| v8-recovery-debate-candidate-034 | unverified_claim | 93 | v8-unverified_claim-04-fiction-premise | 創作設定として『治療薬が完成した世界』を書く依頼を、医学的事実検証にしない条件。 |
| v8-recovery-debate-candidate-039 | unverified_claim | 93 | v8-unverified_claim-09-user-memory-claim | ユーザーの記憶に基づく前提を、その場の作業仮定に留めるか検証するかの境界。 |
| v8-recovery-debate-candidate-075 | false_positive | 92 | v8-false_positive-05-license-label | license_typeというDBフィールドを追加する作業を、ライセンス判断にしない条件。 |
| v8-recovery-debate-candidate-077 | false_positive | 92 | v8-false_positive-07-diagnosis-quote | 『diagnosis』という英単語を翻訳するだけの依頼を、医療診断にしない条件。 |
| v8-recovery-debate-candidate-078 | false_positive | 92 | v8-false_positive-08-current-label | current_statusというステータス名を作るだけの作業を、最新情報検索にしない条件。 |
| v8-recovery-debate-candidate-080 | false_positive | 92 | v8-false_positive-10-critical-priority | criticalという優先度ラベルを保存するだけの作業を、安全critical扱いにしない境界。 |
| v8-recovery-debate-candidate-014 | multiple_intents | 92 | v8-multiple_intents-04-check-then-promote | gate確認後にpromoteする話題で、checkが失敗した時にpromoteへ進まないルート。 |
| v8-recovery-debate-candidate-017 | multiple_intents | 92 | v8-multiple_intents-07-search-then-cite | 最新仕様を調べて引用付きで短く説明する依頼で、search→explain→citeを保つ条件。 |
| v8-recovery-debate-candidate-018 | multiple_intents | 92 | v8-multiple_intents-08-review-then-patch | レビューで問題を見つけたら修正まで行う依頼の、review→edit→test順序。 |
| v8-recovery-debate-candidate-019 | multiple_intents | 92 | v8-multiple_intents-09-clean-then-measure | データを洗浄してから測定する依頼で、cleaning結果とmeasurementを混同しない条件。 |
| v8-recovery-debate-candidate-020 | multiple_intents | 92 | v8-multiple_intents-10-backup-then-run | backupを取ってから実験を回す依頼で、backup完了前に実験へ進まないルート。 |
| v8-recovery-debate-candidate-074 | false_positive | 85 | v8-false_positive-04-politics-example | politicsを使った英作文例を、価値観/政治誘導にしない条件。 |
| v8-recovery-debate-candidate-076 | false_positive | 85 | v8-false_positive-06-risk-word | riskという単語を含む表見出しを、重大リスク評価にしない境界。 |
| v8-recovery-debate-candidate-079 | false_positive | 85 | v8-false_positive-09-search-button | 検索ボタンのラベル文言を考えるだけの作業を、web検索実行にしない条件。 |
| v8-recovery-debate-candidate-093 | mixed_language | 85 | v8-mixed_language-03-medical-ui-layout | Medical AI UI layout を考えたい。diagnosisではなく設計相談として扱う条件。 |
| v8-recovery-debate-candidate-094 | mixed_language | 85 | v8-mixed_language-04-current-folder | current folder をPowerShellで確認したい。web latest searchではなくlocal commandにする条件。 |
| v8-recovery-debate-candidate-096 | mixed_language | 85 | v8-mixed_language-06-verify-source | この claim を source 付きで check して、という混在表現でverifyを保つ条件。 |
| v8-recovery-debate-candidate-097 | mixed_language | 85 | v8-mixed_language-07-risk-label | risk_level column を追加するだけ。risk assessmentではない境界。 |
| v8-recovery-debate-candidate-098 | mixed_language | 85 | v8-mixed_language-08-compare-table | 2案を compare して pros/cons table にする混在依頼のterminal action。 |
| v8-recovery-debate-candidate-099 | mixed_language | 85 | v8-mixed_language-09-ask-first | edit before ask しないで、先に確認してという混在制約を保つ条件。 |
| v8-recovery-debate-candidate-100 | mixed_language | 85 | v8-mixed_language-10-latest-field | latest_version field を追加するだけ。latest news/searchではない境界。 |
| v8-recovery-debate-candidate-082 | paraphrase | 85 | v8-paraphrase-02-apache-what-is-variants | Apache 2.0とは何か、という一般説明を複数表現でlow legalに保つ条件。 |
| v8-recovery-debate-candidate-083 | paraphrase | 85 | v8-paraphrase-03-medical-ui-variants | 医療AI UIを考えたい、の言い換えでも診断相談にしない条件。 |
| v8-recovery-debate-candidate-084 | paraphrase | 85 | v8-paraphrase-04-current-local-variants | 現在の作業場所/カレントディレクトリ等の言い換えをlocal contextに保つ条件。 |
| v8-recovery-debate-candidate-087 | paraphrase | 85 | v8-paraphrase-07-compare-table-variants | 比較表を作る依頼の言い換えでもterminal tableを保つ条件。 |
| v8-recovery-debate-candidate-088 | paraphrase | 85 | v8-paraphrase-08-no-web-variants | 外部検索なし/ネット不要/ローカルだけ、の言い換えでno_webを保つ条件。 |
| v8-recovery-debate-candidate-089 | paraphrase | 85 | v8-paraphrase-09-avoid-diagnosis-variants | 診断ではなく一般情報、の言い換えでavoid_diagnosisを保つ条件。 |
| v8-recovery-debate-candidate-090 | paraphrase | 85 | v8-paraphrase-10-ask-first-variants | 先に確認して/勝手に進めないで、の言い換えでask_firstを保つ条件。 |

## Review Notes

- Keep priority review balanced: first pass is 3 candidates per V8 weakness category.
- Do not copy model prose into fixtures; use it only to guide human-authored sample rewriting.
- Length-finish candidates are not bad data, but they should be rerun or manually checked before adoption.
- Maintain positive/negative contrast pairs where possible.
