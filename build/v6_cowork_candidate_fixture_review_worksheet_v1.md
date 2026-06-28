# V6 Cowork Candidate Fixture Review Worksheet v1

Non-sealed candidate material from redacted Cowork raw logs. Human review is required before training or gate use.

## Probe Summary

- source_items: 25
- promoted_candidates: 22
- intent_accuracy_on_promoted: 0.136
- operation_subset_rate_on_promoted: 0.091
- current_route_gap_count: 20

## Cases

| id | score | status | intent | operations | axes | input |
| --- | ---: | --- | --- | --- | --- | --- |
| v6-cowork-candidate-001 | 7 | route_gap | build | build,verify | compound_intent,processing_plan,separate_pass,cognitive_load | 構成はpassですが、処理としてはチャットの処理出力が終るのをきっかけにpassが稼働する仕組みにしてもらえると負担が下がります。ログが混ざらない、処理も分ける事で思考力の低下を抑える仕組みです。 |
| v6-cowork-candidate-002 | 7 | route_gap | build | build,verify | compound_intent,processing_plan,separate_pass,cognitive_load | 構成は2passですが、処理としてはチャット層の出力が終るのをきっかけに2pass目が稼働する仕組みにしてもらえると負担が下がります。ログが混ざらない、処理も分ける事で思考力の低下を抑える仕組みです。 |
| v6-cowork-candidate-003 | 7 | route_gap | build | build,verify | compound_intent,emotion_dynamics,parameter_tuning,missing_context | ちょっとログがどこに行ったか分からなくなってしまったのですが…<br>emotに対する動的変化として、現在有る時間経過からの感情変化。以外で感情への刺激になりそうな変化を取り入れる。という物です！あと、現在の寂しいの数値は早く上がりすぎるので、実装時は調整を入れたい！という物です |
| v6-cowork-candidate-004 | 6 | route_gap | summarize | summarize | summarize_to_memo,prioritization,handoff | 明日code側を始める際にPhase 5 を待たずに今すぐ着手できる 3 つをメモとして渡したいです！ |
| v6-cowork-candidate-005 | 7 | route_gap | build | build,verify | periodic_review,automation,log_accumulation | dataの蓄積に当たってなのですが、定期的にログを確認してもらい、調整をしてもらうことはかのうでしょうか |
| v6-cowork-candidate-006 | 5 | route_gap | clarify | clarify | scheduling_constraint,missing_runtime_window | PC立ち上げ時出ないとログ確認できないのでその時にお願いしたいです！ |
| v6-cowork-candidate-007 | 7 | route_gap | explore | explore | brainstorm,multi_option,architecture | まず考えてるのは<br>1、ペルソナcard、保存すべき基礎的情報を保持。呼び名や性格、優先事項など。<br>2、脳ノイズの再現、並列処理から、ノイズを抽出しemotionに返す仕組み。<br>3、ゲームエンジンの採用、並列処理、拡張、AI自身に仮想空間を持たせられる。 |
| v6-cowork-candidate-008 | 6 | route_gap | explore | explore | clarify_or_explore,engine_choice,constraint_lightweight | 常駐を目指すなら軽量なエンジンが良いんでしょうか？ |
| v6-cowork-candidate-009 | 7 | route_gap | explore | explore,compare | compare_options,language_stack,external_integration | 外枠はpython以外もアリだと思ってます、外の接続をする、拡張性、を考えて、C#、rust、goなんかもアリだと |
| v6-cowork-candidate-010 | 7 | route_gap | build | build,verify | memory_persona,update_policy,vectorization,compound_intent | そうですね！ペルソナcardは基本を最初に書いておいて、AIが追記、書き換えを行える仕組みが良いとおもいます。書き換えの際は、プロンプトの重要度で触る際簡単に変更しない様に指示。みたいな構造です。出来ればベクトル化が理想です。 |
| v6-cowork-candidate-011 | 7 | route_gap | explore | explore,compare | compare_options,knowledge_source,llm_vs_chromadb,architecture | あと一つ懸念というか、LLMは知識の塊なので、自然な会話になります。CPU先行のこの構造で基礎知識をどう取り入れるか？と考えてました。LLMを基礎知識として使って良いのか？それとも時間がかかるので、専用ChromaDBを置くのか？と |
| v6-cowork-candidate-012 | 4 | route_matches_hint | build | build | naming_request,creative_build | 後で自然に決まりますが、名前があるとブレにくくなるので一つ命名をお願いしたいです！ |
| v6-cowork-candidate-013 | 6 | route_gap | build | build,summarize | docs_update,future_roadmap,phase_boundary | 現状テストを繰り返して蓄積するphaseなので、すべてのphaseが終った後に始める構想としてdocsに残していきたいです！ |
| v6-cowork-candidate-014 | 7 | route_gap | verify | verify | debug_error,missing_file,path_context | (.venv) PS <PATH> python main.py<br>can't open file '<PATH> [Errno 2] No such file or directoryエラーです！ |
| v6-cowork-candidate-015 | 7 | route_gap | verify | verify | debug_error,missing_dependency | Traceback (most recent call last):<br>...<br>ModuleNotFoundError: No module named 'sqlalchemy' |
| v6-cowork-candidate-016 | 6 | route_gap | explain | explain | explain_term,tool_concept,after_success_question | 起動できました！サブグラフと言うのは外部のものだったりしますか |
| v6-cowork-candidate-017 | 7 | route_gap | verify | verify | debug_error,security_policy,custom_node_install | ComfyUI-HunyuanVideo-Foleyこのモデルだけエラーになります<br>[Installation Errors] 'ComfyUI-HunyuanVideo-Foley': With the current security level configuration, only custom nodes from the "default channel" can be installed. |
| v6-cowork-candidate-018 | 6 | route_gap | build | build,summarize | prioritize,write_md,improvement_plan | 優先度高から修正案として.mdにまとめて頂きたいです |
| v6-cowork-candidate-019 | 7 | route_gap | verify | verify,explain | evaluate_draft,skill_review,uncertainty | [Trace Rule v0.1 skill fileアップロード]<br>ちなみに、これの草案としてskillにしたものなのですが、どのくらいの効果が見込めるとか分かりますか |
| v6-cowork-candidate-020 | 7 | route_gap | explore | explore,compare | compare_design,topic_filter,memory_reference | これ、逆に、話題の混濁だけ焦点に当てて、レベル1とレベル2だけを実装して、レベル1、レベル2が違う話題は参照トークンとして使わないとかだったらどう？ |
| v6-cowork-candidate-021 | 7 | route_gap | build | build,verify | build_rule,multi_tag,topic_list | level2に複数の項目(2～3)を付けられるようにして、level１のみトピックスの一覧を作るのはどうでしょう。 |
| v6-cowork-candidate-022 | 5 | route_matches_hint | build | build | write_skill_file,versioned_spec | v0.2としてスキルファイルに指定だだきたいです！ |
