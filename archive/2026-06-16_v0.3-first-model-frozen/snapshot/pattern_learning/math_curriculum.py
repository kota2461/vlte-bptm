"""Mathematical thinking-pattern curriculum for the review queue.

Covers number sense, addition with same-answer variations, elementary
arithmetic, junior-high algebra, and Japanese high-school mathematics.
Entries are inserted as *pending* candidates only; approval and training
remain explicit human actions, matching the Pattern Lab boundary.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

from .models import OPERATORS, ROUTES, PatternDraft, SourceDocument


CURRICULUM_URL = "curriculum://math-v1"
CURRICULUM_REVISION = "1"

LEVELS = (
    "number_sense",
    "addition",
    "elementary",
    "junior_high",
    "high_school",
)


@dataclass(frozen=True)
class MathPattern:
    level: str
    text: str
    route: str
    operators: Tuple[str, ...]
    rating: int
    answer_candidates: Tuple[str, ...] = ()


MATH_CURRICULUM: Tuple[MathPattern, ...] = (
    # Level 1: 基礎的な数の理解
    MathPattern(
        "number_sense",
        "「7」という数字が表す量を説明してください",
        "respond",
        ("definition",),
        5,
    ),
    MathPattern(
        "number_sense",
        "0という数の意味を説明してください",
        "respond",
        ("definition",),
        5,
    ),
    MathPattern(
        "number_sense",
        "5と8はどちらが大きいですか",
        "respond",
        ("comparison",),
        5,
        ("8",),
    ),
    MathPattern(
        "number_sense",
        "12と21の大小を比較してください",
        "respond",
        ("comparison",),
        5,
        ("21",),
    ),
    MathPattern(
        "number_sense",
        "1から10まで順番に数えてください",
        "respond",
        ("sequence",),
        5,
    ),
    MathPattern(
        "number_sense",
        "23の十の位の数字は何ですか",
        "respond",
        ("definition", "decomposition"),
        5,
        ("2",),
    ),
    MathPattern(
        "number_sense",
        "偶数とは何か定義してください",
        "respond",
        ("definition",),
        5,
    ),
    MathPattern(
        "number_sense",
        "3, 6, 9, 12 の次に来る数を答えてください",
        "respond",
        ("sequence",),
        4,
        ("15",),
    ),
    # Level 2: 加算（同回答バリエーションを含む。答え8の言い換え・別構成）
    MathPattern(
        "addition",
        "3+5を計算してください",
        "respond",
        ("calculation",),
        5,
        ("8",),
    ),
    MathPattern(
        "addition",
        "3に5を足すといくつになりますか",
        "respond",
        ("calculation",),
        4,
        ("8",),
    ),
    MathPattern(
        "addition",
        "3たす5の答えを教えてください",
        "respond",
        ("calculation",),
        4,
        ("8",),
    ),
    MathPattern(
        "addition",
        "5+3はいくつですか",
        "respond",
        ("calculation", "equivalence"),
        4,
        ("8",),
    ),
    MathPattern(
        "addition",
        "りんごが3個、みかんが5個あります。果物は全部で何個ですか",
        "respond",
        ("calculation", "decomposition"),
        4,
        ("8個",),
    ),
    MathPattern(
        "addition",
        "6+2を計算してください",
        "respond",
        ("calculation",),
        4,
        ("8",),
    ),
    MathPattern(
        "addition",
        "4+4の答えはいくつですか",
        "respond",
        ("calculation", "equivalence"),
        4,
        ("8",),
    ),
    MathPattern(
        "addition",
        "7+1はいくつになりますか",
        "respond",
        ("calculation",),
        4,
        ("8",),
    ),
    MathPattern(
        "addition",
        "答えが8になる足し算の組み合わせをいくつか挙げてください",
        "explore",
        ("comparison", "calculation"),
        5,
        ("3+5", "5+3", "6+2", "4+4", "7+1"),
    ),
    MathPattern(
        "addition",
        "3+5=9が正しいかどうか確認してください",
        "verify",
        ("verification", "calculation"),
        5,
        ("誤り。3+5=8",),
    ),
    MathPattern(
        "addition",
        "3+5と5+3の結果が等しい理由を説明してください",
        "respond",
        ("equivalence", "causal_relation"),
        5,
    ),
    MathPattern(
        "addition",
        "9+4のような繰り上がりのある足し算の手順を説明してください",
        "respond",
        ("sequence", "calculation"),
        4,
    ),
    MathPattern(
        "addition",
        "ある数に5を足すと8になります。ある数を求めてください",
        "respond",
        ("calculation", "condition"),
        4,
        ("3",),
    ),
    MathPattern(
        "addition",
        "数に何かを足すといくつになりますか",
        "clarify",
        ("condition", "uncertainty"),
        4,
    ),
    # Level 3: 小学校算数
    MathPattern(
        "elementary",
        "9-4を計算してください",
        "respond",
        ("calculation",),
        5,
        ("5",),
    ),
    MathPattern(
        "elementary",
        "7×6を計算してください",
        "respond",
        ("calculation",),
        5,
        ("42",),
    ),
    MathPattern(
        "elementary",
        "56÷8を計算してください",
        "respond",
        ("calculation",),
        5,
        ("7",),
    ),
    MathPattern(
        "elementary",
        "1/2と1/3を通分して大小を比較してください",
        "respond",
        ("comparison", "calculation"),
        5,
        ("1/2 > 1/3",),
    ),
    MathPattern(
        "elementary",
        "0.5と1/2が等しいことを確認してください",
        "verify",
        ("verification", "equivalence"),
        5,
    ),
    MathPattern(
        "elementary",
        "240円の品物を3割引で買うといくらになりますか",
        "respond",
        ("calculation", "decomposition"),
        4,
        ("168円",),
    ),
    MathPattern(
        "elementary",
        "時速4kmで2時間歩くと何km進みますか",
        "respond",
        ("calculation",),
        4,
        ("8km",),
    ),
    MathPattern(
        "elementary",
        "太郎は鉛筆を12本持っていて、友達に何本かあげました。残りは何本ですか",
        "clarify",
        ("condition", "uncertainty"),
        5,
    ),
    MathPattern(
        "elementary",
        "この計算問題の解き方を順序立てて整理し、手順書を作ってください",
        "build",
        ("sequence", "decomposition"),
        4,
    ),
    # Level 4: 中学校数学
    MathPattern(
        "junior_high",
        "一次方程式 2x+3=11 を解いてください",
        "respond",
        ("calculation", "sequence"),
        5,
        ("x=4",),
    ),
    MathPattern(
        "junior_high",
        "連立方程式 x+y=10, x-y=2 を解いてください",
        "respond",
        ("calculation", "decomposition"),
        5,
        ("x=6, y=4",),
    ),
    MathPattern(
        "junior_high",
        "(x+2)(x-3) を展開してください",
        "respond",
        ("calculation",),
        4,
        ("x^2-x-6",),
    ),
    MathPattern(
        "junior_high",
        "x^2-5x+6 を因数分解してください",
        "respond",
        ("calculation", "decomposition"),
        5,
        ("(x-2)(x-3)",),
    ),
    MathPattern(
        "junior_high",
        "三角形の内角の和が180度になることを証明してください",
        "verify",
        ("verification", "causal_relation"),
        5,
    ),
    MathPattern(
        "junior_high",
        "関数 y=2x+1 とはどのような対応関係か説明してください",
        "respond",
        ("definition", "causal_relation"),
        4,
    ),
    MathPattern(
        "junior_high",
        "サイコロを1回振って偶数が出る確率を求めてください",
        "respond",
        ("calculation", "uncertainty"),
        5,
        ("1/2",),
    ),
    MathPattern(
        "junior_high",
        "√2が無理数であることの証明を検証してください",
        "verify",
        ("verification", "causal_relation"),
        5,
    ),
    MathPattern(
        "junior_high",
        "鶴亀算の文章題を連立方程式で解く手順を設計してください",
        "build",
        ("sequence", "decomposition"),
        5,
    ),
    MathPattern(
        "junior_high",
        "比例と反比例の違いを比較して説明してください",
        "respond",
        ("comparison", "definition"),
        4,
    ),
    MathPattern(
        "junior_high",
        "この方程式を解いてください",
        "clarify",
        ("condition",),
        4,
    ),
    # Level 5: 高等学校数学（数I/A/II/B/III相当）
    MathPattern(
        "high_school",
        "二次関数 y=x^2-4x+3 の頂点と最小値を求めてください",
        "respond",
        ("calculation", "decomposition"),
        5,
        ("頂点(2,-1)、最小値-1",),
    ),
    MathPattern(
        "high_school",
        "二次方程式 x^2+2x+k=0 が実数解を持つkの条件を求めてください",
        "respond",
        ("condition", "calculation"),
        5,
        ("k<=1",),
    ),
    MathPattern(
        "high_school",
        "sin30°+cos60° の値を計算してください",
        "respond",
        ("calculation",),
        5,
        ("1",),
    ),
    MathPattern(
        "high_school",
        "三角関数の合成を使って sinθ+cosθ の最大値を求めてください",
        "respond",
        ("calculation", "sequence"),
        4,
        ("√2",),
    ),
    MathPattern(
        "high_school",
        "2^x=8 を満たすxを求めてください",
        "respond",
        ("calculation", "equivalence"),
        4,
        ("x=3",),
    ),
    MathPattern(
        "high_school",
        "log_2 8 の値を求め、指数との関係を説明してください",
        "respond",
        ("calculation", "definition"),
        4,
        ("3",),
    ),
    MathPattern(
        "high_school",
        "等差数列 3,7,11,... の一般項を求めてください",
        "respond",
        ("calculation", "sequence"),
        5,
        ("a_n=4n-1",),
    ),
    MathPattern(
        "high_school",
        "1+2+...+n = n(n+1)/2 を数学的帰納法で証明してください",
        "verify",
        ("verification", "sequence"),
        5,
    ),
    MathPattern(
        "high_school",
        "ベクトルの内積の定義を説明してください",
        "respond",
        ("definition",),
        4,
    ),
    MathPattern(
        "high_school",
        "関数 f(x)=x^3-3x の極値を微分を使って求めてください",
        "respond",
        ("calculation", "sequence"),
        5,
        ("極大値2 (x=-1)、極小値-2 (x=1)",),
    ),
    MathPattern(
        "high_school",
        "曲線 y=x^2 とx軸およびx=1で囲まれた面積を積分で求めてください",
        "respond",
        ("calculation", "decomposition"),
        5,
        ("1/3",),
    ),
    MathPattern(
        "high_school",
        "5人から3人を選ぶ組み合わせは何通りですか",
        "respond",
        ("calculation",),
        4,
        ("10通り",),
    ),
    MathPattern(
        "high_school",
        "データの平均と分散の違いを比較して説明してください",
        "respond",
        ("comparison", "definition"),
        4,
    ),
    MathPattern(
        "high_school",
        "極限 lim(x→0) sinx/x = 1 の計算結果を検証してください",
        "verify",
        ("verification", "calculation"),
        5,
    ),
    MathPattern(
        "high_school",
        "二次方程式の解法を平方完成と判別式の二通りで比較してください",
        "explore",
        ("comparison", "calculation"),
        5,
    ),
    MathPattern(
        "high_school",
        "確率の問題で事象が独立かどうか不明な場合、何を確認すべきか質問してください",
        "clarify",
        ("condition", "uncertainty"),
        4,
    ),
    MathPattern(
        "high_school",
        "この長い証明の要点を短く要約してください",
        "summarize",
        ("decomposition",),
        5,
    ),
    MathPattern(
        "high_school",
        "微分と積分の関係を一文で要約してください",
        "summarize",
        ("decomposition", "equivalence"),
        4,
    ),
    MathPattern(
        "high_school",
        "この単元の公式を一覧に要約してまとめてください",
        "summarize",
        ("decomposition",),
        4,
    ),
    MathPattern(
        "high_school",
        "数列の問題の別解をいくつか探索してください",
        "explore",
        ("comparison", "sequence"),
        4,
    ),
    MathPattern(
        "high_school",
        "解と係数の関係を使って x^2-5x+6=0 の解を求める手順を構成してください",
        "build",
        ("sequence", "calculation"),
        4,
        ("x=2, x=3",),
    ),
    MathPattern(
        "high_school",
        "三角比を使った測量問題の解法プランを設計してください",
        "build",
        ("decomposition", "sequence"),
        5,
    ),
    MathPattern(
        "high_school",
        "ベクトルを使った証明問題の解答方針を組み立ててください",
        "build",
        ("sequence", "verification"),
        4,
    ),
    # 少数Route補強（clarify / explore / summarize のバリエーション）
    MathPattern(
        "elementary",
        "この問題は条件が不足しているので、必要な情報を質問してください",
        "clarify",
        ("condition", "uncertainty"),
        4,
    ),
    MathPattern(
        "junior_high",
        "何を求める問題なのか曖昧なので、先に確認の質問をしてください",
        "clarify",
        ("uncertainty", "condition"),
        4,
    ),
    MathPattern(
        "junior_high",
        "この数学の問題の別解を考えてください",
        "explore",
        ("comparison",),
        4,
    ),
    MathPattern(
        "high_school",
        "三角関数の問題の解き方を複数の方針で検討してください",
        "explore",
        ("comparison", "calculation"),
        4,
    ),
    MathPattern(
        "elementary",
        "この解答のポイントを短くまとめてください",
        "summarize",
        ("decomposition",),
        4,
    ),
    MathPattern(
        "high_school",
        "証明の流れを簡潔にまとめて要約してください",
        "summarize",
        ("decomposition", "sequence"),
        4,
    ),
    MathPattern(
        "addition",
        "答えが同じになる別の計算方法を考えてください",
        "explore",
        ("equivalence", "comparison"),
        4,
    ),
    MathPattern(
        "high_school",
        "微分の問題を別のやり方で解くことを検討してください",
        "explore",
        ("comparison",),
        4,
    ),
    MathPattern(
        "elementary",
        "計算結果の要点を短く要約してください",
        "summarize",
        ("decomposition",),
        4,
    ),
    MathPattern(
        "high_school",
        "この解答全体を3行で要約してください",
        "summarize",
        ("decomposition",),
        4,
    ),
    MathPattern(
        "elementary",
        "計算結果に誤りがないか検算してください",
        "verify",
        ("verification", "calculation"),
        4,
    ),
    MathPattern(
        "high_school",
        "この不等式が常に成り立つか確認してください",
        "verify",
        ("verification", "condition"),
        4,
    ),
    MathPattern(
        "junior_high",
        "解答の根拠が正しいかレビューしてください",
        "verify",
        ("verification",),
        4,
    ),
    MathPattern(
        "high_school",
        "増減表とグラフの形が正しいか検証してください",
        "verify",
        ("verification", "calculation"),
        4,
    ),
    MathPattern(
        "high_school",
        "確率の問題を解く計画を立ててください",
        "build",
        ("sequence", "uncertainty"),
        4,
    ),
    MathPattern(
        "junior_high",
        "図形の証明の方針を構成してください",
        "build",
        ("sequence", "decomposition"),
        4,
    ),
    MathPattern(
        "junior_high",
        "方程式を解くステップを順番に組み立ててください",
        "build",
        ("sequence",),
        4,
    ),
    MathPattern(
        "elementary",
        "文章題を式にする手順を作成してください",
        "build",
        ("decomposition", "sequence"),
        4,
    ),
    MathPattern(
        "high_school",
        "変数の定義が不明なので質問してください",
        "clarify",
        ("condition", "uncertainty"),
        4,
    ),
    MathPattern(
        "junior_high",
        "求める値がどれか曖昧なので確認の質問をしてください",
        "clarify",
        ("uncertainty",),
        4,
    ),
    MathPattern(
        "elementary",
        "問題文に数値が足りないときは何が必要か質問してください",
        "clarify",
        ("condition",),
        4,
    ),
    # explore Route 強化（弱点#1 / 2026-06-11）。
    # 「別の・他の・もっと良い・複数・いくつか + 探す/考える/挙げる/検討」
    # 系の発散的な指示を respond から切り分けるための承認候補。
    MathPattern(
        "addition",
        "8になる別のたし算を考えてください",
        "explore",
        ("comparison", "calculation"),
        5,
        ("3+5", "6+2", "4+4", "7+1"),
    ),
    MathPattern(
        "addition",
        "答えが8になる別の足し算を挙げてください",
        "explore",
        ("comparison", "calculation"),
        4,
        ("2+6", "1+7", "0+8"),
    ),
    MathPattern(
        "addition",
        "この計算を別のやり方でも解いてみてください",
        "explore",
        ("comparison",),
        4,
    ),
    MathPattern(
        "junior_high",
        "別のアプローチを探してください",
        "explore",
        ("comparison",),
        4,
    ),
    MathPattern(
        "junior_high",
        "他の解き方はありますか",
        "explore",
        ("comparison",),
        4,
    ),
    MathPattern(
        "high_school",
        "もっと良い解き方がないか探してください",
        "explore",
        ("comparison",),
        4,
    ),
    MathPattern(
        "elementary",
        "この問題を解く方法を複数考えて挙げてください",
        "explore",
        ("comparison", "sequence"),
        4,
    ),
    MathPattern(
        "high_school",
        "別の視点からこの問題を考え直してください",
        "explore",
        ("comparison",),
        4,
    ),
    MathPattern(
        "high_school",
        "考えられる解法をできるだけ多く列挙してください",
        "explore",
        ("comparison", "decomposition"),
        4,
    ),
    MathPattern(
        "high_school",
        "公式を使わない別解がないか検討してください",
        "explore",
        ("comparison", "calculation"),
        4,
    ),
)


def curriculum_document() -> SourceDocument:
    return SourceDocument(
        source_kind="curriculum",
        title="Math thinking-pattern curriculum v1",
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
    for pattern in MATH_CURRICULUM:
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
                    "goals": [f"math::{pattern.level}"],
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
