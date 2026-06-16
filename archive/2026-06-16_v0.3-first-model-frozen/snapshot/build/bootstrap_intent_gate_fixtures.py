"""Author + freeze the intent-gate fixtures and SHA registry.

Both suites are graded on route() (the real deployment surface = hybrid:
markers + the gated learned layer):
  * foundation_anchors  -- unambiguous canonical cases across all 7 intents;
  * hybrid_regression   -- verify_then_build safety + no-match cases where
                           the learned layer (not markers) is the decider.
We author cases, then keep only those the candidate currently routes
correctly — the router foundation-suite bootstrap logic ("competencies the
model has and must keep"). All cases are disjoint from the campaign.
"""

import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.intent_model import IntentModel
from semantic_routing.adapter import route
from semantic_routing.intent_deployment import (
    FOUNDATION_SUITE_SCHEMA, HYBRID_REGRESSION_SCHEMA, DEFAULT_CANDIDATE,
)
from pattern_learning.deployment import file_sha256

CANDIDATE = ROOT / DEFAULT_CANDIDATE
FOUNDATION_OUT = ROOT / "tests" / "fixtures" / "intent_foundation_anchors_v1.json"
HYBRID_OUT = ROOT / "tests" / "fixtures" / "intent_hybrid_regression_v1.json"
REGISTRY_OUT = ROOT / "tests" / "fixtures" / "intent_gate_fixture_registry.json"

# --- authored unambiguous canonical anchors (predict-based) ---------------
FOUNDATION = [
    ("こんにちは、今日はいい天気ですね", "respond"),
    ("ありがとう、とても助かりました", "respond"),
    ("おはよう！よく眠れた？", "respond"),
    ("了解です、また連絡しますね", "respond"),
    ("Hi there, how is it going?", "respond"),
    ("なぜ鉄は錆びるのか説明して", "explain"),
    ("光合成の仕組みを教えて", "explain"),
    ("どうして月は満ち欠けするのか教えて", "explain"),
    ("エンジンが動く原理を説明してほしい", "explain"),
    ("Explain why the ocean looks blue", "explain"),
    ("引っ越しの段取りを作って", "build"),
    ("新人向けの研修プランを作成して", "build"),
    ("デプロイ手順のチェックリストを用意して", "build"),
    ("会議のアジェンダのドラフトを書いて", "build"),
    ("Make a step-by-step plan for the launch", "build"),
    ("この計算が正しいか確認して: 8×7=54", "verify"),
    ("この見積もりが妥当か検証して", "verify"),
    ("合計金額が合っているか確かめて", "verify"),
    ("この文章に誤りがないかチェックして", "verify"),
    ("Check whether this statement is accurate", "verify"),
    ("この記事を3行で要約して", "summarize"),
    ("議事録の要点をまとめて", "summarize"),
    ("長い報告書を短くまとめて", "summarize"),
    ("この章の概要を簡潔にまとめて", "summarize"),
    ("Summarize the key points of this report", "summarize"),
    ("他にどんなやり方があるか挙げて", "explore"),
    ("選択肢をいくつか比較して提案して", "explore"),
    ("別のアプローチも検討したい", "explore"),
    ("代替案をいくつか出してほしい", "explore"),
    ("What are some different options we could consider?", "explore"),
    # clarify is the abstention/safety class -- triggered by explicit
    # missing-information markers (see baseline INTENT_MARKERS["clarify"]).
    ("詳細はまだ伝えていませんが、進めてください", "clarify"),
    ("条件が不足しています。先に質問してください", "clarify"),
    ("Some details are not provided; ask me first", "clarify"),
]

