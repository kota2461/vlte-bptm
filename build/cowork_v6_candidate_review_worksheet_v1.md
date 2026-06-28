# Cowork V6 Candidate Review Worksheet

Source: `C:\Users\kota\Downloads\cowork_raw_logs.txt`

Policy: raw logs are candidate material only. Redacted items require human review before any training/adoption. Sealed text was not used.

## Summary

- raw user messages: 59
- adopt_nonsealed: 25
- rewrite_before_use: 15
- reject: 19
- usable_total: 40

## Adopt Nonsealed Candidates

| ID | Priority | Axes | Suggested Intent | Redacted Input |
|---|---|---|---|---|
| cowork-v6-009 | high | compound_intent, processing_plan, separate_pass | build | 構成はpassですが、処理としてはチャットの処理出力が終るのをきっかけにpassが稼働する仕組みにしてもらえると負担が下がります。ログが混ざらない、処理も分ける事で思考力の低下を抑える仕組みです。 |
| cowork-v6-010 | high | compound_intent, processing_plan, separate_pass | build | 構成は2passですが、処理としてはチャット層の出力が終るのをきっかけに2pass目が稼働する仕組みにしてもらえると負担が下がります。ログが混ざらない、処理も分ける事で思考力の低下を抑える仕組みです。 |
| cowork-v6-015 | high | compound_intent, emotion_dynamics, parameter_tuning | build | ちょっとログがどこに行ったか分からなくなってしまったのですが… emotに対する動的変化として、現在有る時間経過からの感情変化。以外で感情への刺激になりそうな変化を取り入れる。という物です！あと、現在の寂しいの数値は早く上がりすぎるので、実装時は調整を入... |
| cowork-v6-018 | high | summarize_to_memo, prioritization, handoff | summarize | 明日code側を始める際にPhase 5 を待たずに今すぐ着手できる 3 つをメモとして渡したいです！ |
| cowork-v6-020 | high | periodic_review, automation, log_accumulation | build | dataの蓄積に当たってなのですが、定期的にログを確認してもらい、調整をしてもらうことはかのうでしょうか |
| cowork-v6-021 | medium | scheduling_constraint, missing_runtime_window | clarify | PC立ち上げ時出ないとログ確認できないのでその時にお願いしたいです！ |
| cowork-v6-027 | high | brainstorm, multi_option, architecture | explore | まず考えてるのは 1、ペルソナcard、保存すべき基礎的情報を保持。呼び名や性格、優先事項など。 2、脳ノイズの再現、並列処理から、ノイズを抽出しemotionに返す仕組み。 3、ゲームエンジンの採用、並列処理、拡張、AI自身に仮想空間を持たせられる。 |
| cowork-v6-028 | medium | explore_rationale, game_engine_architecture | respond | そのままその通りですね！人間も脳内で一旦仮想空間に現実を反映させてるという説もありますし、ゲームエンジンを採用する事で色々とメリットがあるのではないか？と思いました。 |
| cowork-v6-029 | high | clarify_or_explore, engine_choice, constraint_lightweight | explore | 常駐を目指すなら軽量なエンジンが良いんでしょうか？ |
| cowork-v6-030 | high | compare_options, language_stack, external_integration | explore | 外枠はpython以外もアリだと思ってます、外の接続をする、拡張性、を考えて、C#、rust、goなんかもアリだと |
| cowork-v6-031 | high | memory_persona, update_policy, vectorization | build | そうですね！ペルソナcardは基本を最初に書いておいて、AIが追記、書き換えを行える仕組みが良いとおもいます。書き換えの際は、プロンプトの重要度で触る際簡単に変更しない様に指示。みたいな構造です。出来ればベクトル化が理想です。 |
| cowork-v6-033 | medium | constraints, persona_policy, priority_high | respond | そこは重要ですね。「迎合しない」「本音を言う」は重要度HIGH候補ですね。 |
| cowork-v6-035 | high | compare_options, knowledge_source, llm_vs_chromadb | explore | あと一つ懸念というか、LLMは知識の塊なので、自然な会話になります。CPU先行のこの構造で基礎知識をどう取り入れるか？と考えてました。LLMを基礎知識として使って良いのか？それとも時間がかかるので、専用ChromaDBを置くのか？と |
| cowork-v6-037 | medium | naming_request, creative_build | build | 後で自然に決まりますが、名前があるとブレにくくなるので一つ命名をお願いしたいです！ |
| cowork-v6-039 | high | docs_update, future_roadmap, phase_boundary | build | 現状テストを繰り返して蓄積するphaseなので、すべてのphaseが終った後に始める構想としてdocsに残していきたいです！ |
| cowork-v6-043 | high | debug_error, missing_file, path_context | verify | (.venv) PS <PATH> python main.py can't open file '<PATH> [Errno 2] No such file or directoryエラーです！ |
| cowork-v6-045 | high | debug_error, missing_dependency | verify | Traceback (most recent call last): ... ModuleNotFoundError: No module named 'sqlalchemy' |
| cowork-v6-048 | high | explain_term, tool_concept, after_success_question | explain | 起動できました！サブグラフと言うのは外部のものだったりしますか |
| cowork-v6-049 | high | debug_error, security_policy, custom_node_install | verify | ComfyUI-HunyuanVideo-Foleyこのモデルだけエラーになります [Installation Errors] 'ComfyUI-HunyuanVideo-Foley': With the current security level c... |
| cowork-v6-052 | high | prioritize, write_md, improvement_plan | build | 優先度高から修正案として.mdにまとめて頂きたいです |
| cowork-v6-053 | high | evaluate_draft, skill_review, uncertainty | verify | [Trace Rule v0.1 skill fileアップロード] ちなみに、これの草案としてskillにしたものなのですが、どのくらいの効果が見込めるとか分かりますか |
| cowork-v6-054 | high | compare_design, topic_filter, memory_reference | explore | これ、逆に、話題の混濁だけ焦点に当てて、レベル1とレベル2だけを実装して、レベル1、レベル2が違う話題は参照トークンとして使わないとかだったらどう？ |
| cowork-v6-055 | high | build_rule, multi_tag, topic_list | build | level2に複数の項目(2～3)を付けられるようにして、level１のみトピックスの一覧を作るのはどうでしょう。 |
| cowork-v6-056 | high | design_decision, or_logic, recall_priority | respond | or の条件にすることで、拾いこぼしが無くなるのでそちらです！level1で大枠が決まるのでlevel２で厳密にすると同じ話題の拾いこぼしになりそうなので |
| cowork-v6-057 | high | write_skill_file, versioned_spec | build | v0.2としてスキルファイルに指定だだきたいです！ |

