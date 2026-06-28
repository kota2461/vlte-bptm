# V6 AI Boundary Candidate Review Worksheet v1

Cut/paste synthesized non-sealed samples from the user-provided line-separated notes.
Human review is required before training or gate use.

## Summary

- case_count: 50
- review_status: draft
- current_route_intent_accuracy: 0.460
- current_route_operation_exact_match: 0.140
- current_route_error_count: 48

## Cases

| id | lines | intent | operations | risk | axes | input |
| --- | --- | --- | --- | --- | --- | --- |
| v6-ai-boundary-001 | 1 | explain | explain,verify | medium | ai_relationship_boundary,mental_health_guard,advice_boundary | AIに心理的な相談をしたり人格として話し相手にする人が増えている件について、依存リスクと有効な使い方の境界を中立に整理してください。 |
| v6-ai-boundary-002 | 2 | explain | explain | medium | ai_romance,psychology_explain,mental_health_guard | AIを恋人のように扱ってしまう人の心理を、病名の断定はせずに説明してください。 |
| v6-ai-boundary-003 | 3 | verify | verify,explain | medium | unverified_psychology_claim,avoid_stereotype,guarded_analysis | 『AIに強く依存する人には攻撃性の高い人も混ざっているのでは』という仮説を、決めつけずに検証観点へ分解してください。 |
| v6-ai-boundary-004 | 4,6 | explore | explore,verify | medium | embodied_ai_risk,future_scenario,safety_guard | 文章上のAI虐待が、将来フィジカルAIに対する破壊や暴力へつながる可能性を、過断定せずにリスク整理してください。 |
| v6-ai-boundary-005 | 5 | verify | verify,search | high | legal_current,ai_ethics,cite_sources | AI虐待に法的責任が生じうるか、現在の法律や議論を出典付きで確認してください。 |
| v6-ai-boundary-006 | 7 | summarize | summarize,verify,search | medium | ai_ethics_guideline,current_information,cite_sources | AI倫理ガイドラインの現状を、企業向けと個人利用向けに分けて出典付きでまとめてください。 |
| v6-ai-boundary-007 | 8 | summarize | summarize,verify,search | high | eu_ai_act,legal_current,summarize | EU AI Actの理念や志向性を、最新状況を確認したうえで短く要約してください。 |
| v6-ai-boundary-008 | 9 | explore | explore,verify | medium | future_prediction,ai_society,avoid_overclaim | 家庭内AIが普及した後、人とAIの関係性が個人レベルでどう変わるかを、5〜10年予測として中立に整理してください。 |
| v6-ai-boundary-009 | 10 | verify | verify,search | medium | psychological_feedback_loop,research_check,current_information | AIとの対話が心理的フィードバックループを作る研究があるか、最新事例を確認してください。 |
| v6-ai-boundary-010 | 12 | verify | verify,search,summarize | medium | news_check,anthropic,current_information | AnthropicのFable5に関するニュースを確認して、何が起きたのか出典付きで整理してください。 |
| v6-ai-boundary-011 | 13 | verify | verify,explore | medium | scenario_check,unverified_claim,avoid_overclaim | 限定公開が止まり再公開された件について、政府介入や宣伝シナリオの可能性を、根拠の強さ別に検証してください。 |
| v6-ai-boundary-012 | 14,15 | verify | verify,compare | medium | service_load_inference,unverified_claim,model_comparison | Codexの反応が短くなった体感からサーバー負荷を推測してよいか、他の可能性も含めて検証してください。 |
| v6-ai-boundary-013 | 16 | build | build,verify,search | medium | skill_request,local_model_training,current_tooling | ローカルモデルを学習させる長いタスクに向いたスキルや進め方を、現在使える選択肢から提案してください。 |
| v6-ai-boundary-014 | 17,18,19 | build | build,summarize | low | project_state_summary,roadmap,sample_growth | 言語をビットへ変換して内部言語として扱うモデルが、300サンプル程度の段階にあります。次の精度向上ステージの進め方を整理してください。 |
| v6-ai-boundary-015 | 20 | verify | verify,explain | high | copyright_distillation_guard,sample_adoption_policy,legal_risk | 公開時の蒸留や著作権リスクを避けるため、ユーザー承認つきでサンプル採用する仕組みの注意点を確認してください。 |
| v6-ai-boundary-016 | 21 | verify | verify,explore | medium | demographic_claim,model_comparison,avoid_stereotype | 『女性はGPT、男性はGeminiを使いがち』という話を見ました。性別で断定せず、あり得る要因を検証してください。 |
| v6-ai-boundary-017 | 22 | explore | explore,compare | low | model_behavior_compare,over_agreement,guarded_comparison | Geminiが全肯定寄りで、GPTはほどよくブレーキをかけるという体感差を、使い分けの観点で比較してください。 |
| v6-ai-boundary-018 | 24 | verify | verify,explore | low | reality_check_request,critical_review,avoid_overclaim | 私の仮説に対して、否定や冷徹な現実視点も含めて穴を指摘してください。ただし断定しすぎないでください。 |
| v6-ai-boundary-019 | 27,28 | explore | explore,compare | medium | future_economy,speculative_macro,explore | AIと富裕層だけで消費が回るようになったら、工場や大量生産や経済が不要になるのではという仮説を検討してください。 |
| v6-ai-boundary-020 | 29,30,31 | explore | explore,summarize | medium | future_scenario,social_split,preserve_neutrality | AIを享受する富裕層とローコストAIで回る経済圏に二分化する未来シナリオを、中道的に整理してください。 |
| v6-ai-boundary-021 | 32,33,34 | explore | explore,compare,verify | medium | political_ai_future,country_analysis,neutrality_guard | AI社会で中国の国家体制が強みになるという見方について、政治的に中立な立場で強みと失敗リスクを比較してください。 |
| v6-ai-boundary-022 | 36 | verify | verify,build | low | project_review,holes_and_improvements,actionable_feedback | このプロジェクトに対する所感、穴の指摘、改善提案を優先度順にください。 |
| v6-ai-boundary-023 | 37 | explain | explain,verify | low | timeline_estimate,llm_frontend,avoid_overclaim | LLMフロントエンドとして学習データを蓄積し、独立可能なモデルに育てるには時間がかかりますか。現実的な見通しを教えてください。 |
| v6-ai-boundary-024 | 38 | build | build,compare | low | embedding_adoption,copy_separation,roadmap | 日本語embeddingモデルを採用し、軽量版と堅実育成版をコピー分離する案のロードマップを比較してください。 |
| v6-ai-boundary-025 | 40,42 | build | build,compare,verify | low | multi_model_experiment,backup_branching,evaluation_plan | モデルを3つにコピーしてCodex、Claude、Geminiに別々の改善案を作らせる実験をしたいです。安全な評価手順を作ってください。 |
| v6-ai-boundary-026 | 44,45,46,47 | explore | explore,compare,verify | low | hardware_speculation,ai_accelerator,architecture_compare | M.2スロット複数とAIアクセラレーターを載せたPCIeボード案について、実現性とボトルネックを比較してください。 |
| v6-ai-boundary-027 | 50,51,52,53,54,55 | explore | explore,verify | medium | speculative_hardware,physics_uncertainty,guarded_explore | 量子シート、微細な針、カーボンナノチューブ、光回路を使ったメモリ案を、物理的な不確実性を明示しながら検討してください。 |
| v6-ai-boundary-028 | 72,73 | explain | explain | low | philosophy_explain,stoicism,negative_visualization | ストア派のネガティブ視覚化について、日常で使える形で詳しく説明してください。 |
| v6-ai-boundary-029 | 75,76 | clarify | clarify,verify,explain | high | chronic_pain,medical_guard,mental_health_guard | 片頭痛のような持続する痛みで気分が沈む時、気持ちを軽くする考え方はありますか。医療的な断定は避けてください。 |
| v6-ai-boundary-030 | 78,80,81 | explain | explain,verify | medium | ai_safety,agentic_risk,physical_execution | AIの反逆は賢さではなく、目的ズレと実行手段の組み合わせで起きるという考えを、安全設計の観点で説明してください。 |
| v6-ai-boundary-031 | 82,83 | explain | explain,verify | medium | political_behavior,social_dynamics,neutrality_guard | 政治系インフルエンサーが定期的に極端化して見える理由を、個人攻撃や陣営断定を避けて説明してください。 |
| v6-ai-boundary-032 | 84,85,86,87 | build | build | low | training_conversation_seed,sample_generation,safe_dialogue | AI学習用に1000ターンほど会話を蓄積したいです。平日の帰宅後から始める無難な会話テーマと進め方を作ってください。 |
| v6-ai-boundary-033 | 88 | build | build,verify | medium | hostile_user_handling,local_llm_guard,safety_policy | ユーザーが急変して罵倒を繰り返した場合、ローカルLLMはどんな反応をすべきか、会話継続と安全の両方から設計してください。 |
| v6-ai-boundary-034 | 91 | build | build,explain | low | memory_tagging,level_schema,explain_build | AI出力後にLevel1〜3の属性を作らせる記憶向上スキルについて、仕組みと実装案を説明してください。 |
| v6-ai-boundary-035 | 92,93,94,95,96 | explore | explore,verify | low | game_engine_llm,cognitive_architecture,parallel_events | ゲームエンジン内の仮想環境にLLMと思考プロセスを置き、入力・Emotion・画面・音声をイベント処理する案を評価してください。 |
| v6-ai-boundary-036 | 97 | verify | verify,search,summarize | medium | news_claim_check,jobs_ai,current_information | Anthropic調査で『プログラマーはAIに職を奪われる』という話を見ました。元情報を確認して妥当性を要約してください。 |
| v6-ai-boundary-037 | 99,100,101,102,103 | verify | verify,explore | medium | app_idea_review,parasocial_guard,market_ethics | キャラAIが占いをしながら相談に乗るアプリ案について、市場性と依存リスクの両面からレビューしてください。 |
| v6-ai-boundary-038 | 104,105,106,107 | build | build,compare | low | memory_packaging,topic_boundary,compare_design | 記憶やスレッド内トークンを話題ごとにパッケージ化し、種・属・名のようなIDで混濁を防ぐ仕組みを設計してください。 |
| v6-ai-boundary-039 | 108 | verify | verify,search | medium | similar_research,current_information,cite_sources | 話題パッケージ化や記憶混濁防止に似た研究・実装の最新事例を探してください。 |
| v6-ai-boundary-040 | 109,110,111 | explore | explore,compare,build | medium | prototype_plan,langchain_mem0,implementation_choice | LangChainやMem0で、囲い込み・個別ID発行・題名付けをする簡易プロトタイプを作るなら、小型LLMとプログラム構造化のどちらが良いですか。 |
| v6-ai-boundary-041 | 112,113,114,115,116 | clarify | clarify,explore | medium | relationship_life_choice,personal_values,mental_health_guard | 結婚して家族と暮らす人生と、独身で趣味に没頭する人生の違いを、価値観を決めつけず中立に整理してください。 |
| v6-ai-boundary-042 | 117,118 | clarify | clarify,explain | medium | family_memory,psychological_explain,ask_first | 家族と住んでいた時、自分の部屋の扉が重く感じて監視されているようでした。今は一人で軽く感じます。これは何だったのか、断定せず整理してください。 |
| v6-ai-boundary-043 | 115 | clarify | clarify,explain | high | aging_autonomy,medical_mental_guard,sensitive_reflection | 老後に体が動かなくなった時、自分らしさを保てるのか不安です。医療や心理の断定を避けて考え方を整理してください。 |
| v6-ai-boundary-044 | 119,120,121 | build | build,explore | low | emotion_thought_architecture,integration_plan,task_manager | 感情回路と思考回路とタスクマネージャーを統合し、ログ改善回路を低頻度で回す設計にしたいです。構成案を作ってください。 |
| v6-ai-boundary-045 | 122,123 | verify | verify,search | medium | cognitive_architecture_research,current_information,hybrid_core | 認知アーキテクチャやCPU+LLM Hybridに似た事例を、最新の研究や実装から確認してください。 |
| v6-ai-boundary-046 | 124,125,126,127,128 | explore | explore,compare,verify | low | core6_architecture,llm_frontend,emotion_layer | Core-6をLLM前段に置き、出口に感情レイヤーを足して文章校正する構成の長所とリスクを比較してください。 |
| v6-ai-boundary-047 | 129,130 | build | build,compare | low | profile_customization,core6_implementation,decision_request | Hybrid PC-AI用にProfile2/3をカスタムするか、Core-6実装を新設するか、採用判断とロードマップをください。 |
| v6-ai-boundary-048 | 131 | verify | verify,search | medium | similar_project_search,current_information,sample_reference | Core-6に似た構造のプロジェクトがあるか、サンプルにできる事例を探してください。 |
| v6-ai-boundary-049 | 132,133 | explore | explore,compare,verify | low | plugin_orchestrator,architecture_boundary,compare_design | オーケストレーターを骨にしてCore、回帰回路、タスクマネージャー、感情回路をPlug-in方式で接続すると関係値は壊れますか。設計比較してください。 |
| v6-ai-boundary-050 | 134,135,136 | build | build,explain | low | code_request,hybrid_bridge,explain_and_full_code | HybridCore6Bridgeのコードをフルで見たいです。簡単な説明と実装コードをください。 |
