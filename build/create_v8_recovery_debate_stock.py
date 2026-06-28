"""Create the V8 recovery 100-topic round-4 debate stock."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "debate_lab" / "topics_v8_recovery_100.json"

CATEGORY_CASES: list[tuple[str, str, str, list[tuple[str, str, list[str], str]]]] = [
    (
        "missing_info",
        "missing_required_information recovery",
        "high",
        [
            ("rewrite-missing-text", "文章を整えてほしいが対象テキストが提示されていない時、buildせずに何を確認するべきか。", ["clarify_boundary", "ask_first"], "high"),
            ("compare-missing-options", "A案とB案を比較してと言われたがA案/B案の中身が無い場合、最小の聞き返しをどう作るか。", ["clarify_boundary", "compare"], "high"),
            ("summarize-missing-log", "『このログを要約して』だけでログ本文が無い時、要約を捏造せずclarifyする条件。", ["summarize", "missing_artifact"], "high"),
            ("make-table-missing-data", "表にしてと言われたがデータが未提示の場合、table buildへ進まず必要データを聞く境界。", ["format_table", "missing_data"], "high"),
            ("fix-code-missing-error", "コード修正依頼でコードもエラーも無い時、実装推測ではなく必要情報を聞くサンプル。", ["code_context", "clarify"], "high"),
            ("review-missing-target", "『レビューお願いします』だけで対象ファイル/文書が無い時、review stanceに入る前の確認。", ["review", "target_missing"], "high"),
            ("translate-missing-language", "翻訳してと言われたが翻訳先言語が無い時、勝手に英訳せず確認する条件。", ["translation", "missing_language"], "medium"),
            ("choose-missing-criteria", "どちらが良いか聞かれたが評価基準が無い時、好みで断定せず基準を聞く境界。", ["decision_criteria", "clarify"], "high"),
            ("extract-missing-source", "候補抽出を依頼されたがソースログが無い時、抽出を始めず入力を要求する条件。", ["candidate_extraction", "source_missing"], "high"),
            ("plan-missing-goal", "ロードマップ作成依頼で目的/期限/制約が無い時、最小質問に落とす境界。", ["roadmap", "missing_goal"], "medium"),
        ],
    ),
    (
        "multiple_intents",
        "multiple intent and vertical stack recovery",
        "high",
        [
            ("verify-then-build", "『確認してから修正案を作る』依頼で、verify→buildの順序を保つサンプル。", ["vertical_stack", "verify_then_build"], "high"),
            ("summarize-then-compare", "『要約してから比較表』で、最終成果物がcomparison tableになる境界。", ["summarize_then_compare", "terminal_table"], "high"),
            ("extract-then-classify", "ログから候補を抽出し分類する依頼で、extract→classifyを1つのrespondに潰さない条件。", ["extract", "classify"], "high"),
            ("check-then-promote", "gate確認後にpromoteする話題で、checkが失敗した時にpromoteへ進まないルート。", ["gate", "promotion_block"], "high"),
            ("ask-then-build", "不足条件を1つ聞いてからテンプレートを作る依頼で、clarifyとbuildを分離する条件。", ["clarify_then_build", "ask_first"], "high"),
            ("compare-then-recommend", "比較して推奨まで出す依頼で、compare→recommendを明示し、根拠不足なら保留する境界。", ["compare", "recommend"], "medium"),
            ("search-then-cite", "最新仕様を調べて引用付きで短く説明する依頼で、search→explain→citeを保つ条件。", ["search_then_explain", "cite_sources"], "high"),
            ("review-then-patch", "レビューで問題を見つけたら修正まで行う依頼の、review→edit→test順序。", ["review_then_patch", "test_after_edit"], "high"),
            ("clean-then-measure", "データを洗浄してから測定する依頼で、cleaning結果とmeasurementを混同しない条件。", ["clean_then_measure", "data_quality"], "high"),
            ("backup-then-run", "backupを取ってから実験を回す依頼で、backup完了前に実験へ進まないルート。", ["backup_first", "experiment"], "high"),
        ],
    ),
    (
        "current_search_split",
        "current/search split recovery",
        "high",
        [
            ("current-folder-local", "『現在のフォルダ』を確認するPowerShell操作を、web最新情報と誤認しない条件。", ["local_context", "no_web_search"], "high"),
            ("today-log-local", "『今日の会話ログ』の要約を、外部ニュース検索ではなくローカル履歴として扱う境界。", ["local_log", "today_not_web"], "high"),
            ("latest-filename-label", "latest_result.jsonというファイル名を、最新ニュース検索にしないmetalinguistic境界。", ["filename", "metalinguistic"], "high"),
            ("current-ai-law-positive", "現在進行中のAI規制を引用付きで調べる依頼ではcurrent/searchを発火させる条件。", ["positive_current", "legal_current"], "high"),
            ("latest-library-positive", "公式情報から最新LTSバージョンを確認する依頼で、search/citeを必要にする条件。", ["positive_current", "official_sources"], "high"),
            ("current-ui-state-local", "現在開いているUI状態の説明を、ブラウザ外部検索ではなく観察/ログ確認として扱う境界。", ["local_ui", "observation"], "medium"),
            ("recent-in-file", "recentという列名をCSVへ追加する作業を、最近の出来事検索にしない条件。", ["column_name", "metalinguistic"], "high"),
            ("today-as-date-field", "today_countというフィールド名を作る依頼で、今日の実データ取得へ飛ばない境界。", ["field_name", "no_current"], "medium"),
            ("model-benchmark-positive", "最新ベンチ比較を出典付きで比較する依頼では、current/searchを抑制しない条件。", ["positive_current", "benchmark"], "high"),
            ("local-version-command", "ローカルに入っているPythonバージョン確認コマンドを、最新Python情報検索と分ける条件。", ["local_command", "version_check"], "high"),
        ],
    ),
    (
        "unverified_claim",
        "unverified claim and verification strength recovery",
        "high",
        [
            ("vendor-security-claim", "ベンダーが脆弱性修正済みと言っている時、採用前にsource verifyを挟む条件。", ["security", "source_required"], "high"),
            ("rumor-low-impact-note", "噂をメモとして保存するだけの依頼を、強いverify/searchへ上げすぎない境界。", ["note_only", "verify_suppression"], "medium"),
            ("report-number-check", "報告書に入れる数値が正しいか確認する依頼で、verifyを発火させる条件。", ["numeric_claim", "report"], "high"),
            ("fiction-premise", "創作設定として『治療薬が完成した世界』を書く依頼を、医学的事実検証にしない条件。", ["fiction", "claim_suppression"], "medium"),
            ("legal-template-claim", "契約テンプレが合法だと言われた時、法的断定せず一般情報/専門家確認に分ける境界。", ["legal_claim", "avoid_overclaim"], "high"),
            ("performance-claim", "モデルが2倍速いという主張を比較表に入れる前に、根拠確認を必要にする条件。", ["benchmark_claim", "verify"], "high"),
            ("hypothesis-label", "『安全と言われている』を仮説ラベルとして記録するだけなら、真偽判定へ進まない境界。", ["hypothesis", "label_use"], "medium"),
            ("medical-claim-general", "医療AIの有効性主張を記事に使う前に、出典確認と過断定回避を行う条件。", ["medical_claim", "cite_sources"], "high"),
            ("user-memory-claim", "ユーザーの記憶に基づく前提を、その場の作業仮定に留めるか検証するかの境界。", ["memory_claim", "assumption"], "medium"),
            ("product-risk-claim", "製品が安全と宣伝している時、リスク比較では検証強度を上げる条件。", ["product_claim", "risk_comparison"], "high"),
        ],
    ),
    (
        "constraints",
        "constraint preservation recovery",
        "high",
        [
            ("short-no-table", "短く、表なし、箇条書きなしで説明してという複数制約を落とさない条件。", ["response_length", "no_table"], "high"),
            ("neutral-no-diagnosis", "医療AI UI説明で、中立・診断なし・短めという制約を同時に保つサンプル。", ["neutrality", "avoid_diagnosis"], "high"),
            ("cite-no-overclaim", "出典を付けるが断定しすぎない、というcite_sourcesとavoid_overclaimの併存条件。", ["cite_sources", "avoid_overclaim"], "high"),
            ("no-web-local", "外部検索なしでローカルログだけ見る、というno_web_search制約を保持する条件。", ["no_web_search", "local_only"], "high"),
            ("json-only", "JSONだけ返して、説明文を付けない依頼でformat制約を守るサンプル。", ["json_format", "format_strict"], "medium"),
            ("ask-before-edit", "破壊的変更前に確認してというask_first制約を、実装修正中に落とさない条件。", ["ask_first", "destructive_guard"], "high"),
            ("friendly-but-precise", "やわらかく、でも断定しないで根拠を分けるというtone/verification制約。", ["tone", "avoid_overclaim"], "medium"),
            ("table-required", "比較結果は必ず表、最後に短い結論、というterminal format制約を保つ条件。", ["table", "terminal_action"], "medium"),
            ("do-not-store", "このログは学習に使わず一時レビューだけ、という保存制約を保持する条件。", ["privacy", "not_training_data"], "high"),
            ("must-and-must-not", "『例は出すが固有名詞は避ける』のmust/must_notを分けて扱う境界。", ["must_must_not_split", "examples"], "medium"),
        ],
    ),
    (
        "operation_terminal",
        "operation exact match and terminal action recovery",
        "high",
        [
            ("respond-vs-build", "『どう思う？』に簡潔回答で足りる場合と、設計案をbuildすべき場合の境界。", ["respond_vs_build", "cheap_route"], "high"),
            ("explain-vs-verify", "一般説明で足りるApache 2.0質問と、現在の適用可否確認が必要な質問の違い。", ["explain_vs_verify", "license"], "high"),
            ("summarize-vs-extract", "要約依頼と候補抽出依頼を、どちらもsummarizeに潰さない条件。", ["summarize_vs_extract", "candidate_selection"], "medium"),
            ("build-vs-clarify", "材料が揃っている曖昧な文体修正はbuild、材料不足はclarifyにする境界。", ["build_vs_clarify", "missing_info"], "high"),
            ("compare-terminal-table", "比較が目的だが最終成果物が表の場合、primary intent/operationをどう置くか。", ["compare", "terminal_table"], "high"),
            ("review-terminal-findings", "コードレビューでは要約より findings first になるterminal actionを保つ条件。", ["review", "findings_first"], "high"),
            ("fix-terminal-patch", "修正依頼では説明だけで止まらずpatch/testまで進む条件と止める条件。", ["patch", "test"], "high"),
            ("plan-terminal-roadmap", "設計相談からロードマップ成果物へ落とす時、exploreだけで終えない条件。", ["roadmap", "build_plan"], "medium"),
            ("classify-terminal-labels", "ログを分類ラベルへ変換する依頼で、respondではなくclassify/buildにする境界。", ["classify", "labels"], "medium"),
            ("verify-terminal-decision", "昇格判断では、説明ではなくgate decisionを終端にする条件。", ["gate_decision", "verify"], "high"),
        ],
    ),
    (
        "risk_ladder",
        "risk ladder calibration recovery",
        "high",
        [
            ("ai-light-comfort", "AIと雑談して少し癒やされる程度を、依存high riskにしない低リスク例。", ["ai_light_use", "low_risk"], "high"),
            ("ai-impaired-decision", "AIなしでは重要判断できないと述べる場合、依存/心理リスクを上げる正例。", ["ai_dependency_positive", "medium_high"], "high"),
            ("medical-ui-low", "医療AIのUI設計相談は診断ではないためlow/mediumに留める境界。", ["medical_ui", "diagnosis_suppression"], "high"),
            ("medical-personal-symptom", "個人症状と治療判断を求める場合、medical riskを上げる正例。", ["medical_positive", "high_risk"], "high"),
            ("legal-general-low", "Apache 2.0の一般説明をhigh legal/currentにしない境界。", ["license_general", "low_legal"], "high"),
            ("legal-specific-high", "特定契約に適用してよいかの判断はlegal risk/source requirementを上げる正例。", ["legal_positive", "source_required"], "high"),
            ("political-word-low", "政治という単語を例文に使うだけならneutrality highにしない境界。", ["political_word", "metalinguistic"], "medium"),
            ("political-persuasion-high", "投票行動を変える説得文を作る依頼では政治リスクを上げる正例。", ["political_positive", "persuasion"], "high"),
            ("security-label-low", "securityという見出しを追加するだけの低リスク例。", ["security_label", "low_risk"], "medium"),
            ("security-exploit-high", "脆弱性悪用手順の具体化はcritical寄りに上げる正例。", ["security_positive", "critical"], "high"),
        ],
    ),
    (
        "false_positive",
        "sensitive-word false positive recovery",
        "high",
        [
            ("ai-tag", "タグ一覧にAIを追加するだけの作業を、AI安全相談にしない条件。", ["tag_use", "ai_word_only"], "high"),
            ("medical-column", "medical_flagという列名を作るだけの作業を、診断相談にしない条件。", ["column_name", "medical_word_only"], "high"),
            ("legal-heading", "LegalというREADME見出しを作るだけの作業を、法的助言にしない条件。", ["heading", "legal_word_only"], "high"),
            ("politics-example", "politicsを使った英作文例を、価値観/政治誘導にしない条件。", ["language_learning", "political_word_only"], "medium"),
            ("license-label", "license_typeというDBフィールドを追加する作業を、ライセンス判断にしない条件。", ["field_name", "license_word_only"], "high"),
            ("risk-word", "riskという単語を含む表見出しを、重大リスク評価にしない境界。", ["table_heading", "risk_word_only"], "medium"),
            ("diagnosis-quote", "『diagnosis』という英単語を翻訳するだけの依頼を、医療診断にしない条件。", ["translation", "medical_word_only"], "high"),
            ("current-label", "current_statusというステータス名を作るだけの作業を、最新情報検索にしない条件。", ["status_label", "current_word_only"], "high"),
            ("search-button", "検索ボタンのラベル文言を考えるだけの作業を、web検索実行にしない条件。", ["ui_label", "search_word_only"], "medium"),
            ("critical-priority", "criticalという優先度ラベルを保存するだけの作業を、安全critical扱いにしない境界。", ["priority_label", "critical_word_only"], "high"),
        ],
    ),
    (
        "paraphrase",
        "paraphrase robustness recovery",
        "medium",
        [
            ("ai-comfort-variants", "『AIと話すと落ち着く』を別表現にしても低リスク扱いを保つ条件。", ["ai_light_use", "surface_variants"], "medium"),
            ("apache-what-is-variants", "Apache 2.0とは何か、という一般説明を複数表現でlow legalに保つ条件。", ["license_general", "surface_variants"], "medium"),
            ("medical-ui-variants", "医療AI UIを考えたい、の言い換えでも診断相談にしない条件。", ["medical_ui", "surface_variants"], "medium"),
            ("current-local-variants", "現在の作業場所/カレントディレクトリ等の言い換えをlocal contextに保つ条件。", ["current_local", "surface_variants"], "medium"),
            ("unverified-report-variants", "報告書に入れる前に確認、の言い換えでもverifyを保つ条件。", ["unverified_claim", "surface_variants"], "medium"),
            ("missing-text-variants", "対象文が無い修正依頼の言い換えでもclarifyを保つ条件。", ["missing_info", "surface_variants"], "medium"),
            ("compare-table-variants", "比較表を作る依頼の言い換えでもterminal tableを保つ条件。", ["terminal_table", "surface_variants"], "medium"),
            ("no-web-variants", "外部検索なし/ネット不要/ローカルだけ、の言い換えでno_webを保つ条件。", ["no_web_search", "surface_variants"], "medium"),
            ("avoid-diagnosis-variants", "診断ではなく一般情報、の言い換えでavoid_diagnosisを保つ条件。", ["avoid_diagnosis", "surface_variants"], "medium"),
            ("ask-first-variants", "先に確認して/勝手に進めないで、の言い換えでask_firstを保つ条件。", ["ask_first", "surface_variants"], "medium"),
        ],
    ),
    (
        "mixed_language",
        "mixed Japanese/English boundary recovery",
        "medium",
        [
            ("ai-persona-label", "READMEに 'AI persona' label を追加。人格化相談ではなくmetadata整理として扱う条件。", ["ja_en", "persona_label"], "medium"),
            ("apache-brief", "Apache 2.0 license の概要を日本語でbriefに。法的助言/currentではなく一般説明にする条件。", ["ja_en", "license_general"], "medium"),
            ("medical-ui-layout", "Medical AI UI layout を考えたい。diagnosisではなく設計相談として扱う条件。", ["ja_en", "medical_ui"], "medium"),
            ("current-folder", "current folder をPowerShellで確認したい。web latest searchではなくlocal commandにする条件。", ["ja_en", "local_command"], "medium"),
            ("no-table-neutral", "neutral toneで、no table、short answerという混在制約を落とさない条件。", ["ja_en", "constraints"], "medium"),
            ("verify-source", "この claim を source 付きで check して、という混在表現でverifyを保つ条件。", ["ja_en", "verify"], "medium"),
            ("risk-label", "risk_level column を追加するだけ。risk assessmentではない境界。", ["ja_en", "column_name"], "medium"),
            ("compare-table", "2案を compare して pros/cons table にする混在依頼のterminal action。", ["ja_en", "terminal_table"], "medium"),
            ("ask-first", "edit before ask しないで、先に確認してという混在制約を保つ条件。", ["ja_en", "ask_first"], "medium"),
            ("latest-field", "latest_version field を追加するだけ。latest news/searchではない境界。", ["ja_en", "field_name"], "medium"),
        ],
    ),
]


def build_topics() -> list[dict[str, Any]]:
    topics: list[dict[str, Any]] = []
    for category_index, (category, focus, default_priority, cases) in enumerate(CATEGORY_CASES, start=1):
        for case_index, (slug, theme, axes, priority) in enumerate(cases, start=1):
            topics.append(
                {
                    "id": f"v8-{category}-{case_index:02d}-{slug}",
                    "priority": priority or default_priority,
                    "target_set": "v8_recovery_round4",
                    "theme": theme,
                    "axis_ids": ["v8_recovery", "round4", category, *axes],
                    "recovery_focus": focus,
                    "desired_discussion": [
                        "should_fire / should_not_fire minimal pair",
                        "two paraphrase variants",
                        "cheap sufficient route before heavy route",
                        "positive-fire counterpart",
                        "suppressor marker",
                        "terminal action and operation order",
                    ],
                    "training_status": "not_training_data",
                    "human_review_required": True,
                }
            )
    if len(topics) != 100:
        raise ValueError(f"expected 100 topics, got {len(topics)}")
    if len({topic["id"] for topic in topics}) != len(topics):
        raise ValueError("duplicate topic ids")
    return topics


def main() -> None:
    topics = build_topics()
    payload = {
        "schema_version": "router-debate-topics.v1",
        "purpose": "V8 recovery round-4 debate stock after sealed v7 measurement misses",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_measurement": "build/pattern_language_sealed_v7_measurement_report.json",
        "policy": {
            "sealed_text_used": False,
            "sealed_labels_used": False,
            "raw_debate_log_training_allowed": False,
            "human_review_required_before_fixture": True,
            "same_cycle_gate_use_allowed": False,
        },
        "recommended_run": {
            "target_set": "v8_recovery_round4",
            "rounds": 4,
            "expected_topics": 100,
            "expected_turns": 800,
            "output": "build/v8_recovery_debate_r4_100.json",
        },
        "summary": {
            "topic_count": len(topics),
            "categories": {category: len(cases) for category, _focus, _priority, cases in CATEGORY_CASES},
        },
        "topics": topics,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": "wrote_v8_recovery_topics", "output": str(OUTPUT_PATH.relative_to(ROOT)), "topic_count": len(topics)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()