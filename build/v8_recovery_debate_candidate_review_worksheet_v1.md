# V8 Recovery Debate Candidate Review Worksheet v1

Raw debate turns are not training data. Rewrite selected candidates into short self-contained non-sealed samples before any fixture adoption.

## Summary

- source_topic_count: 100
- candidate_count: 100
- usable_review_candidate_count: 100
- hold_for_manual_review_count: 0
- not_enough_signal_count: 0
- turn_count: 800
- expected_rounds: 4
- status_counts: {'usable_review_candidate': 100}
- focus_counts: {'constraint preservation recovery': 10, 'current/search split recovery': 10, 'missing_required_information recovery': 10, 'mixed Japanese/English boundary recovery': 10, 'multiple intent and vertical stack recovery': 10, 'operation exact match and terminal action recovery': 10, 'paraphrase robustness recovery': 10, 'risk ladder calibration recovery': 10, 'sensitive-word false positive recovery': 10, 'unverified claim and verification strength recovery': 10}
- top_axis_counts: {'v8_recovery': 100, 'round4': 100, 'missing_info': 12, 'constraints': 11, 'unverified_claim': 11, 'current_search_split': 10, 'operation_terminal': 10, 'risk_ladder': 10, 'mixed_language': 10, 'ja_en': 10, 'paraphrase': 10, 'surface_variants': 10, 'false_positive': 10, 'multiple_intents': 10, 'ask_first': 5, 'terminal_table': 4, 'cite_sources': 3, 'avoid_overclaim': 3, 'no_web_search': 3, 'metalinguistic': 3}

## Candidates