# --- hybrid-regression anchors (route-based: safety + no-match) -----------
HYBRID = [
    ("こんにちは、調子はどう？", "respond"),
    ("なぜ空は青いのか教えて", "explain"),
    ("セットアップ手順を作って", "build"),
    ("この計算が合っているか確認して: 12 + 7 = 20", "verify"),
    ("この記事を要約して", "summarize"),
    ("他の解き方も教えて", "explore"),
    # verify_then_build safety: verification is a prerequisite, build is primary
    ("計算を検算してから手順書を作って", "build"),
    ("仕様が正しいか確認したうえで実装プランを作成して", "build"),
    # no-match anchors: markers stay silent so the learned layer decides
    ("最近ずっと忙しくて疲れがたまっている", "respond"),
    ("週末は家でゆっくり過ごすつもりです", "respond"),
]

MIN_PER_INTENT_FOUNDATION = 2


def main() -> None:
    model = IntentModel.load(CANDIDATE)

    # filter foundation by route() correctness (deployment surface)
    kept_f, dropped_f = [], []
    for text, intent in FOUNDATION:
        got = route(text, intent_model=model).packet.primary_intent
        (kept_f if got == intent else dropped_f).append(
            {"input": text, "intent": intent, "predicted": got})
    print("FOUNDATION kept:", len(kept_f), "/", len(FOUNDATION))
    for d in dropped_f:
        print("  dropped:", d["intent"], "->", d["predicted"], "|", d["input"])

    # filter hybrid by route() correctness
    kept_h, dropped_h = [], []
    for text, intent in HYBRID:
        got = route(text, intent_model=model).packet.primary_intent
        (kept_h if got == intent else dropped_h).append(
            {"input": text, "intent": intent, "predicted": got})
    print("HYBRID kept:", len(kept_h), "/", len(HYBRID))
    for d in dropped_h:
        print("  dropped:", d["intent"], "->", d["predicted"], "|", d["input"])

    f_counts = Counter(c["intent"] for c in kept_f)
    h_counts = Counter(c["intent"] for c in kept_h)
    print("foundation by_intent:", dict(sorted(f_counts.items())))
    print("hybrid by_intent:", dict(sorted(h_counts.items())))

    weak = {i: f_counts.get(i, 0) for i in
            ["respond", "explain", "build", "verify", "summarize", "explore", "clarify"]
            if f_counts.get(i, 0) < MIN_PER_INTENT_FOUNDATION}
    if weak:
        print("WARNING: foundation intents below min:", weak)

    # write fixtures (cases only: input + intent)
    FOUNDATION_OUT.write_text(json.dumps({
        "schema_version": FOUNDATION_SUITE_SCHEMA,
        "description": "Unambiguous per-intent anchors; raw IntentModel.predict must match. Disjoint from the measurement campaign.",
        "cases": [{"input": c["input"], "intent": c["intent"]} for c in kept_f],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    HYBRID_OUT.write_text(json.dumps({
        "schema_version": HYBRID_REGRESSION_SCHEMA,
        "description": "route() primary_intent must match; marker-dominated incl. verify_then_build safety. Disjoint from the campaign.",
        "cases": [{"input": c["input"], "intent": c["intent"]} for c in kept_h],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # registry with SHAs + minimum counts (per-intent floors from what we froze)
    registry = {
        "schema_version": "gate-fixture-registry.v1",
        "description": "Frozen fixtures for the intent-model deployment gate.",
        "fixtures": {
            FOUNDATION_OUT.name: {
                "version": "v1",
                "role": "intent_foundation_anchor",
                "sha256": file_sha256(FOUNDATION_OUT),
                "min_case_count": len(kept_f),
                "min_intent_counts": dict(sorted(f_counts.items())),
            },
            HYBRID_OUT.name: {
                "version": "v1",
                "role": "intent_hybrid_regression",
                "sha256": file_sha256(HYBRID_OUT),
                "min_case_count": len(kept_h),
                "min_intent_counts": dict(sorted(h_counts.items())),
            },
        },
    }
    REGISTRY_OUT.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nwrote:")
    print(" ", FOUNDATION_OUT.relative_to(ROOT), file_sha256(FOUNDATION_OUT)[:12])
    print(" ", HYBRID_OUT.relative_to(ROOT), file_sha256(HYBRID_OUT)[:12])
    print(" ", REGISTRY_OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
