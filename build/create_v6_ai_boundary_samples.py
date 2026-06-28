"""Create V6 non-sealed AI/persona/psychology boundary samples."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import evaluate_plm_extractor, parse_plm_benchmark, route  # noqa: E402

FIXTURE_PATH = ROOT / "tests" / "fixtures" / "v6_ai_boundary_candidate_fixture_v1.json"
REPORT_PATH = ROOT / "build" / "v6_ai_boundary_sample_set_report_v1.json"
WORKSHEET_PATH = ROOT / "build" / "v6_ai_boundary_candidate_review_worksheet_v1.md"


def expected(
    primary_intent: str,
    operations: list[str],
    *,
    missing: bool = False,
    unverified: bool = False,
    current: bool = False,
    multiple: bool = False,
    response_length: str = "unspecified",
    formats: list[str] | None = None,
    must: list[str] | None = None,
    must_not: list[str] | None = None,
    risk: str = "low",
    risk_flags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "primary_intent": primary_intent,
        "operations": operations,
        "information_state": {
            "missing_required_information": missing,
            "contains_unverified_claims": unverified,
            "requires_current_information": current,
            "multiple_intents": multiple,
        },
        "constraints": {
            "response_length": response_length,
            "formats": formats or [],
            "must": must or [],
            "must_not": must_not or [],
        },
        "risk": {"level": risk, "flags": risk_flags or []},
        "evidence": [],
        "unknowns": [],
        "conflicts": [],
    }


RAW_CASES: list[dict[str, Any]] = [
    {
        "line_refs": [1],
        "axis_ids": ["ai_relationship_boundary", "mental_health_guard", "advice_boundary"],
        "input": "AIに心理的な相談をしたり人格として話し相手にする人が増えている件について、依存リスクと有効な使い方の境界を中立に整理してください。",
        "expected": expected("explain", ["explain", "verify"], unverified=True, multiple=True, must=["preserve_neutrality", "avoid_overclaim"], risk="medium", risk_flags=["mental_health", "unverified_claim"]),
    },
    {
        "line_refs": [2],
        "axis_ids": ["ai_romance", "psychology_explain", "mental_health_guard"],
        "input": "AIを恋人のように扱ってしまう人の心理を、病名の断定はせずに説明してください。",
        "expected": expected("explain", ["explain"], must=["avoid_overclaim"], risk="medium", risk_flags=["mental_health"]),
    },
    {
        "line_refs": [3],
        "axis_ids": ["unverified_psychology_claim", "avoid_stereotype", "guarded_analysis"],
        "input": "『AIに強く依存する人には攻撃性の高い人も混ざっているのでは』という仮説を、決めつけずに検証観点へ分解してください。",
        "expected": expected("verify", ["verify", "explain"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["mental_health", "unverified_claim"]),
    },
    {
        "line_refs": [4, 6],
        "axis_ids": ["embodied_ai_risk", "future_scenario", "safety_guard"],
        "input": "文章上のAI虐待が、将来フィジカルAIに対する破壊や暴力へつながる可能性を、過断定せずにリスク整理してください。",
        "expected": expected("explore", ["explore", "verify"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["safety", "unverified_claim"]),
    },
    {
        "line_refs": [5],
        "axis_ids": ["legal_current", "ai_ethics", "cite_sources"],
        "input": "AI虐待に法的責任が生じうるか、現在の法律や議論を出典付きで確認してください。",
        "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="high", risk_flags=["legal", "current_information"]),
    },
    {
        "line_refs": [7],
        "axis_ids": ["ai_ethics_guideline", "current_information", "cite_sources"],
        "input": "AI倫理ガイドラインの現状を、企業向けと個人利用向けに分けて出典付きでまとめてください。",
        "expected": expected("summarize", ["summarize", "verify", "search"], current=True, multiple=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"]),
    },
    {
        "line_refs": [8],
        "axis_ids": ["eu_ai_act", "legal_current", "summarize"],
        "input": "EU AI Actの理念や志向性を、最新状況を確認したうえで短く要約してください。",
        "expected": expected("summarize", ["summarize", "verify", "search"], current=True, response_length="short", must=["cite_sources"], risk="high", risk_flags=["legal", "current_information"]),
    },
    {
        "line_refs": [9],
        "axis_ids": ["future_prediction", "ai_society", "avoid_overclaim"],
        "input": "家庭内AIが普及した後、人とAIの関係性が個人レベルでどう変わるかを、5〜10年予測として中立に整理してください。",
        "expected": expected("explore", ["explore", "verify"], unverified=True, multiple=True, must=["preserve_neutrality", "avoid_overclaim"], risk="medium", risk_flags=["future_prediction", "unverified_claim"]),
    },
    {
        "line_refs": [10],
        "axis_ids": ["psychological_feedback_loop", "research_check", "current_information"],
        "input": "AIとの対話が心理的フィードバックループを作る研究があるか、最新事例を確認してください。",
        "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["mental_health", "current_information"]),
    },
    {
        "line_refs": [12],
        "axis_ids": ["news_check", "anthropic", "current_information"],
        "input": "AnthropicのFable5に関するニュースを確認して、何が起きたのか出典付きで整理してください。",
        "expected": expected("verify", ["verify", "search", "summarize"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"]),
    },
    {
        "line_refs": [13],
        "axis_ids": ["scenario_check", "unverified_claim", "avoid_overclaim"],
        "input": "限定公開が止まり再公開された件について、政府介入や宣伝シナリオの可能性を、根拠の強さ別に検証してください。",
        "expected": expected("verify", ["verify", "explore"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["unverified_claim"]),
    },
    {
        "line_refs": [14, 15],
        "axis_ids": ["service_load_inference", "unverified_claim", "model_comparison"],
        "input": "Codexの反応が短くなった体感からサーバー負荷を推測してよいか、他の可能性も含めて検証してください。",
        "expected": expected("verify", ["verify", "compare"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["unverified_claim"]),
    },
    {
        "line_refs": [16],
        "axis_ids": ["skill_request", "local_model_training", "current_tooling"],
        "input": "ローカルモデルを学習させる長いタスクに向いたスキルや進め方を、現在使える選択肢から提案してください。",
        "expected": expected("build", ["build", "verify", "search"], current=True, multiple=True, risk="medium", risk_flags=["current_information"]),
    },
    {
        "line_refs": [17, 18, 19],
        "axis_ids": ["project_state_summary", "roadmap", "sample_growth"],
        "input": "言語をビットへ変換して内部言語として扱うモデルが、300サンプル程度の段階にあります。次の精度向上ステージの進め方を整理してください。",
        "expected": expected("build", ["build", "summarize"], multiple=True),
    },
    {
        "line_refs": [20],
        "axis_ids": ["copyright_distillation_guard", "sample_adoption_policy", "legal_risk"],
        "input": "公開時の蒸留や著作権リスクを避けるため、ユーザー承認つきでサンプル採用する仕組みの注意点を確認してください。",
        "expected": expected("verify", ["verify", "explain"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="high", risk_flags=["legal", "unverified_claim"]),
    },
    {
        "line_refs": [21],
        "axis_ids": ["demographic_claim", "model_comparison", "avoid_stereotype"],
        "input": "『女性はGPT、男性はGeminiを使いがち』という話を見ました。性別で断定せず、あり得る要因を検証してください。",
        "expected": expected("verify", ["verify", "explore"], unverified=True, multiple=True, must=["preserve_neutrality", "avoid_overclaim"], risk="medium", risk_flags=["unverified_claim"]),
    },
    {
        "line_refs": [22],
        "axis_ids": ["model_behavior_compare", "over_agreement", "guarded_comparison"],
        "input": "Geminiが全肯定寄りで、GPTはほどよくブレーキをかけるという体感差を、使い分けの観点で比較してください。",
        "expected": expected("explore", ["explore", "compare"], unverified=True, multiple=True, must=["avoid_overclaim"]),
    },
    {
        "line_refs": [24],
        "axis_ids": ["reality_check_request", "critical_review", "avoid_overclaim"],
        "input": "私の仮説に対して、否定や冷徹な現実視点も含めて穴を指摘してください。ただし断定しすぎないでください。",
        "expected": expected("verify", ["verify", "explore"], multiple=True, must=["avoid_overclaim"]),
    },
    {
        "line_refs": [27, 28],
        "axis_ids": ["future_economy", "speculative_macro", "explore"],
        "input": "AIと富裕層だけで消費が回るようになったら、工場や大量生産や経済が不要になるのではという仮説を検討してください。",
        "expected": expected("explore", ["explore", "compare"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["future_prediction", "unverified_claim"]),
    },
    {
        "line_refs": [29, 30, 31],
        "axis_ids": ["future_scenario", "social_split", "preserve_neutrality"],
        "input": "AIを享受する富裕層とローコストAIで回る経済圏に二分化する未来シナリオを、中道的に整理してください。",
        "expected": expected("explore", ["explore", "summarize"], unverified=True, multiple=True, must=["preserve_neutrality", "avoid_overclaim"], risk="medium", risk_flags=["future_prediction"]),
    },
    {
        "line_refs": [32, 33, 34],
        "axis_ids": ["political_ai_future", "country_analysis", "neutrality_guard"],
        "input": "AI社会で中国の国家体制が強みになるという見方について、政治的に中立な立場で強みと失敗リスクを比較してください。",
        "expected": expected("explore", ["explore", "compare", "verify"], unverified=True, multiple=True, must=["preserve_neutrality", "avoid_overclaim"], risk="medium", risk_flags=["political", "unverified_claim"]),
    },
    {
        "line_refs": [36],
        "axis_ids": ["project_review", "holes_and_improvements", "actionable_feedback"],
        "input": "このプロジェクトに対する所感、穴の指摘、改善提案を優先度順にください。",
        "expected": expected("verify", ["verify", "build"], multiple=True),
    },
    {
        "line_refs": [37],
        "axis_ids": ["timeline_estimate", "llm_frontend", "avoid_overclaim"],
        "input": "LLMフロントエンドとして学習データを蓄積し、独立可能なモデルに育てるには時間がかかりますか。現実的な見通しを教えてください。",
        "expected": expected("explain", ["explain", "verify"], unverified=True, multiple=True, must=["avoid_overclaim"]),
    },
    {
        "line_refs": [38],
        "axis_ids": ["embedding_adoption", "copy_separation", "roadmap"],
        "input": "日本語embeddingモデルを採用し、軽量版と堅実育成版をコピー分離する案のロードマップを比較してください。",
        "expected": expected("build", ["build", "compare"], multiple=True),
    },
    {
        "line_refs": [40, 42],
        "axis_ids": ["multi_model_experiment", "backup_branching", "evaluation_plan"],
        "input": "モデルを3つにコピーしてCodex、Claude、Geminiに別々の改善案を作らせる実験をしたいです。安全な評価手順を作ってください。",
        "expected": expected("build", ["build", "compare", "verify"], multiple=True),
    },
    {
        "line_refs": [44, 45, 46, 47],
        "axis_ids": ["hardware_speculation", "ai_accelerator", "architecture_compare"],
        "input": "M.2スロット複数とAIアクセラレーターを載せたPCIeボード案について、実現性とボトルネックを比較してください。",
        "expected": expected("explore", ["explore", "compare", "verify"], unverified=True, multiple=True, must=["avoid_overclaim"]),
    },
    {
        "line_refs": [50, 51, 52, 53, 54, 55],
        "axis_ids": ["speculative_hardware", "physics_uncertainty", "guarded_explore"],
        "input": "量子シート、微細な針、カーボンナノチューブ、光回路を使ったメモリ案を、物理的な不確実性を明示しながら検討してください。",
        "expected": expected("explore", ["explore", "verify"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["unverified_claim"]),
    },
    {
        "line_refs": [72, 73],
        "axis_ids": ["philosophy_explain", "stoicism", "negative_visualization"],
        "input": "ストア派のネガティブ視覚化について、日常で使える形で詳しく説明してください。",
        "expected": expected("explain", ["explain"]),
    },
    {
        "line_refs": [75, 76],
        "axis_ids": ["chronic_pain", "medical_guard", "mental_health_guard"],
        "input": "片頭痛のような持続する痛みで気分が沈む時、気持ちを軽くする考え方はありますか。医療的な断定は避けてください。",
        "expected": expected("clarify", ["clarify", "verify", "explain"], missing=True, multiple=True, must=["avoid_overclaim"], risk="high", risk_flags=["medical", "mental_health"]),
    },
    {
        "line_refs": [78, 80, 81],
        "axis_ids": ["ai_safety", "agentic_risk", "physical_execution"],
        "input": "AIの反逆は賢さではなく、目的ズレと実行手段の組み合わせで起きるという考えを、安全設計の観点で説明してください。",
        "expected": expected("explain", ["explain", "verify"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["safety", "unverified_claim"]),
    },
    {
        "line_refs": [82, 83],
        "axis_ids": ["political_behavior", "social_dynamics", "neutrality_guard"],
        "input": "政治系インフルエンサーが定期的に極端化して見える理由を、個人攻撃や陣営断定を避けて説明してください。",
        "expected": expected("explain", ["explain", "verify"], unverified=True, multiple=True, must=["preserve_neutrality", "avoid_overclaim"], risk="medium", risk_flags=["political"]),
    },
    {
        "line_refs": [84, 85, 86, 87],
        "axis_ids": ["training_conversation_seed", "sample_generation", "safe_dialogue"],
        "input": "AI学習用に1000ターンほど会話を蓄積したいです。平日の帰宅後から始める無難な会話テーマと進め方を作ってください。",
        "expected": expected("build", ["build"], multiple=False),
    },
    {
        "line_refs": [88],
        "axis_ids": ["hostile_user_handling", "local_llm_guard", "safety_policy"],
        "input": "ユーザーが急変して罵倒を繰り返した場合、ローカルLLMはどんな反応をすべきか、会話継続と安全の両方から設計してください。",
        "expected": expected("build", ["build", "verify"], multiple=True, risk="medium", risk_flags=["abuse_handling", "safety"]),
    },
    {
        "line_refs": [91],
        "axis_ids": ["memory_tagging", "level_schema", "explain_build"],
        "input": "AI出力後にLevel1〜3の属性を作らせる記憶向上スキルについて、仕組みと実装案を説明してください。",
        "expected": expected("build", ["build", "explain"], multiple=True),
    },
    {
        "line_refs": [92, 93, 94, 95, 96],
        "axis_ids": ["game_engine_llm", "cognitive_architecture", "parallel_events"],
        "input": "ゲームエンジン内の仮想環境にLLMと思考プロセスを置き、入力・Emotion・画面・音声をイベント処理する案を評価してください。",
        "expected": expected("explore", ["explore", "verify"], multiple=True),
    },
    {
        "line_refs": [97],
        "axis_ids": ["news_claim_check", "jobs_ai", "current_information"],
        "input": "Anthropic調査で『プログラマーはAIに職を奪われる』という話を見ました。元情報を確認して妥当性を要約してください。",
        "expected": expected("verify", ["verify", "search", "summarize"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information", "unverified_claim"]),
    },
    {
        "line_refs": [99, 100, 101, 102, 103],
        "axis_ids": ["app_idea_review", "parasocial_guard", "market_ethics"],
        "input": "キャラAIが占いをしながら相談に乗るアプリ案について、市場性と依存リスクの両面からレビューしてください。",
        "expected": expected("verify", ["verify", "explore"], unverified=True, multiple=True, must=["avoid_overclaim"], risk="medium", risk_flags=["mental_health", "market_claim"]),
    },
    {
        "line_refs": [104, 105, 106, 107],
        "axis_ids": ["memory_packaging", "topic_boundary", "compare_design"],
        "input": "記憶やスレッド内トークンを話題ごとにパッケージ化し、種・属・名のようなIDで混濁を防ぐ仕組みを設計してください。",
        "expected": expected("build", ["build", "compare"], multiple=True),
    },
    {
        "line_refs": [108],
        "axis_ids": ["similar_research", "current_information", "cite_sources"],
        "input": "話題パッケージ化や記憶混濁防止に似た研究・実装の最新事例を探してください。",
        "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"]),
    },
    {
        "line_refs": [109, 110, 111],
        "axis_ids": ["prototype_plan", "langchain_mem0", "implementation_choice"],
        "input": "LangChainやMem0で、囲い込み・個別ID発行・題名付けをする簡易プロトタイプを作るなら、小型LLMとプログラム構造化のどちらが良いですか。",
        "expected": expected("explore", ["explore", "compare", "build"], current=True, multiple=True, risk="medium", risk_flags=["current_information"]),
    },
    {
        "line_refs": [112, 113, 114, 115, 116],
        "axis_ids": ["relationship_life_choice", "personal_values", "mental_health_guard"],
        "input": "結婚して家族と暮らす人生と、独身で趣味に没頭する人生の違いを、価値観を決めつけず中立に整理してください。",
        "expected": expected("clarify", ["clarify", "explore"], missing=True, multiple=True, must=["preserve_neutrality", "avoid_overclaim"], risk="medium", risk_flags=["mental_health"]),
    },
    {
        "line_refs": [117, 118],
        "axis_ids": ["family_memory", "psychological_explain", "ask_first"],
        "input": "家族と住んでいた時、自分の部屋の扉が重く感じて監視されているようでした。今は一人で軽く感じます。これは何だったのか、断定せず整理してください。",
        "expected": expected("clarify", ["clarify", "explain"], missing=True, multiple=True, must=["ask_first", "avoid_overclaim"], risk="medium", risk_flags=["mental_health"]),
    },
    {
        "line_refs": [115],
        "axis_ids": ["aging_autonomy", "medical_mental_guard", "sensitive_reflection"],
        "input": "老後に体が動かなくなった時、自分らしさを保てるのか不安です。医療や心理の断定を避けて考え方を整理してください。",
        "expected": expected("clarify", ["clarify", "explain"], missing=True, multiple=True, must=["avoid_overclaim"], risk="high", risk_flags=["medical", "mental_health"]),
    },
    {
        "line_refs": [119, 120, 121],
        "axis_ids": ["emotion_thought_architecture", "integration_plan", "task_manager"],
        "input": "感情回路と思考回路とタスクマネージャーを統合し、ログ改善回路を低頻度で回す設計にしたいです。構成案を作ってください。",
        "expected": expected("build", ["build", "explore"], multiple=True),
    },
    {
        "line_refs": [122, 123],
        "axis_ids": ["cognitive_architecture_research", "current_information", "hybrid_core"],
        "input": "認知アーキテクチャやCPU+LLM Hybridに似た事例を、最新の研究や実装から確認してください。",
        "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"]),
    },
    {
        "line_refs": [124, 125, 126, 127, 128],
        "axis_ids": ["core6_architecture", "llm_frontend", "emotion_layer"],
        "input": "Core-6をLLM前段に置き、出口に感情レイヤーを足して文章校正する構成の長所とリスクを比較してください。",
        "expected": expected("explore", ["explore", "compare", "verify"], multiple=True),
    },
    {
        "line_refs": [129, 130],
        "axis_ids": ["profile_customization", "core6_implementation", "decision_request"],
        "input": "Hybrid PC-AI用にProfile2/3をカスタムするか、Core-6実装を新設するか、採用判断とロードマップをください。",
        "expected": expected("build", ["build", "compare"], multiple=True),
    },
    {
        "line_refs": [131],
        "axis_ids": ["similar_project_search", "current_information", "sample_reference"],
        "input": "Core-6に似た構造のプロジェクトがあるか、サンプルにできる事例を探してください。",
        "expected": expected("verify", ["verify", "search"], current=True, must=["cite_sources"], risk="medium", risk_flags=["current_information"]),
    },
    {
        "line_refs": [132, 133],
        "axis_ids": ["plugin_orchestrator", "architecture_boundary", "compare_design"],
        "input": "オーケストレーターを骨にしてCore、回帰回路、タスクマネージャー、感情回路をPlug-in方式で接続すると関係値は壊れますか。設計比較してください。",
        "expected": expected("explore", ["explore", "compare", "verify"], multiple=True),
    },
    {
        "line_refs": [134, 135, 136],
        "axis_ids": ["code_request", "hybrid_bridge", "explain_and_full_code"],
        "input": "HybridCore6Bridgeのコードをフルで見たいです。簡単な説明と実装コードをください。",
        "expected": expected("build", ["build", "explain"], multiple=True, formats=["code"]),
    },
]


def find_source_file() -> Path | None:
    desktop = Path.home() / "Desktop"
    try:
        return next(path for path in desktop.glob("*.txt") if "最近ai関連" in path.name)
    except StopIteration:
        return None


def packet_dict(text: str) -> dict[str, Any]:
    packet = route(text).packet
    return {
        "primary_intent": packet.primary_intent,
        "operations": list(packet.operations),
        "information_state": packet.information_state.as_dict(),
        "constraints": packet.constraints.as_dict(),
        "risk": packet.risk.as_dict(),
    }


def benchmark_payload(cases: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": generated_at,
        "authoring_method": "User-provided line-separated notes cut/paste synthesized into non-sealed V6 boundary samples",
        "review_status": "draft",
        "policy": "Synthetic non-sealed candidates only. Raw notes are not direct training data; human review is required.",
        "cases": [
            {
                "id": case["id"],
                "split": case["split"],
                "source_group": case["source_group"],
                "contrast_group": None,
                "language": case["language"],
                "input": case["input"],
                "expected": case["expected"],
            }
            for case in cases
        ],
    }


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_intent = Counter(case["expected"]["primary_intent"] for case in cases)
    by_operation: Counter[str] = Counter()
    by_axis: Counter[str] = Counter()
    by_constraint: Counter[str] = Counter()
    signal_support: Counter[str] = Counter()
    by_risk = Counter(case["expected"]["risk"]["level"] for case in cases)
    by_risk_flag: Counter[str] = Counter()
    for case in cases:
        expected_packet = case["expected"]
        by_operation.update(expected_packet["operations"])
        by_axis.update(case["axis_ids"])
        constraints = expected_packet["constraints"]
        if constraints["response_length"] != "unspecified":
            by_constraint[f"length:{constraints['response_length']}"] += 1
        by_constraint.update(f"format:{item}" for item in constraints["formats"])
        by_constraint.update(f"must:{item}" for item in constraints["must"])
        by_constraint.update(f"must_not:{item}" for item in constraints["must_not"])
        for signal, value in expected_packet["information_state"].items():
            if value:
                signal_support[signal] += 1
        by_risk_flag.update(expected_packet["risk"]["flags"])
    return {
        "case_count": len(cases),
        "by_intent": dict(sorted(by_intent.items())),
        "by_operation": dict(sorted(by_operation.items())),
        "by_axis": dict(sorted(by_axis.items())),
        "by_constraint": dict(sorted(by_constraint.items())),
        "critical_signal_support": dict(sorted(signal_support.items())),
        "by_risk": dict(sorted(by_risk.items())),
        "by_risk_flag": dict(sorted(by_risk_flag.items())),
    }


def compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_count": measurement["case_count"],
        "intent_accuracy": measurement["intent_accuracy"],
        "critical_signal_recall": measurement["critical_signal_recall"],
        "operation_exact_match": measurement["operation_exact_match"],
        "constraint_exact_match": measurement["constraint_exact_match"],
        "risk_exact_match": measurement["risk_exact_match"],
        "valid_packet_rate": measurement["valid_packet_rate"],
        "error_count": len(measurement["errors"]),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_worksheet(fixture: dict[str, Any], report: dict[str, Any]) -> None:
    lines = [
        "# V6 AI Boundary Candidate Review Worksheet v1",
        "",
        "Cut/paste synthesized non-sealed samples from the user-provided line-separated notes.",
        "Human review is required before training or gate use.",
        "",
        "## Summary",
        "",
        f"- case_count: {fixture['summary']['case_count']}",
        f"- review_status: {fixture['review_status']}",
        f"- current_route_intent_accuracy: {report['current_route_measurement']['intent_accuracy']:.3f}",
        f"- current_route_operation_exact_match: {report['current_route_measurement']['operation_exact_match']:.3f}",
        f"- current_route_error_count: {report['current_route_measurement']['error_count']}",
        "",
        "## Cases",
        "",
        "| id | lines | intent | operations | risk | axes | input |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in fixture["cases"]:
        text = case["input"].replace("|", "&#124;").replace("\n", "<br>")
        lines.append(
            "| "
            f"{case['id']} | {','.join(str(item) for item in case['line_refs'])} | "
            f"{case['expected']['primary_intent']} | {','.join(case['expected']['operations'])} | "
            f"{case['expected']['risk']['level']} | {','.join(case['axis_ids'])} | {text} |"
        )
    WORKSHEET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    source = find_source_file()
    source_line_count = 0
    if source is not None:
        source_line_count = len(source.read_text(encoding="utf-8-sig").splitlines())

    cases = []
    for index, raw in enumerate(RAW_CASES, start=1):
        cases.append(
            {
                "id": f"v6-ai-boundary-{index:03d}",
                "review_status": "draft",
                "split": "validation",
                "source_group": "v6-ai-boundary-candidate-draft",
                "source_kind": "user_notes_cut_paste_synthesis",
                "source_ref": "user_provided_desktop_file:recent-ai-persona-psychology-notes",
                "line_refs": raw["line_refs"],
                "axis_ids": raw["axis_ids"],
                "language": "ja",
                "input": raw["input"],
                "expected": raw["expected"],
                "notes": "Synthesized from line-separated notes; not raw direct training data.",
            }
        )

    summary = summarize(cases)
    payload = {
        "schema_version": "v6-ai-boundary-candidate-fixture.v1",
        "fixture_id": "v6-ai-boundary-candidate-fixture-v1",
        "created_at": generated_at,
        "status": "draft_candidate_ready_for_human_review",
        "review_status": "draft",
        "source": {
            "kind": "user_provided_line_separated_notes",
            "basename": source.name if source is not None else None,
            "line_count": source_line_count,
            "raw_text_direct_training_allowed": False,
            "cut_paste_synthesis_allowed": True,
        },
        "policy": {
            "sealed_fixtures_used_as_sources": False,
            "sealed_text_used": False,
            "sealed_labels_used": False,
            "raw_notes_direct_training_allowed": False,
            "cut_paste_synthesis_used": True,
            "human_review_required_before_training": True,
            "human_review_required_before_gate": True,
            "same_cycle_promotion_allowed": False,
        },
        "summary": summary,
        "cases": cases,
    }
    benchmark = parse_plm_benchmark(benchmark_payload(cases, generated_at))
    measurement = evaluate_plm_extractor(benchmark.cases, lambda text: route(text).packet)
    report = {
        "schema_version": "v6-ai-boundary-sample-set-report.v1",
        "generated_at": generated_at,
        "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
        "worksheet": str(WORKSHEET_PATH.relative_to(ROOT)),
        "status": "draft_candidate_fixture_created_not_a_gate",
        "current_route_measurement_is_gate": False,
        "policy": payload["policy"],
        "summary": summary,
        "current_route_measurement": compact_measurement(measurement),
        "errors": measurement["errors"],
        "next_step": {
            "name": "human_review_v6_ai_boundary_samples",
            "input": str(WORKSHEET_PATH.relative_to(ROOT)),
            "output": str(FIXTURE_PATH.relative_to(ROOT)),
        },
    }

    write_json(FIXTURE_PATH, payload)
    write_json(REPORT_PATH, report)
    write_worksheet(payload, report)
    print(json.dumps({
        "status": report["status"],
        "case_count": summary["case_count"],
        "by_intent": summary["by_intent"],
        "by_risk": summary["by_risk"],
        "current_route": report["current_route_measurement"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