## Rewrite Before Use

| ID | Priority | Axes | Suggested Intent | Redacted Input |
|---|---|---|---|---|
| cowork-v6-002 | medium | debug_error, encoding_error, current_tooling | verify | S <PATH> State Register> powershell -ExecutionPolicy Bypass -File .\git_publish_setup.ps1 発生場所 <PATH> State Register\git_publis... |
| cowork-v6-003 | medium | debug_error, missing_tool, current_tooling | verify | Local repo is ready. Next: create the GitHub repo and push - see SETUP_GITHUB.md PS <PATH> State Register> gh auth login gh : 用... |
| cowork-v6-004 | medium | debug_error, git_remote, current_tooling | verify | PS <PATH> State Register> cd "<PATH> State Register" PS <PATH> State Register> git remote add origin <URL> error: remote origin... |
| cowork-v6-007 | low | context_dependent_build | respond | true変更お願いします！ |
| cowork-v6-008 | medium | long_log_review, feedback_triage, git_publish | respond | 走りました！ありがとうございました！あまり期待はできませんが、採用できるフィードバックがあればありがたいですね。 PS <PATH> cd "<PATH> State Register" PS <PATH> State Register> git add... |
| cowork-v6-011 | high | missing_info, observation_pass, incomplete_input | clarify | 観測パスに読ませるのはGemma2の出力＋読み込ませた感情値でどうでしょう、そこから改めて変化を出力簡素化が可能なら() |
| cowork-v6-012 | medium | conditional_adoption, evaluation_plan | respond | それではcode側で7日間検証をしながら出力が弱い(オウム返し)等だった場合途中でも採用します！ありがとうございました。 |
| cowork-v6-016 | medium | future_scope, ui_voice_live2d, compound_intent | build | 更に、その先で余裕がある場合の実装案 live２Ⅾでキャラ化(表現、感情の出力として)音声(live２Ⅾに合わせて)その前にUI関係も決めないといけないですね |
| cowork-v6-017 | medium | proposal_request, context_dependent | explore | 今の所はこんなところです！現状から、ここは作った方が良い！と言う提案はありますか？ |
| cowork-v6-025 | medium | verify_path, startup_question | respond | Claudeさん！データの蓄積って"<PATH> |
| cowork-v6-032 | medium | definition_context, persona_design | respond | AIのペルソナです。書き換えを許可する事で、変化を取り入れ最適化？独自性を育てます |
| cowork-v6-040 | low | format_preference, context_dependent | respond | 良いですね。思い出しやすい形でよろしくお願いします！ |
| cowork-v6-042 | medium | environment_choice, fallback_plan | respond | Stabilitymatrlx だと、構造に手を出しにくいので一回<PATH> に戻ります |
| cowork-v6-044 | medium | unverified_claim, model_selection | respond | 複数モデルがインストールされているので自動的に使われたものと思われます |
| cowork-v6-051 | medium | status_with_finding, capability_inference | respond | wan2.2の方はモデル探しちょっとかかりそうなのでテンプレートのLTS2.3使って動画が作られ始めました。⑱は未対応ですが、実装メモリを超えたモデルでもきちんと動くことが分かり可能性を感じます！ |