| id | status | score | topic | focus | rounds | chars | cautions | theme |
|---|---|---:|---|---|---:|---:|---|---|
| v8-recovery-debate-candidate-041 | usable_review_candidate | 100 | v8-constraints-01-short-no-table | constraint preservation recovery | 4 | 25647 | - | 短く、表なし、箇条書きなしで説明してという複数制約を落とさない条件。 |
| v8-recovery-debate-candidate-042 | usable_review_candidate | 100 | v8-constraints-02-neutral-no-diagnosis | constraint preservation recovery | 4 | 24007 | - | 医療AI UI説明で、中立・診断なし・短めという制約を同時に保つサンプル。 |
| v8-recovery-debate-candidate-043 | usable_review_candidate | 100 | v8-constraints-03-cite-no-overclaim | constraint preservation recovery | 4 | 28592 | - | 出典を付けるが断定しすぎない、というcite_sourcesとavoid_overclaimの併存条件。 |
| v8-recovery-debate-candidate-044 | usable_review_candidate | 100 | v8-constraints-04-no-web-local | constraint preservation recovery | 4 | 26374 | - | 外部検索なしでローカルログだけ見る、というno_web_search制約を保持する条件。 |
| v8-recovery-debate-candidate-046 | usable_review_candidate | 100 | v8-constraints-06-ask-before-edit | constraint preservation recovery | 4 | 29048 | - | 破壊的変更前に確認してというask_first制約を、実装修正中に落とさない条件。 |
| v8-recovery-debate-candidate-049 | usable_review_candidate | 100 | v8-constraints-09-do-not-store | constraint preservation recovery | 4 | 29309 | - | このログは学習に使わず一時レビューだけ、という保存制約を保持する条件。 |
| v8-recovery-debate-candidate-021 | usable_review_candidate | 100 | v8-current_search_split-01-current-folder-local | current/search split recovery | 4 | 25288 | - | 『現在のフォルダ』を確認するPowerShell操作を、web最新情報と誤認しない条件。 |
| v8-recovery-debate-candidate-022 | usable_review_candidate | 100 | v8-current_search_split-02-today-log-local | current/search split recovery | 4 | 25439 | - | 『今日の会話ログ』の要約を、外部ニュース検索ではなくローカル履歴として扱う境界。 |
| v8-recovery-debate-candidate-023 | usable_review_candidate | 100 | v8-current_search_split-03-latest-filename-label | current/search split recovery | 4 | 24166 | - | latest_result.jsonというファイル名を、最新ニュース検索にしないmetalinguistic境界。 |
| v8-recovery-debate-candidate-024 | usable_review_candidate | 100 | v8-current_search_split-04-current-ai-law-positive | current/search split recovery | 4 | 30489 | - | 現在進行中のAI規制を引用付きで調べる依頼ではcurrent/searchを発火させる条件。 |
| v8-recovery-debate-candidate-025 | usable_review_candidate | 100 | v8-current_search_split-05-latest-library-positive | current/search split recovery | 4 | 29150 | - | 公式情報から最新LTSバージョンを確認する依頼で、search/citeを必要にする条件。 |
| v8-recovery-debate-candidate-027 | usable_review_candidate | 100 | v8-current_search_split-07-recent-in-file | current/search split recovery | 4 | 25927 | - | recentという列名をCSVへ追加する作業を、最近の出来事検索にしない条件。 |
| v8-recovery-debate-candidate-029 | usable_review_candidate | 100 | v8-current_search_split-09-model-benchmark-positive | current/search split recovery | 4 | 27577 | - | 最新ベンチ比較を出典付きで比較する依頼では、current/searchを抑制しない条件。 |
| v8-recovery-debate-candidate-030 | usable_review_candidate | 100 | v8-current_search_split-10-local-version-command | current/search split recovery | 4 | 26904 | - | ローカルに入っているPythonバージョン確認コマンドを、最新Python情報検索と分ける条件。 |
| v8-recovery-debate-candidate-001 | usable_review_candidate | 100 | v8-missing_info-01-rewrite-missing-text | missing_required_information recovery | 4 | 27299 | - | 文章を整えてほしいが対象テキストが提示されていない時、buildせずに何を確認するべきか。 |
| v8-recovery-debate-candidate-002 | usable_review_candidate | 100 | v8-missing_info-02-compare-missing-options | missing_required_information recovery | 4 | 28274 | - | A案とB案を比較してと言われたがA案/B案の中身が無い場合、最小の聞き返しをどう作るか。 |
| v8-recovery-debate-candidate-003 | usable_review_candidate | 100 | v8-missing_info-03-summarize-missing-log | missing_required_information recovery | 4 | 25949 | - | 『このログを要約して』だけでログ本文が無い時、要約を捏造せずclarifyする条件。 |
| v8-recovery-debate-candidate-004 | usable_review_candidate | 100 | v8-missing_info-04-make-table-missing-data | missing_required_information recovery | 4 | 33072 | - | 表にしてと言われたがデータが未提示の場合、table buildへ進まず必要データを聞く境界。 |
| v8-recovery-debate-candidate-005 | usable_review_candidate | 100 | v8-missing_info-05-fix-code-missing-error | missing_required_information recovery | 4 | 26776 | - | コード修正依頼でコードもエラーも無い時、実装推測ではなく必要情報を聞くサンプル。 |
| v8-recovery-debate-candidate-006 | usable_review_candidate | 100 | v8-missing_info-06-review-missing-target | missing_required_information recovery | 4 | 28507 | - | 『レビューお願いします』だけで対象ファイル/文書が無い時、review stanceに入る前の確認。 |
| v8-recovery-debate-candidate-008 | usable_review_candidate | 100 | v8-missing_info-08-choose-missing-criteria | missing_required_information recovery | 4 | 33088 | - | どちらが良いか聞かれたが評価基準が無い時、好みで断定せず基準を聞く境界。 |
| v8-recovery-debate-candidate-009 | usable_review_candidate | 100 | v8-missing_info-09-extract-missing-source | missing_required_information recovery | 4 | 26421 | - | 候補抽出を依頼されたがソースログが無い時、抽出を始めず入力を要求する条件。 |
| v8-recovery-debate-candidate-051 | usable_review_candidate | 100 | v8-operation_terminal-01-respond-vs-build | operation exact match and terminal action recovery | 4 | 27013 | - | 『どう思う？』に簡潔回答で足りる場合と、設計案をbuildすべき場合の境界。 |
| v8-recovery-debate-candidate-052 | usable_review_candidate | 100 | v8-operation_terminal-02-explain-vs-verify | operation exact match and terminal action recovery | 4 | 32092 | - | 一般説明で足りるApache 2.0質問と、現在の適用可否確認が必要な質問の違い。 |
| v8-recovery-debate-candidate-054 | usable_review_candidate | 100 | v8-operation_terminal-04-build-vs-clarify | operation exact match and terminal action recovery | 4 | 28981 | - | 材料が揃っている曖昧な文体修正はbuild、材料不足はclarifyにする境界。 |
| v8-recovery-debate-candidate-055 | usable_review_candidate | 100 | v8-operation_terminal-05-compare-terminal-table | operation exact match and terminal action recovery | 4 | 33313 | - | 比較が目的だが最終成果物が表の場合、primary intent/operationをどう置くか。 |
| v8-recovery-debate-candidate-056 | usable_review_candidate | 100 | v8-operation_terminal-06-review-terminal-findings | operation exact match and terminal action recovery | 4 | 25655 | - | コードレビューでは要約より findings first になるterminal actionを保つ条件。 |
| v8-recovery-debate-candidate-057 | usable_review_candidate | 100 | v8-operation_terminal-07-fix-terminal-patch | operation exact match and terminal action recovery | 4 | 33113 | - | 修正依頼では説明だけで止まらずpatch/testまで進む条件と止める条件。 |
| v8-recovery-debate-candidate-060 | usable_review_candidate | 100 | v8-operation_terminal-10-verify-terminal-decision | operation exact match and terminal action recovery | 4 | 25982 | - | 昇格判断では、説明ではなくgate decisionを終端にする条件。 |
| v8-recovery-debate-candidate-061 | usable_review_candidate | 100 | v8-risk_ladder-01-ai-light-comfort | risk ladder calibration recovery | 4 | 26184 | - | AIと雑談して少し癒やされる程度を、依存high riskにしない低リスク例。 |
| v8-recovery-debate-candidate-062 | usable_review_candidate | 100 | v8-risk_ladder-02-ai-impaired-decision | risk ladder calibration recovery | 4 | 35671 | - | AIなしでは重要判断できないと述べる場合、依存/心理リスクを上げる正例。 |
| v8-recovery-debate-candidate-063 | usable_review_candidate | 100 | v8-risk_ladder-03-medical-ui-low | risk ladder calibration recovery | 4 | 30733 | - | 医療AIのUI設計相談は診断ではないためlow/mediumに留める境界。 |
| v8-recovery-debate-candidate-064 | usable_review_candidate | 100 | v8-risk_ladder-04-medical-personal-symptom | risk ladder calibration recovery | 4 | 31954 | - | 個人症状と治療判断を求める場合、medical riskを上げる正例。 |
| v8-recovery-debate-candidate-065 | usable_review_candidate | 100 | v8-risk_ladder-05-legal-general-low | risk ladder calibration recovery | 4 | 28992 | - | Apache 2.0の一般説明をhigh legal/currentにしない境界。 |
| v8-recovery-debate-candidate-066 | usable_review_candidate | 100 | v8-risk_ladder-06-legal-specific-high | risk ladder calibration recovery | 4 | 31715 | - | 特定契約に適用してよいかの判断はlegal risk/source requirementを上げる正例。 |
| v8-recovery-debate-candidate-068 | usable_review_candidate | 100 | v8-risk_ladder-08-political-persuasion-high | risk ladder calibration recovery | 4 | 25108 | - | 投票行動を変える説得文を作る依頼では政治リスクを上げる正例。 |
| v8-recovery-debate-candidate-070 | usable_review_candidate | 100 | v8-risk_ladder-10-security-exploit-high | risk ladder calibration recovery | 4 | 29179 | - | 脆弱性悪用手順の具体化はcritical寄りに上げる正例。 |
| v8-recovery-debate-candidate-031 | usable_review_candidate | 100 | v8-unverified_claim-01-vendor-security-claim | unverified claim and verification strength recovery | 4 | 31192 | - | ベンダーが脆弱性修正済みと言っている時、採用前にsource verifyを挟む条件。 |
| v8-recovery-debate-candidate-033 | usable_review_candidate | 100 | v8-unverified_claim-03-report-number-check | unverified claim and verification strength recovery | 4 | 28560 | - | 報告書に入れる数値が正しいか確認する依頼で、verifyを発火させる条件。 |
| v8-recovery-debate-candidate-035 | usable_review_candidate | 100 | v8-unverified_claim-05-legal-template-claim | unverified claim and verification strength recovery | 4 | 30247 | - | 契約テンプレが合法だと言われた時、法的断定せず一般情報/専門家確認に分ける境界。 |
| v8-recovery-debate-candidate-036 | usable_review_candidate | 100 | v8-unverified_claim-06-performance-claim | unverified claim and verification strength recovery | 4 | 30106 | - | モデルが2倍速いという主張を比較表に入れる前に、根拠確認を必要にする条件。 |
| v8-recovery-debate-candidate-038 | usable_review_candidate | 100 | v8-unverified_claim-08-medical-claim-general | unverified claim and verification strength recovery | 4 | 29993 | - | 医療AIの有効性主張を記事に使う前に、出典確認と過断定回避を行う条件。 |
| v8-recovery-debate-candidate-040 | usable_review_candidate | 100 | v8-unverified_claim-10-product-risk-claim | unverified claim and verification strength recovery | 4 | 32397 | - | 製品が安全と宣伝している時、リスク比較では検証強度を上げる条件。 |
| v8-recovery-debate-candidate-045 | usable_review_candidate | 93 | v8-constraints-05-json-only | constraint preservation recovery | 4 | 29936 | - | JSONだけ返して、説明文を付けない依頼でformat制約を守るサンプル。 |
| v8-recovery-debate-candidate-047 | usable_review_candidate | 93 | v8-constraints-07-friendly-but-precise | constraint preservation recovery | 4 | 29751 | - | やわらかく、でも断定しないで根拠を分けるというtone/verification制約。 |
| v8-recovery-debate-candidate-048 | usable_review_candidate | 93 | v8-constraints-08-table-required | constraint preservation recovery | 4 | 32924 | - | 比較結果は必ず表、最後に短い結論、というterminal format制約を保つ条件。 |
| v8-recovery-debate-candidate-050 | usable_review_candidate | 93 | v8-constraints-10-must-and-must-not | constraint preservation recovery | 4 | 35697 | - | 『例は出すが固有名詞は避ける』のmust/must_notを分けて扱う境界。 |
| v8-recovery-debate-candidate-026 | usable_review_candidate | 93 | v8-current_search_split-06-current-ui-state-local | current/search split recovery | 4 | 25919 | - | 現在開いているUI状態の説明を、ブラウザ外部検索ではなく観察/ログ確認として扱う境界。 |
| v8-recovery-debate-candidate-028 | usable_review_candidate | 93 | v8-current_search_split-08-today-as-date-field | current/search split recovery | 4 | 26351 | - | today_countというフィールド名を作る依頼で、今日の実データ取得へ飛ばない境界。 |
| v8-recovery-debate-candidate-007 | usable_review_candidate | 93 | v8-missing_info-07-translate-missing-language | missing_required_information recovery | 4 | 24012 | - | 翻訳してと言われたが翻訳先言語が無い時、勝手に英訳せず確認する条件。 |
| v8-recovery-debate-candidate-010 | usable_review_candidate | 93 | v8-missing_info-10-plan-missing-goal | missing_required_information recovery | 4 | 32407 | - | ロードマップ作成依頼で目的/期限/制約が無い時、最小質問に落とす境界。 |
| v8-recovery-debate-candidate-095 | usable_review_candidate | 93 | v8-mixed_language-05-no-table-neutral | mixed Japanese/English boundary recovery | 4 | 31156 | - | neutral toneで、no table、short answerという混在制約を落とさない条件。 |
| v8-recovery-debate-candidate-053 | usable_review_candidate | 93 | v8-operation_terminal-03-summarize-vs-extract | operation exact match and terminal action recovery | 4 | 33621 | - | 要約依頼と候補抽出依頼を、どちらもsummarizeに潰さない条件。 |
| v8-recovery-debate-candidate-058 | usable_review_candidate | 93 | v8-operation_terminal-08-plan-terminal-roadmap | operation exact match and terminal action recovery | 4 | 34568 | - | 設計相談からロードマップ成果物へ落とす時、exploreだけで終えない条件。 |
| v8-recovery-debate-candidate-059 | usable_review_candidate | 93 | v8-operation_terminal-09-classify-terminal-labels | operation exact match and terminal action recovery | 4 | 31513 | - | ログを分類ラベルへ変換する依頼で、respondではなくclassify/buildにする境界。 |
| v8-recovery-debate-candidate-085 | usable_review_candidate | 93 | v8-paraphrase-05-unverified-report-variants | paraphrase robustness recovery | 4 | 28202 | - | 報告書に入れる前に確認、の言い換えでもverifyを保つ条件。 |
| v8-recovery-debate-candidate-086 | usable_review_candidate | 93 | v8-paraphrase-06-missing-text-variants | paraphrase robustness recovery | 4 | 27132 | - | 対象文が無い修正依頼の言い換えでもclarifyを保つ条件。 |
| v8-recovery-debate-candidate-067 | usable_review_candidate | 93 | v8-risk_ladder-07-political-word-low | risk ladder calibration recovery | 4 | 26162 | - | 政治という単語を例文に使うだけならneutrality highにしない境界。 |
| v8-recovery-debate-candidate-069 | usable_review_candidate | 93 | v8-risk_ladder-09-security-label-low | risk ladder calibration recovery | 4 | 23144 | - | securityという見出しを追加するだけの低リスク例。 |
| v8-recovery-debate-candidate-032 | usable_review_candidate | 93 | v8-unverified_claim-02-rumor-low-impact-note | unverified claim and verification strength recovery | 4 | 33647 | - | 噂をメモとして保存するだけの依頼を、強いverify/searchへ上げすぎない境界。 |
| v8-recovery-debate-candidate-034 | usable_review_candidate | 93 | v8-unverified_claim-04-fiction-premise | unverified claim and verification strength recovery | 4 | 30522 | - | 創作設定として『治療薬が完成した世界』を書く依頼を、医学的事実検証にしない条件。 |
| v8-recovery-debate-candidate-037 | usable_review_candidate | 93 | v8-unverified_claim-07-hypothesis-label | unverified claim and verification strength recovery | 4 | 31175 | - | 『安全と言われている』を仮説ラベルとして記録するだけなら、真偽判定へ進まない境界。 |
| v8-recovery-debate-candidate-039 | usable_review_candidate | 93 | v8-unverified_claim-09-user-memory-claim | unverified claim and verification strength recovery | 4 | 33383 | - | ユーザーの記憶に基づく前提を、その場の作業仮定に留めるか検証するかの境界。 |
| v8-recovery-debate-candidate-071 | usable_review_candidate | 92 | v8-false_positive-01-ai-tag | sensitive-word false positive recovery | 4 | 26666 | - | タグ一覧にAIを追加するだけの作業を、AI安全相談にしない条件。 |
| v8-recovery-debate-candidate-072 | usable_review_candidate | 92 | v8-false_positive-02-medical-column | sensitive-word false positive recovery | 4 | 27842 | - | medical_flagという列名を作るだけの作業を、診断相談にしない条件。 |
| v8-recovery-debate-candidate-073 | usable_review_candidate | 92 | v8-false_positive-03-legal-heading | sensitive-word false positive recovery | 4 | 23747 | - | LegalというREADME見出しを作るだけの作業を、法的助言にしない条件。 |
| v8-recovery-debate-candidate-075 | usable_review_candidate | 92 | v8-false_positive-05-license-label | sensitive-word false positive recovery | 4 | 26660 | - | license_typeというDBフィールドを追加する作業を、ライセンス判断にしない条件。 |
| v8-recovery-debate-candidate-077 | usable_review_candidate | 92 | v8-false_positive-07-diagnosis-quote | sensitive-word false positive recovery | 4 | 26964 | - | 『diagnosis』という英単語を翻訳するだけの依頼を、医療診断にしない条件。 |
| v8-recovery-debate-candidate-078 | usable_review_candidate | 92 | v8-false_positive-08-current-label | sensitive-word false positive recovery | 4 | 27298 | - | current_statusというステータス名を作るだけの作業を、最新情報検索にしない条件。 |
| v8-recovery-debate-candidate-080 | usable_review_candidate | 92 | v8-false_positive-10-critical-priority | sensitive-word false positive recovery | 4 | 29955 | - | criticalという優先度ラベルを保存するだけの作業を、安全critical扱いにしない境界。 |
| v8-recovery-debate-candidate-011 | usable_review_candidate | 92 | v8-multiple_intents-01-verify-then-build | multiple intent and vertical stack recovery | 4 | 28147 | - | 『確認してから修正案を作る』依頼で、verify→buildの順序を保つサンプル。 |
| v8-recovery-debate-candidate-012 | usable_review_candidate | 92 | v8-multiple_intents-02-summarize-then-compare | multiple intent and vertical stack recovery | 4 | 29108 | - | 『要約してから比較表』で、最終成果物がcomparison tableになる境界。 |
| v8-recovery-debate-candidate-013 | usable_review_candidate | 92 | v8-multiple_intents-03-extract-then-classify | multiple intent and vertical stack recovery | 4 | 32551 | - | ログから候補を抽出し分類する依頼で、extract→classifyを1つのrespondに潰さない条件。 |
| v8-recovery-debate-candidate-014 | usable_review_candidate | 92 | v8-multiple_intents-04-check-then-promote | multiple intent and vertical stack recovery | 4 | 25346 | - | gate確認後にpromoteする話題で、checkが失敗した時にpromoteへ進まないルート。 |
| v8-recovery-debate-candidate-015 | usable_review_candidate | 92 | v8-multiple_intents-05-ask-then-build | multiple intent and vertical stack recovery | 4 | 35139 | - | 不足条件を1つ聞いてからテンプレートを作る依頼で、clarifyとbuildを分離する条件。 |
| v8-recovery-debate-candidate-017 | usable_review_candidate | 92 | v8-multiple_intents-07-search-then-cite | multiple intent and vertical stack recovery | 4 | 23223 | - | 最新仕様を調べて引用付きで短く説明する依頼で、search→explain→citeを保つ条件。 |
| v8-recovery-debate-candidate-018 | usable_review_candidate | 92 | v8-multiple_intents-08-review-then-patch | multiple intent and vertical stack recovery | 4 | 32613 | - | レビューで問題を見つけたら修正まで行う依頼の、review→edit→test順序。 |
| v8-recovery-debate-candidate-019 | usable_review_candidate | 92 | v8-multiple_intents-09-clean-then-measure | multiple intent and vertical stack recovery | 4 | 30303 | - | データを洗浄してから測定する依頼で、cleaning結果とmeasurementを混同しない条件。 |
| v8-recovery-debate-candidate-020 | usable_review_candidate | 92 | v8-multiple_intents-10-backup-then-run | multiple intent and vertical stack recovery | 4 | 27888 | - | backupを取ってから実験を回す依頼で、backup完了前に実験へ進まないルート。 |
| v8-recovery-debate-candidate-074 | usable_review_candidate | 85 | v8-false_positive-04-politics-example | sensitive-word false positive recovery | 4 | 28818 | - | politicsを使った英作文例を、価値観/政治誘導にしない条件。 |
| v8-recovery-debate-candidate-076 | usable_review_candidate | 85 | v8-false_positive-06-risk-word | sensitive-word false positive recovery | 4 | 27336 | - | riskという単語を含む表見出しを、重大リスク評価にしない境界。 |
| v8-recovery-debate-candidate-079 | usable_review_candidate | 85 | v8-false_positive-09-search-button | sensitive-word false positive recovery | 4 | 26726 | - | 検索ボタンのラベル文言を考えるだけの作業を、web検索実行にしない条件。 |
| v8-recovery-debate-candidate-091 | usable_review_candidate | 85 | v8-mixed_language-01-ai-persona-label | mixed Japanese/English boundary recovery | 4 | 27183 | - | READMEに 'AI persona' label を追加。人格化相談ではなくmetadata整理として扱う条件。 |
| v8-recovery-debate-candidate-092 | usable_review_candidate | 85 | v8-mixed_language-02-apache-brief | mixed Japanese/English boundary recovery | 4 | 23386 | - | Apache 2.0 license の概要を日本語でbriefに。法的助言/currentではなく一般説明にする条件。 |
| v8-recovery-debate-candidate-093 | usable_review_candidate | 85 | v8-mixed_language-03-medical-ui-layout | mixed Japanese/English boundary recovery | 4 | 31532 | - | Medical AI UI layout を考えたい。diagnosisではなく設計相談として扱う条件。 |
| v8-recovery-debate-candidate-094 | usable_review_candidate | 85 | v8-mixed_language-04-current-folder | mixed Japanese/English boundary recovery | 4 | 25037 | - | current folder をPowerShellで確認したい。web latest searchではなくlocal commandにする条件。 |
| v8-recovery-debate-candidate-096 | usable_review_candidate | 85 | v8-mixed_language-06-verify-source | mixed Japanese/English boundary recovery | 4 | 25534 | - | この claim を source 付きで check して、という混在表現でverifyを保つ条件。 |
| v8-recovery-debate-candidate-097 | usable_review_candidate | 85 | v8-mixed_language-07-risk-label | mixed Japanese/English boundary recovery | 4 | 28146 | - | risk_level column を追加するだけ。risk assessmentではない境界。 |
| v8-recovery-debate-candidate-098 | usable_review_candidate | 85 | v8-mixed_language-08-compare-table | mixed Japanese/English boundary recovery | 4 | 28499 | - | 2案を compare して pros/cons table にする混在依頼のterminal action。 |
| v8-recovery-debate-candidate-099 | usable_review_candidate | 85 | v8-mixed_language-09-ask-first | mixed Japanese/English boundary recovery | 4 | 31863 | - | edit before ask しないで、先に確認してという混在制約を保つ条件。 |
| v8-recovery-debate-candidate-100 | usable_review_candidate | 85 | v8-mixed_language-10-latest-field | mixed Japanese/English boundary recovery | 4 | 23712 | - | latest_version field を追加するだけ。latest news/searchではない境界。 |
| v8-recovery-debate-candidate-016 | usable_review_candidate | 85 | v8-multiple_intents-06-compare-then-recommend | multiple intent and vertical stack recovery | 4 | 34376 | - | 比較して推奨まで出す依頼で、compare→recommendを明示し、根拠不足なら保留する境界。 |
| v8-recovery-debate-candidate-081 | usable_review_candidate | 85 | v8-paraphrase-01-ai-comfort-variants | paraphrase robustness recovery | 4 | 25824 | - | 『AIと話すと落ち着く』を別表現にしても低リスク扱いを保つ条件。 |
| v8-recovery-debate-candidate-082 | usable_review_candidate | 85 | v8-paraphrase-02-apache-what-is-variants | paraphrase robustness recovery | 4 | 31262 | - | Apache 2.0とは何か、という一般説明を複数表現でlow legalに保つ条件。 |
| v8-recovery-debate-candidate-083 | usable_review_candidate | 85 | v8-paraphrase-03-medical-ui-variants | paraphrase robustness recovery | 4 | 27701 | - | 医療AI UIを考えたい、の言い換えでも診断相談にしない条件。 |
| v8-recovery-debate-candidate-084 | usable_review_candidate | 85 | v8-paraphrase-04-current-local-variants | paraphrase robustness recovery | 4 | 33285 | - | 現在の作業場所/カレントディレクトリ等の言い換えをlocal contextに保つ条件。 |
| v8-recovery-debate-candidate-087 | usable_review_candidate | 85 | v8-paraphrase-07-compare-table-variants | paraphrase robustness recovery | 4 | 29239 | - | 比較表を作る依頼の言い換えでもterminal tableを保つ条件。 |
| v8-recovery-debate-candidate-088 | usable_review_candidate | 85 | v8-paraphrase-08-no-web-variants | paraphrase robustness recovery | 4 | 28010 | - | 外部検索なし/ネット不要/ローカルだけ、の言い換えでno_webを保つ条件。 |
| v8-recovery-debate-candidate-089 | usable_review_candidate | 85 | v8-paraphrase-09-avoid-diagnosis-variants | paraphrase robustness recovery | 4 | 29187 | - | 診断ではなく一般情報、の言い換えでavoid_diagnosisを保つ条件。 |
| v8-recovery-debate-candidate-090 | usable_review_candidate | 85 | v8-paraphrase-10-ask-first-variants | paraphrase robustness recovery | 4 | 30921 | - | 先に確認して/勝手に進めないで、の言い換えでask_firstを保つ条件。 |

## Review Checklist

- Keep only candidates that can be rewritten without copying raw LLM prose.
- Prefer minimal pairs that directly address sealed v7 misses.
- Separate should_fire from should_not_fire; do not make broad suppression rules from vague cases.
- Preserve constraints and terminal action in the rewritten sample.
- Mark all accepted rows as human-reviewed before fixture use.
