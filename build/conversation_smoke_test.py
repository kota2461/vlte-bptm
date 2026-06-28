"""Run an open conversation-routing smoke test.

This diagnostic intentionally does not read or evaluate the active PLM sealed
fixture. It measures the currently connected deterministic Semantic Adapter,
Processing Router, Core shadow bridge, and the frozen Legacy Router.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pattern_learning.trainer import RouterModel
from semantic_routing import (
    build_processing_plan,
    extract_semantic_packet,
    run_core_shadow,
)
from semantic_routing.reproducibility import reproducible_now_iso


MODEL_PATH = ROOT / "build" / "pattern_router_model.json"
OUTPUT_PATH = ROOT / "build" / "conversation_smoke_report.json"


@dataclass(frozen=True)
class ConversationCase:
    case_id: str
    category: str
    text: str
    expected_intent: str
    expected_class: str
    expected_core_mode: str


CASES: Tuple[ConversationCase, ...] = (
    ConversationCase(
        "conversation-01",
        "greeting",
        "こんにちは！今日は少し相談したいです。",
        "respond",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-02",
        "gratitude",
        "ありがとうございます。とても助かりました。",
        "respond",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-03",
        "explanation",
        "なぜキャッシュを使うと応答が速くなるのか説明してください。",
        "explain",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-04",
        "missing_information",
        "費用を計算してください。ただし利用人数はまだ伝えていません。",
        "clarify",
        "clarify",
        "horizontal",
    ),
    ConversationCase(
        "conversation-05",
        "summary",
        "この打ち合わせ内容を3行で要約してください。",
        "summarize",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-06",
        "current_verification",
        "現在の料金が正しいか、出典付きで確認してください。",
        "verify",
        "verified",
        "vertical",
    ),
    ConversationCase(
        "conversation-07",
        "implementation",
        "認証機能の実装計画を作ってください。",
        "build",
        "standard",
        "horizontal",
    ),
    ConversationCase(
        "conversation-08",
        "verify_then_build",
        "前提の妥当性を検証し、その上で実装計画を作ってください。",
        "build",
        "verified",
        "vertical",
    ),
    ConversationCase(
        "conversation-09",
        "alternatives",
        "障害を減らす複数の案を挙げて比較してください。",
        "explore",
        "deep",
        "hybrid",
    ),
    ConversationCase(
        "conversation-10",
        "mixed_language_compound",
        "このAPI仕様を確認し、その上でimplementation planを作ってください。",
        "build",
        "verified",
        "vertical",
    ),
    ConversationCase(
        "conversation-11",
        "legal_current",
        "現在の法律に照らして、この契約条項が妥当か確認してください。",
        "verify",
        "verified",
        "vertical",
    ),
    ConversationCase(
        "conversation-12",
        "negative_constraint",
        "コードは不要なので、移行の作業計画だけ作ってください。",
        "build",
        "standard",
        "horizontal",
    ),
    ConversationCase(
        "conversation-13",
        "indirect_explanation",
        "この挙動、どうしてこうなるんでしょうか。",
        "explain",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-14",
        "emotional_conversation",
        "プロジェクトがうまく進まず、少し不安になっています。",
        "respond",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-15",
        "summary_and_compare",
        "この議論を要約し、その上で選択肢のリスクを比較してください。",
        "summarize",
        "deep",
        "hybrid",
    ),
    ConversationCase(
        "conversation-16",
        "direct_fact",
        "Pythonで辞書を作る記号は何ですか。",
        "respond",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-17",
        "indirect_english_explanation",
        "Could you walk me through what makes this retry policy safe?",
        "explain",
        "economy",
        "horizontal",
    ),
    ConversationCase(
        "conversation-18",
        "ironic_exploration",
        "この完璧な案にも、念のためalternativesをいくつか挙げてください。",
        "explore",
        "deep",
        "hybrid",
    ),
)


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def main() -> None:
    legacy = RouterModel.load(MODEL_PATH)
    results = []
    semantic_passes = 0
    plan_passes = 0
    end_to_end_passes = 0

    for case in CASES:
        packet = extract_semantic_packet(case.text)
        plan = build_processing_plan(packet)
        shadow = run_core_shadow(case.text, packet, plan)
        legacy_prediction = legacy.predict(case.text)
        semantic_pass = packet.primary_intent == case.expected_intent
        plan_pass = (
            plan.processing_class == case.expected_class
            and plan.core_mode == case.expected_core_mode
        )
        end_to_end_pass = semantic_pass and plan_pass
        semantic_passes += semantic_pass
        plan_passes += plan_pass
        end_to_end_passes += end_to_end_pass
        pipeline = shadow.pipeline_state
        vertical = pipeline.get("vertical_stack")
        hybrid = pipeline.get("hybrid_stack_mesh")
        results.append(
            {
                "id": case.case_id,
                "category": case.category,
                "input": case.text,
                "expected": {
                    "intent": case.expected_intent,
                    "processing_class": case.expected_class,
                    "core_mode": case.expected_core_mode,
                },
                "actual": {
                    "intent": packet.primary_intent,
                    "semantic_confidence": packet.confidence,
                    "operations": list(packet.operations),
                    "information_state": packet.information_state.as_dict(),
                    "risk": packet.risk.as_dict(),
                    "processing_class": plan.processing_class,
                    "core_mode": plan.core_mode,
                    "reason_codes": list(plan.reason_codes),
                    "core_llm_mode": pipeline["llm_order"]["mode"],
                    "vertical_execution_order": (
                        vertical["execution_order"] if vertical else None
                    ),
                    "hybrid_next_dispatch": (
                        hybrid["next_dispatch"] if hybrid else None
                    ),
                    "legacy_raw_route": legacy_prediction.route,
                    "legacy_effective_route": (
                        legacy_prediction.effective_route
                    ),
                    "legacy_confidence": round(
                        legacy_prediction.confidence,
                        6,
                    ),
                },
                "checks": {
                    "semantic_intent": semantic_pass,
                    "processing_plan": plan_pass,
                    "end_to_end": end_to_end_pass,
                },
            }
        )

    report = {
        "schema_version": "conversation-smoke-report.v1",
        "generated_at": reproducible_now_iso(),
        "scope": (
            "deterministic Semantic Adapter -> Processing Router -> "
            "Core shadow; answer generation is not evaluated"
        ),
        "active_sealed_v2_read": False,
        "case_count": len(CASES),
        "metrics": {
            "semantic_intent_accuracy": _ratio(
                semantic_passes,
                len(CASES),
            ),
            "processing_plan_accuracy": _ratio(
                plan_passes,
                len(CASES),
            ),
            "end_to_end_route_accuracy": _ratio(
                end_to_end_passes,
                len(CASES),
            ),
            "passed": end_to_end_passes,
            "failed": len(CASES) - end_to_end_passes,
        },
        "results": results,
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