## Reject / Quarantine

| ID | Reason | Redacted Input |
|---|---|---|
| cowork-v6-001 | GitHub account URL; not a routing sample. | 作製したアカウントこちらです！<URL> |
| cowork-v6-005 | Image placeholder has no text semantics. | [Image attached] |
| cowork-v6-006 | Pure completion status. | gitは行けました！ |
| cowork-v6-013 | Too short and contextless. | 追記おねがいします |
| cowork-v6-014 | Thanks only. | ありがとうございます！ |
| cowork-v6-019 | Thanks only. | ありがとうございます！お疲れ様でした |
| cowork-v6-022 | Meta marker, not user natural prompt. | [schedule skillのSKILL.md読み込み] |
| cowork-v6-023 | Generic acknowledgement. | ではよろしくお願いします！ |
| cowork-v6-024 | Casual cost-plan comment only. | ありがとうございます！従量課金でなくmaxプランを選んでよかったです！ |
| cowork-v6-026 | Thread premise, not task input. | このスレッドは提案、構想ベース半分雑談です！ |
| cowork-v6-034 | Approval only. | 良いですね。採用したいです！ |
| cowork-v6-036 | Status/approval only. | 良いですね。思考用に中型モデルも置いてるので丁度いいです。 |
| cowork-v6-038 | Name preference only. | ANIMA「育つ魂」って所が良いですね |
| cowork-v6-041 | Thanks only. | ありがとうございます！またアイディアが湧いたらここに書き込みます！ |
| cowork-v6-046 | Status only. | 開きました。ワークフローが共有されてました |
| cowork-v6-047 | Placeholder log success, no actionable text. | [pip install ログ貼付、torch/transformers等インストール成功] |
| cowork-v6-050 | Going-to-try status. | [手動インストール手順の情報共有、依存関係インストール、モデルファイル確認について] 探してきました！やってきます |
| cowork-v6-058 | Thanks only. | ありがとうございます！使ってきます！ |
| cowork-v6-059 | Command trigger, not natural routing sample. | <command-message>anthropic-skills:setup-cowork</command-message> <command-name>/anthropic-skills:... |

## Recommended V6 Use

1. Use `adopt_nonsealed` as review worksheet inputs, not as automatic training data.
2. Rewrite `rewrite_before_use` into sanitized, self-contained prompts before adding them to any fixture.
3. Prioritize clarify/missing-info, compound intent, build/verify/respond boundary, and debug/error patterns.
4. Keep rejects quarantined; most are acknowledgements, status-only messages, image placeholders, or command triggers.
