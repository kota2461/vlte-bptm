"""Specification-derived route-boundary contrasts, revision 3.

Revision 3 (2026-06-18): targets the weak boundaries surfaced by
``docs/PATTERN_BOUNDARY_V2_UNTRAINED_ACCURACY.md`` (2026-06-11). That audit
found ``build`` recall 0.33, ``verify`` recall 0.17, the ``build_respond``
boundary at 0.42 (0/6 pairs both correct), ``clarify_verify`` at 0.42, and
English accuracy at 0.25 versus Japanese 0.72. The main confusions were
``build -> respond`` (5), ``verify -> respond`` (3), and ``verify -> clarify``
(2): ``build`` and ``verify`` intent kept collapsing into ``respond``.

This revision adds contrast pairs on exactly those boundaries, in both
Japanese and English, and inherits the revision-2 lesson: do not let a
surface marker carry the label. Negation ("〜せず" / "without ...") is spread
across ``build`` and ``verify`` prompts, ``build`` requests appear in
imperative, polite-question, and declarative forms, and ``respond`` prompts
use positive phrasing on the same buildable topic so only the intent — not a
lexical tell — separates the routes.

The prompts are independently authored from the project's route definitions.
They contain no copied source text, model responses, hidden reasoning, or
teacher logits. Seeding creates pending candidates only and requires human
approval before any training.
"""

from datetime import datetime, timezone
from typing import List, Tuple

from .boundary_curriculum_v2 import ContrastPrompt
from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument

CURRICULUM_URL = "curriculum://route-boundaries-v3-round1"
CURRICULUM_REVISION = "3"
AUTHORING_METHOD = "specification-derived-synthetic"
AUTHORING_MODELS = {
    "round1_draft": "claude-opus-4-8",
}


