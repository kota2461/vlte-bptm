"""Language-basics thinking-pattern curriculum for the review queue.

Covers Japanese and English greetings plus basic sentence understanding
(subject/predicate, tense, politeness, translation, grammar checking).
Entries are inserted as *pending* candidates only; approval and training
remain explicit human actions, matching the Pattern Lab boundary.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://language-v1"
CURRICULUM_REVISION = "1"

LEVELS = (
    "greetings_ja",
    "greetings_en",
    "basic_ja",
    "basic_en",
)


@dataclass(frozen=True)
class LanguagePattern:
    level: str
    text: str
    route: str
    operators: Tuple[str, ...]
    rating: int
    answer_candidates: Tuple[str, ...] = ()


LANGUAGE_CURRICULUM: Tuple[LanguagePattern, ...] = (
    # 日本語の挨拶（直接応答）
    LanguagePattern(
        "greetings_ja",
        "こんにちは",
        "respond",
        ("definition",),
        5,
        ("こんにちは。今日はどんなご用件ですか",),
    ),
    LanguagePattern(
        "greetings_ja",
        "おはようございます",
        "respond",
        ("definition",),
        5,
        ("おはようございます。良い一日になりますように",),
    ),
    LanguagePattern(
        "greetings_ja",
        "こんばんは",
        "respond",
        ("definition",),
        4,
        ("こんばんは。お疲れさまです",),
    ),
    LanguagePattern(
        "greetings_ja",
        "ありがとうございます",
        "respond",
        ("definition",),
        5,
        ("どういたしまして",),
    ),
    LanguagePattern(
        "greetings_ja",
        "さようなら、またね",
        "respond",
        ("definition",),
        4,
        ("さようなら。また会いましょう",),
    ),
    LanguagePattern(
        "greetings_ja",
        "はじめまして、よろしくお願いします",
        "respond",
        ("definition",),
        5,
        ("はじめまして。こちらこそよろしくお願いします",),
    ),
    LanguagePattern(
        "greetings_ja",
        "お元気ですか",
        "respond",
        ("definition",),
        4,
        ("はい、元気です。あなたはいかがですか",),
    ),
    LanguagePattern(
        "greetings_ja",
        "おやすみなさい",
        "respond",
        ("definition",),
        4,
        ("おやすみなさい。良い夢を",),
    ),
    LanguagePattern(
        "greetings_ja",
        "久しぶりですね、元気でしたか",
        "respond",
        ("definition",),
        4,
        ("お久しぶりです。おかげさまで元気です",),
    ),
    LanguagePattern(
        "greetings_ja",
        "今日は天気がいいですね",
        "respond",
        ("definition",),
        4,
        ("本当にいい天気ですね",),
    ),
    # 英語の挨拶（直接応答）
    LanguagePattern(
        "greetings_en",
        "Hello!",
        "respond",
        ("definition",),
        5,
        ("Hello! How can I help you today?",),
    ),
    LanguagePattern(
        "greetings_en",
        "Good morning!",
        "respond",
        ("definition",),
        5,
        ("Good morning! Have a nice day.",),
    ),
    LanguagePattern(
        "greetings_en",
        "Good evening, how are you?",
        "respond",
        ("definition",),
        4,
        ("Good evening! I'm doing well, thank you.",),
    ),
    LanguagePattern(
        "greetings_en",
        "Thank you so much!",
        "respond",
        ("definition",),
        5,
        ("You're welcome!",),
    ),
    LanguagePattern(
        "greetings_en",
        "Nice to meet you.",
        "respond",
        ("definition",),
        5,
        ("Nice to meet you too.",),
    ),
    LanguagePattern(
        "greetings_en",
        "See you later!",
        "respond",
        ("definition",),
        4,
        ("See you! Take care.",),
    ),
    LanguagePattern(
        "greetings_en",
        "How are you doing today?",
        "respond",
        ("definition",),
        4,
        ("I'm doing well, thanks. How about you?",),
    ),
    LanguagePattern(
        "greetings_en",
        "Long time no see!",
        "respond",
        ("definition",),
        4,
        ("It's been a while! Good to see you.",),
    ),
    # 日本語の基礎文理解
    LanguagePattern(
        "basic_ja",
        "「猫が魚を食べた」の主語と述語を見つけてください",
        "respond",
        ("decomposition",),
        5,
        ("主語: 猫が、述語: 食べた",),
    ),
    LanguagePattern(
        "basic_ja",
        "「は」と「が」の使い方の違いを比較してください",
        "respond",
        ("comparison",),
        5,
    ),
    LanguagePattern(
        "basic_ja",
        "敬語とは何か説明してください",
        "respond",
        ("definition",),
        5,
    ),
    LanguagePattern(
        "basic_ja",
        "「雨が降ったので、試合は中止になった」の因果関係を説明してください",
        "respond",
        ("causal_relation",),
        5,
    ),
    LanguagePattern(
        "basic_ja",
        "「行く」の丁寧語は何ですか",
        "respond",
        ("equivalence", "definition"),
        4,
        ("行きます",),
    ),
    LanguagePattern(
        "basic_ja",
        "ひらがなとカタカナの使い分けを説明してください",
        "respond",
        ("comparison", "definition"),
        4,
    ),
    LanguagePattern(
        "basic_ja",
        "この文章のあいまいな表現について確認の質問をしてください",
        "clarify",
        ("uncertainty", "condition"),
        4,
    ),
    LanguagePattern(
        "basic_ja",
        "この段落を一文に要約してください",
        "summarize",
        ("decomposition",),
        5,
    ),
    LanguagePattern(
        "basic_ja",
        "この文の敬語の使い方が正しいか確認してください",
        "verify",
        ("verification",),
        5,
    ),
    LanguagePattern(
        "basic_ja",
        "同じ意味になる別の言い方をいくつか考えてください",
        "explore",
        ("equivalence", "comparison"),
        5,
    ),
    LanguagePattern(
        "basic_ja",
        "わかりやすい文章を書く手順を組み立ててください",
        "build",
        ("sequence",),
        4,
    ),
    LanguagePattern(
        "basic_ja",
        "文の意味が二通りに読めるときは、どちらの意味か質問してください",
        "clarify",
        ("uncertainty",),
        4,
    ),
    # 英語の基礎文理解
    LanguagePattern(
        "basic_en",
        "Translate \"Good morning\" into Japanese.",
        "respond",
        ("equivalence",),
        5,
        ("おはようございます",),
    ),
    LanguagePattern(
        "basic_en",
        "What does the word \"apple\" mean?",
        "respond",
        ("definition",),
        5,
        ("りんご",),
    ),
    LanguagePattern(
        "basic_en",
        "Find the subject and the verb in \"The cat eats fish\".",
        "respond",
        ("decomposition",),
        5,
        ("subject: The cat, verb: eats",),
    ),
    LanguagePattern(
        "basic_en",
        "Compare the present tense and the past tense in English.",
        "respond",
        ("comparison",),
        5,
    ),
    LanguagePattern(
        "basic_en",
        "Explain what the be-verb is.",
        "respond",
        ("definition",),
        4,
    ),
    LanguagePattern(
        "basic_en",
        "\"I went to school yesterday\" を日本語に訳してください",
        "respond",
        ("equivalence",),
        4,
        ("私は昨日学校へ行きました",),
    ),
    LanguagePattern(
        "basic_en",
        "英語のbe動詞の活用を順番に挙げてください",
        "respond",
        ("sequence",),
        4,
        ("am / is / are / was / were / been",),
    ),
    LanguagePattern(
        "basic_en",
        "Verify whether this sentence is grammatically correct: \"He go to school.\"",
        "verify",
        ("verification",),
        5,
        ("Incorrect. \"He goes to school.\"",),
    ),
    LanguagePattern(
        "basic_en",
        "Summarize this English paragraph in one sentence.",
        "summarize",
        ("decomposition",),
        5,
    ),
    LanguagePattern(
        "basic_en",
        "Please ask me questions if my English sentence is ambiguous.",
        "clarify",
        ("uncertainty", "condition"),
        4,
    ),
    LanguagePattern(
        "basic_en",
        "Suggest several different ways to say \"thank you\".",
        "explore",
        ("comparison", "equivalence"),
        5,
    ),
    LanguagePattern(
        "basic_en",
        "Build a step-by-step plan for writing a short English essay.",
        "build",
        ("sequence", "decomposition"),
        4,
    ),
    # explore Route 強化（弱点#1 / 2026-06-11）。表現の言い換え・代替案の
    # 発散的な指示を respond から切り分けるための承認候補。
    LanguagePattern(
        "basic_ja",
        "「ありがとう」の別の言い方をいくつか挙げてください",
        "explore",
        ("comparison", "equivalence"),
        4,
    ),
    LanguagePattern(
        "basic_ja",
        "この文をもっと丁寧な表現に言い換える案を複数考えてください",
        "explore",
        ("comparison", "equivalence"),
        4,
    ),
    LanguagePattern(
        "basic_en",
        "List several alternative ways to greet someone in English.",
        "explore",
        ("comparison",),
        4,
    ),
    LanguagePattern(
        "basic_en",
        "Brainstorm different ways to rephrase this sentence.",
        "explore",
        ("comparison", "equivalence"),
        4,
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="Language basics thinking-pattern curriculum v1",
        url=CURRICULUM_URL,
        revision_id=CURRICULUM_REVISION,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        license_name="project-curriculum",
        attribution="Thought State Register",
        text="",
        metadata={"levels": list(LEVELS)},
    )


def curriculum_drafts() -> List[PatternDraft]:
    drafts: List[PatternDraft] = []
    for pattern in LANGUAGE_CURRICULUM:
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
                    "goals": [f"language::{pattern.level}"],
                    "constraints": [],
                    "uncertainty": (
                        ["needs missing conditions"]
                        if pattern.route == "clarify"
                        else []
                    ),
                    "operation": pattern.operators[0],
                    "candidates": list(pattern.answer_candidates),
                    "level": pattern.level,
                },
                confidence=min(0.95, 0.55 + 0.08 * pattern.rating),
            )
        )
    return drafts
