"""Generate a weak-point debate topics file targeting the learned model's holes.

From build/model_vs_markers_harness_v1.json: explain 0/4 and English 0.57 (vs
Japanese 0.79) are the weak areas. These themes steer the Gemma/Qwen debate to
produce diverse, boundary-aware English/explain samples (which then go through
human review before any training use).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "debate_lab" / "topics_weakpoint_explain_english_v1.json"

DD = [
    "should_fire / should_not_fire minimal pair",
    "two paraphrase variants",
    "produce short self-contained user-utterance samples (not debate prose)",
    "positive-fire counterpart and a suppressor (false-positive) counterpart",
    "terminal action and operation order",
]


def t(id_, theme, intent, axes, focus, prio="high"):
    return {
        "id": id_, "priority": prio, "target_set": "weakpoint_explain_english_v1",
        "theme": theme, "axis_ids": axes, "recovery_focus": focus,
        "desired_discussion": DD, "training_status": "not_training_data",
        "human_review_required": True,
    }


TOPICS = [
    # English explain (the 0/4 hole), incl. confusable boundaries
    t("we-explain-01", "In English, a user asks why adding an index sped up a slow query. Route to explain (mechanism/cause), not respond (one-line fact) and not verify.", "explain", ["weakpoint", "english", "explain", "explain_vs_respond"], "explain recall (English)"),
    t("we-explain-02", "English: 'Help me understand how OAuth refresh tokens actually work.' Route to explain, not respond.", "explain", ["weakpoint", "english", "explain"], "explain recall (English)"),
    t("we-explain-03", "English colloquial: 'I don't really get why my recursion overflows.' Route to explain.", "explain", ["weakpoint", "english", "explain", "colloquial"], "explain recall (English colloquial)"),
    t("we-explain-04", "English: 'Walk me through what causes cache invalidation bugs.' explain, not build.", "explain", ["weakpoint", "english", "explain", "explain_vs_build"], "explain vs build boundary"),
    t("we-explain-05", "English: 'Explain what a p-value actually means here' vs 'What is a p-value' -- explain (meaning-in-context) vs respond (definition).", "explain", ["weakpoint", "english", "explain", "explain_vs_respond"], "explain vs respond minimal pair"),
    t("we-explain-06", "English: 'Why is my Docker image so large?' Route to explain (cause), not respond.", "explain", ["weakpoint", "english", "explain"], "explain recall (English)"),
    t("we-explain-07", "English: 'Can you explain the difference between TCP and UDP and why it matters' -- explain, even though 'difference' hints explore/compare.", "explain", ["weakpoint", "english", "explain", "explain_vs_explore"], "explain vs explore boundary"),
    t("we-explain-08", "English: 'I never really understood why floating point is imprecise.' explain.", "explain", ["weakpoint", "english", "explain", "colloquial"], "explain recall (English)"),
    t("we-explain-09", "English: 'How does gradient descent actually converge?' explain (how/why), not respond.", "explain", ["weakpoint", "english", "explain"], "explain recall (English)"),
    t("we-explain-10", "English: 'Explain why my unit test passes locally but fails in CI.' explain vs verify('check it').", "explain", ["weakpoint", "english", "explain", "explain_vs_verify"], "explain vs verify boundary"),
    t("we-explain-11", "English: 'What's the reasoning behind using a message queue here?' explain.", "explain", ["weakpoint", "english", "explain"], "explain recall (English)"),
    t("we-explain-12", "English: 'Give me the intuition behind backpropagation.' explain.", "explain", ["weakpoint", "english", "explain"], "explain recall (English)"),
    # English boundary cases that must NOT become explain (false-positive guard)
    t("we-bnd-01", "English: 'Is 0.1 + 0.2 == 0.3 in Python?' route respond/verify, NOT explain.", "respond", ["weakpoint", "english", "explain_false_positive", "respond"], "explain false-positive guard"),
    t("we-bnd-02", "English: 'Check whether this regex is correct.' verify, not explain.", "verify", ["weakpoint", "english", "verify", "explain_false_positive"], "verify vs explain"),
    t("we-bnd-03", "English: 'Compare REST vs GraphQL for my use case.' explore, not explain.", "explore", ["weakpoint", "english", "explore", "explain_false_positive"], "explore vs explain"),
    t("we-bnd-04", "English: 'What is a semaphore?' respond (definition), not explain (how-it-works).", "respond", ["weakpoint", "english", "respond", "respond_vs_explain"], "respond vs explain minimal pair"),
    t("we-bnd-05", "English: 'List a few ways to cache API responses.' explore, not explain.", "explore", ["weakpoint", "english", "explore"], "English explore recall"),
    t("we-bnd-06", "English: 'Tell me the capital of Australia.' respond.", "respond", ["weakpoint", "english", "respond"], "English respond recall"),
    # English multiple-intent / terminal (build/verify/explore + explain)
    t("we-multi-01", "English: 'Draft a rollout plan, then explain the risky step.' multiple_intents: build then explain terminal.", "build", ["weakpoint", "english", "multiple_intents", "explain", "operation_terminal"], "multi-intent build+explain"),
    t("we-multi-02", "English: 'Should I use Postgres or MongoDB? Explain your reasoning.' explore + explain.", "explore", ["weakpoint", "english", "multiple_intents", "explore", "explain"], "multi-intent explore+explain"),
    t("we-multi-03", "English: 'Verify these invoice totals and explain any discrepancy.' verify + explain, unverified_claim signal.", "verify", ["weakpoint", "english", "multiple_intents", "verify", "explain", "unverified_claim"], "multi-intent verify+explain"),
    # explain paraphrase + mixed/JA to broaden transfer
    t("we-para-01", "English paraphrase cluster for explain: 'why', 'how come', 'what's the reason', 'help me understand' -- all explain.", "explain", ["weakpoint", "english", "explain", "paraphrase"], "explain paraphrase transfer"),
    t("we-para-02", "Mixed ja/en: 'このアルゴリズムが速い理由を explain して' -- explain (mixed language).", "explain", ["weakpoint", "mixed_language", "explain"], "explain mixed-language"),
    t("we-para-03", "English: 'I'm confused about how JWT signing works.' explain (colloquial confusion cue).", "explain", ["weakpoint", "english", "explain", "colloquial"], "explain recall (English)"),
    t("we-para-04", "English boundary: 'break down why this approach scales better' = explain, vs 'break down the tasks' = build. Disambiguate 'break down'.", "explain", ["weakpoint", "english", "explain", "explain_vs_build"], "break_down disambiguation"),
    t("we-para-05", "English: 'what's going on when my container OOMs?' explain (cause).", "explain", ["weakpoint", "english", "explain", "colloquial"], "explain recall (English)"),
]


def main() -> None:
    doc = {
        "schema_version": "router-debate-topics.v1",
        "purpose": "Weak-point debate stock: explain intent (model 0/4) and English (0.57 vs ja 0.79). Diverse, boundary-aware English/explain themes to lift the learned model's weak areas. Human review required before any training use.",
        "created_at": "2026-01-01T00:00:00+00:00",
        "source_measurement": "build/model_vs_markers_harness_v1.json",
        "policy": {
            "sealed_text_used": False,
            "sealed_labels_used": False,
            "raw_debate_log_training_allowed": False,
            "human_review_required_before_fixture": True,
            "same_cycle_gate_use_allowed": False,
        },
        "recommended_run": {
            "target_set": "weakpoint_explain_english_v1",
            "rounds": 4,
            "expected_topics": len(TOPICS),
            "expected_turns": len(TOPICS) * 8,
            "output": "build/weakpoint_explain_english_debate_v1.json",
        },
        "summary": {
            "topic_count": len(TOPICS),
            "categories": {
                "english_explain": 12,
                "english_boundary_guard": 6,
                "english_multi_intent": 3,
                "explain_paraphrase_mixed": 4,
            },
        },
        "topics": TOPICS,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()} with {len(TOPICS)} topics")


if __name__ == "__main__":
    main()