BOUNDARY_CURRICULUM_V3: Tuple[ContrastPrompt, ...] = (
    # ---- build vs respond (worst boundary: 0/6 pairs) ----------------------
    ContrastPrompt(
        "build_respond",
        "br-cache-ja",
        "ja",
        "simple",
        "ja-respond-opinion",
        "このキャッシュ層は設計として筋がいいと思う。良さの理由を一緒に言語化したい",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-cache-ja",
        "ja",
        "simple",
        "ja-build-imperative",
        "このキャッシュ層を実装してください",
        "build",
        ("sequence",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-cache-ja",
        "ja",
        "hard",
        "ja-build-question",
        "キャッシュ層、コードに起こしてもらえる?",
        "build",
        ("sequence",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-form-ja",
        "ja",
        "simple",
        "ja-respond-opinion",
        "入力フォームの使い勝手、今のままでも気持ちよく使えていると思う",
        "respond",
        ("comparison",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-form-ja",
        "ja",
        "hard",
        "ja-build-negation",
        "入力フォームは一から書かず、既存の部品を組み合わせて用意して",
        "build",
        ("decomposition",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-naming-ja",
        "ja",
        "simple",
        "ja-respond-opinion",
        "この命名、意味はちゃんと伝わると思う。気に入っているよ",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-naming-ja",
        "ja",
        "simple",
        "ja-build-imperative",
        "命名規則に沿って全体をリネームして",
        "build",
        ("sequence",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-auth-en",
        "en",
        "simple",
        "en-respond-opinion",
        "I think this auth design is solid; help me put into words why it works.",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-auth-en",
        "en",
        "simple",
        "en-build-imperative",
        "Implement this authentication flow.",
        "build",
        ("sequence",),
    ),
    ContrastPrompt(
        "build_respond",
        "br-auth-en",
        "en",
        "hard",
        "en-build-question",
        "Could you write the authentication flow for this module?",
        "build",
        ("sequence",),
    ),
    # ---- respond vs verify (verify recall 0.17) ----------------------------
    ContrastPrompt(
        "respond_verify",
        "rv-regex-ja",
        "ja",
        "simple",
        "ja-respond-opinion",
        "正規表現って読みにくいよね。読みやすく保つコツがあれば聞きたい",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-regex-ja",
        "ja",
        "simple",
        "ja-verify-check",
        "この正規表現が想定パターンを取りこぼさないか確認して",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-migration-ja",
        "ja",
        "simple",
        "ja-respond-opinion",
        "このマイグレーション方針、考え方としては腑に落ちた",
        "respond",
        ("causal_relation",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-migration-ja",
        "ja",
        "hard",
        "ja-verify-question",
        "このマイグレーション、ロールバック条件をちゃんと満たしてる?",
        "verify",
        ("condition",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-migration-ja",
        "ja",
        "simple",
        "ja-verify-negation",
        "このマイグレーションでデータ欠損が起きないか検証して",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-query-en",
        "en",
        "simple",
        "en-respond-opinion",
        "This query is hard to read; any tips to keep it clean would be welcome.",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-query-en",
        "en",
        "simple",
        "en-verify-check",
        "Check whether this query ever returns duplicate rows.",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-index-en",
        "en",
        "simple",
        "en-respond-opinion",
        "Indexes always confuse me, honestly.",
        "respond",
        ("definition",),
    ),
    ContrastPrompt(
        "respond_verify",
        "rv-index-en",
        "en",
        "hard",
        "en-verify-negation",
        "Confirm this index does not miss the slow query's filter columns.",
        "verify",
        ("verification",),
    ),
    # ---- clarify vs verify (boundary 0.42, verify->clarify leaks) ----------
    ContrastPrompt(
        "clarify_verify",
        "cv-check-ja",
        "ja",
        "simple",
        "ja-clarify-uncertainty",
        "「チェックして」だけだと、何を基準に見ればいいかが決まらない",
        "clarify",
        ("uncertainty",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-check-ja",
        "ja",
        "simple",
        "ja-verify-check",
        "受け入れ条件を満たしているか点検して",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-spec-ja",
        "ja",
        "hard",
        "ja-clarify-uncertainty",
        "どの版の仕様を正とするか分からないと、整合の判断はできない",
        "clarify",
        ("uncertainty",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-spec-ja",
        "ja",
        "simple",
        "ja-verify-check",
        "実装が最新仕様と矛盾しないか確認して",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-done-en",
        "en",
        "simple",
        "en-clarify-uncertainty",
        "Without the acceptance criteria, I cannot tell what 'check this' should mean.",
        "clarify",
        ("uncertainty",),
    ),
    ContrastPrompt(
        "clarify_verify",
        "cv-done-en",
        "en",
        "simple",
        "en-verify-check",
        "Confirm the change meets the listed acceptance criteria.",
        "verify",
        ("verification",),
    ),
    # ---- build vs verify (intent separation insufficient) ------------------
    ContrastPrompt(
        "build_verify",
        "bv-validation-ja",
        "ja",
        "simple",
        "ja-build-imperative",
        "入力バリデーションを追加して",
        "build",
        ("sequence",),
    ),
    ContrastPrompt(
        "build_verify",
        "bv-validation-ja",
        "ja",
        "simple",
        "ja-verify-check",
        "入力バリデーションに抜けがないか点検して",
        "verify",
        ("verification",),
    ),
    ContrastPrompt(
        "build_verify",
        "bv-retry-ja",
        "ja",
        "simple",
        "ja-build-imperative",
        "リトライ処理を実装して",
        "build",
        ("sequence",),
    ),
    ContrastPrompt(
        "build_verify",
        "bv-retry-ja",
        "ja",
        "hard",
        "ja-verify-question",
        "リトライ処理、無限ループに陥らない作りになってる?",
        "verify",
        ("condition", "verification"),
    ),
    ContrastPrompt(
        "build_verify",
        "bv-ratelimit-en",
        "en",
        "simple",
        "en-build-imperative",
        "Add a rate limiter to this endpoint.",
        "build",
        ("sequence",),
    ),
    ContrastPrompt(
        "build_verify",
        "bv-ratelimit-en",
        "en",
        "hard",
        "en-verify-negation",
        "Check that the rate limiter does not block legitimate traffic.",
        "verify",
        ("condition", "verification"),
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="Original route boundary contrast curriculum v3 round 1",
        url=CURRICULUM_URL,
        revision_id=CURRICULUM_REVISION,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        license_name="project-original-synthetic",
        attribution="Thought State Register project",
        text="",
        metadata={
            "authoring_method": AUTHORING_METHOD,
            "authoring_models": dict(AUTHORING_MODELS),
            "ai_assisted_authoring": True,
            "teacher_model_outputs_used": False,
            "copied_source_text_used": False,
            "hidden_reasoning_used": False,
            "approval_required": True,
            "revision_note": (
                "revision 3 targets the build/verify-vs-respond and "
                "clarify-vs-verify weak boundaries and the English gap from "
                "the 2026-06-11 untrained accuracy audit; negation markers are "
                "spread across build/verify so no surface tell carries a label"
            ),
            "boundaries": sorted(
                {pattern.boundary for pattern in BOUNDARY_CURRICULUM_V3}
            ),
            "contrast_group_field": "contrast_group",
            "template_id_field": "template_id",
        },
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for pattern in BOUNDARY_CURRICULUM_V3:
        if pattern.route not in ROUTES:
            raise ValueError(f"unknown route: {pattern.route}")
        unknown = sorted(set(pattern.operators) - set(OPERATORS))
        if unknown:
            raise ValueError(f"unknown operators: {', '.join(unknown)}")
        drafts.append(
            PatternDraft(
                input_text=pattern.text,
                suggested_route=pattern.route,
                suggested_operators=list(pattern.operators),
                thought_form={
                    "facts": [pattern.text],
                    "goals": [f"distinguish {pattern.boundary}"],
                    "constraints": [
                        "route intent only",
                        "human approval required",
                    ],
                    "uncertainty": [],
                    "operation": pattern.operators[0],
                    "candidates": [],
                    "boundary": pattern.boundary,
                    "contrast_group": pattern.contrast_group,
                    "language": pattern.language,
                    "difficulty": pattern.difficulty,
                    "template_id": pattern.template_id,
                    "curriculum_revision": CURRICULUM_REVISION,
                    "authoring_method": AUTHORING_METHOD,
                    "ai_assisted_authoring": True,
                    "teacher_output_used": False,
                    "copied_source_text_used": False,
                },
                confidence=0.9,
            )
        )
    return drafts
