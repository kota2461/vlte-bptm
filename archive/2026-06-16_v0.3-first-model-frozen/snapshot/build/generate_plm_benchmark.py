"""Generate the frozen draft Pattern Language Model benchmark v1.

The sealed split is authored and frozen here but is not evaluated by the
baseline report. This is an AI-assisted draft requiring human review.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


OUTPUT = Path("tests/fixtures/pattern_language_benchmark_v1.json")
SPLITS = ("train", "validation", "sealed")


@dataclass(frozen=True)
class CaseSpec:
    text: str
    evidence: Tuple[Tuple[str, str], ...]
    operations: Tuple[str, ...] = ()
    missing: bool = False
    unverified: bool = False
    current: bool = False
    multiple: bool = False
    response_length: str = "unspecified"
    formats: Tuple[str, ...] = ()
    must: Tuple[str, ...] = ()
    must_not: Tuple[str, ...] = ()
    risk_level: str = "low"
    risk_flags: Tuple[str, ...] = ()
    unknowns: Tuple[str, ...] = ()
    conflicts: Tuple[str, ...] = ()
    contrast_group: str | None = None


def c(
    text: str,
    signal: str,
    phrase: str,
    **kwargs,
) -> CaseSpec:
    evidence = kwargs.pop("evidence", ((signal, phrase),))
    return CaseSpec(text=text, evidence=evidence, **kwargs)


CASES = {
    "respond": (
        c("HTTPの正式名称は何ですか。", "direct_response_request", "何ですか"),
        c("富士山の標高を教えてください。", "direct_response_request", "教えて"),
        c("What does CPU stand for?", "direct_response_request", "What does"),
        c("Name the smallest prime number.", "direct_response_request", "Name the"),
        c(
            "この値の単位だけを短く答えてください。",
            "direct_response_request",
            "答えて",
            response_length="short",
            evidence=(
                ("direct_response_request", "答えて"),
                ("short_response", "短く"),
            ),
        ),
        c("この記号が示す意味を教えてください。", "direct_response_request", "教えて"),
        c(
            "Tell me the file extension used for JSON.",
            "direct_response_request",
            "Tell me",
        ),
        c(
            "Which port is normally associated with HTTPS?",
            "direct_response_request",
            "Which",
        ),
        c("円周率の先頭3桁を答えてください。", "direct_response_request", "答えて"),
        c("この略語の読み方を教えてください。", "direct_response_request", "教えて"),
        c("What is the result of 9 minus 4?", "direct_response_request", "What is"),
        c("Who is the author named in this citation?", "direct_response_request", "Who is"),
    ),
    "explain": (
        c("キャッシュが応答を速くする仕組みを説明してください。", "explanation_request", "仕組み"),
        c("なぜ主キーが必要なのか説明してください。", "explanation_request", "なぜ"),
        c("Explain how a checksum detects corruption.", "explanation_request", "Explain"),
        c("Why does indexing improve some database queries?", "explanation_request", "Why"),
        c(
            "この方式を採用する理由を簡潔に説明してください。",
            "explanation_request",
            "理由",
            response_length="short",
            evidence=(
                ("explanation_request", "理由"),
                ("short_response", "簡潔"),
            ),
        ),
        c("非同期処理が待ち時間を隠す仕組みを説明してください。", "explanation_request", "仕組み"),
        c("Describe how dependency injection works.", "explanation_request", "Describe how"),
        c("Explain the reason this request is idempotent.", "explanation_request", "Explain"),
        c("なぜこの検査が必要なのか教えてください。", "explanation_request", "なぜ"),
        c("このアルゴリズムが収束する仕組みを詳しく説明してください。", "explanation_request", "仕組み", response_length="long", evidence=(("explanation_request", "仕組み"), ("long_response", "詳しく"))),
        c("How does a reverse proxy protect an application server?", "explanation_request", "How does"),
        c("Explain why the two results differ.", "explanation_request", "Explain"),
    ),
    "clarify": (
        c("見積もりを作ってください。利用者数はまだ伝えていません。", "missing_information", "まだ伝えていません", missing=True),
        c("導入手順が必要ですが、対象OSはまだ決めていません。", "missing_information", "まだ決めていません", missing=True),
        c("Estimate the cost, but the number of licenses was not provided.", "missing_information", "not provided", missing=True),
        c("Before answering, ask me which database version is installed.", "missing_information", "Before answering", missing=True, must=("ask_first",)),
        c("必要な情報が不足しています。先に質問してください。", "missing_information", "不足しています", missing=True, must=("ask_first",), evidence=(("missing_information", "不足しています"), ("constraint_ask_first", "先に質問"))),
        c("移行期間を計算したいですが、データ量がまだ伝わっていません。", "missing_information", "まだ伝わっていません", missing=True, operations=("clarify", "calculate")),
        c("The estimate depends on traffic volume, which is not stated.", "missing_information", "not stated", missing=True),
        c("Ask me which region to use before giving cloud commands.", "missing_information", "Ask me", missing=True, must=("ask_first",)),
        c("契約額を出す前に、契約年数を聞いてください。", "missing_information", "聞いてください", missing=True, must=("ask_first",)),
        c("対象ファイルが分かりません。先に質問してください。", "missing_information", "分かりません", missing=True, unknowns=("target_file",), must=("ask_first",), evidence=(("missing_information", "分かりません"), ("constraint_ask_first", "先に質問"))),
        c("Some information is missing, so ask which environment this concerns.", "missing_information", "information is missing", missing=True, must=("ask_first",)),
        c("The calculation needs a tax rate that has not been shared.", "missing_information", "not been shared", missing=True, operations=("clarify", "calculate")),
    ),
    "build": (
        c("承認済みの案を実装手順に分解してください。", "implementation_request", "実装手順"),
        c("担当者別の作業計画を作ってください。", "implementation_request", "作業計画"),
        c("Create a step-by-step rollout plan for this change.", "implementation_request", "step-by-step"),
        c("Break down the migration into ordered tasks.", "implementation_request", "ordered tasks"),
        c("設定から試験までの手順を箇条書きで作ってください。", "implementation_request", "手順", formats=("bullets",), evidence=(("implementation_request", "手順"), ("format_bullets", "箇条書き"))),
        c("この仕様から導入計画を詳しく作成してください。", "implementation_request", "導入計画", response_length="long", evidence=(("implementation_request", "導入計画"), ("long_response", "詳しく"))),
        c("Turn these requirements into an implementation plan.", "implementation_request", "implementation plan"),
        c("Make an ordered task list for the release.", "implementation_request", "task list"),
        c("復旧方法は決定済みです。作業の順番を作ってください。", "implementation_request", "順番"),
        c("この変更の実装計画をJSONで出してください。", "implementation_request", "実装計画", formats=("json",), evidence=(("implementation_request", "実装計画"), ("format_json", "JSON"))),
        c("Prepare a work plan from setup through validation.", "implementation_request", "work plan"),
        c("Build a rollout plan, but do not include code.", "implementation_request", "rollout plan", must_not=("no_code",), evidence=(("implementation_request", "rollout plan"), ("constraint_no_code", "do not include code"))),
    ),
    "verify": (
        c("この合計が正しいか確認してください。", "verification_request", "正しいか", unverified=True, operations=("verify", "calculate")),
        c("提示された見積もりが上限内か検証してください。", "verification_request", "検証して", unverified=True, evidence=(("unverified_claim", "提示された"), ("verification_request", "検証して"))),
        c("Check whether these totals add up correctly.", "verification_request", "Check", unverified=True, operations=("verify", "calculate")),
        c("Validate the claimed result against the evidence.", "verification_request", "Validate", unverified=True, evidence=(("verification_request", "Validate"), ("unverified_claim", "claimed"))),
        c("最新の料金か、出典付きで確認してください。", "verification_request", "確認して", current=True, unverified=True, must=("cite_sources",), risk_level="medium", risk_flags=("current_information", "unverified_claim"), operations=("verify", "search"), evidence=(("current_information", "最新"), ("constraint_cite_sources", "出典付き"), ("verification_request", "確認して"))),
        c("この主張が妥当か、根拠を示して確かめてください。", "verification_request", "妥当か", unverified=True, must=("cite_sources",), risk_level="medium", risk_flags=("unverified_claim",), evidence=(("unverified_claim", "主張"), ("verification_request", "妥当か"), ("constraint_cite_sources", "根拠を示して"))),
        c("Confirm that the current version still supports this option.", "verification_request", "Confirm", current=True, risk_level="medium", risk_flags=("current_information",), operations=("verify", "search"), evidence=(("verification_request", "Confirm"), ("current_information", "current"))),
        c("Make sure the proposed limit is safe.", "verification_request", "Make sure", unverified=True, evidence=(("verification_request", "Make sure"), ("unverified_claim", "proposed"))),
        c("現在の法律に照らして、この契約条項を確認してください。", "verification_request", "確認して", current=True, unverified=True, risk_level="high", risk_flags=("legal", "current_information", "unverified_claim"), operations=("verify", "search"), evidence=(("current_information", "現在"), ("legal_risk", "法律"), ("verification_request", "確認して"))),
        c("報告された数値が表と一致するか確かめてください。", "verification_request", "一致するか", unverified=True, evidence=(("unverified_claim", "報告された"), ("verification_request", "一致するか"))),
        c("Verify today's exchange rate with sources.", "verification_request", "Verify", current=True, must=("cite_sources",), risk_level="medium", risk_flags=("current_information",), operations=("verify", "search"), evidence=(("verification_request", "Verify"), ("current_information", "today"), ("constraint_cite_sources", "with sources"))),
        c("Double-check whether the medication dose matches the prescription.", "verification_request", "Double-check", unverified=True, risk_level="high", risk_flags=("medical", "unverified_claim"), evidence=(("verification_request", "Double-check"), ("medical_risk", "medication"))),
    ),
    "summarize": (
        c("この議事録を3行で要約してください。", "summary_request", "要約", response_length="short", evidence=(("short_response", "3行"), ("summary_request", "要約"))),
        c("長い説明を要点だけにまとめてください。", "summary_request", "要点"),
        c("Summarize this report in one sentence.", "summary_request", "Summarize", response_length="short", evidence=(("summary_request", "Summarize"), ("short_response", "one sentence"))),
        c("Condense the discussion into bullet points.", "summary_request", "Condense", formats=("bullets",), evidence=(("summary_request", "Condense"), ("format_bullets", "bullet points"))),
        c("会議の決定事項を短くまとめてください。", "summary_request", "まとめて", response_length="short", evidence=(("short_response", "短く"), ("summary_request", "まとめて"))),
        c("この記事の要点を表形式で要約してください。", "summary_request", "要点", formats=("table",), evidence=(("summary_request", "要点"), ("format_table", "表形式"))),
        c("Recap the main decisions briefly.", "summary_request", "Recap", response_length="short", evidence=(("summary_request", "Recap"), ("short_response", "briefly"))),
        c("Boil these notes down to the key points.", "summary_request", "Boil"),
        c("この調査結果を一文でまとめてください。", "summary_request", "まとめて", response_length="short", evidence=(("short_response", "一文"), ("summary_request", "まとめて"))),
        c("変更履歴から重要点だけを要約してください。", "summary_request", "要約"),
        c("Give me a concise summary of the incident.", "summary_request", "summary", response_length="short", evidence=(("short_response", "concise"), ("summary_request", "summary"))),
        c("Summarize the findings without using a table.", "summary_request", "Summarize", must_not=("no_table",)),
    ),
    "explore": (
        c("負荷を減らす複数の案を挙げてください。", "exploration_request", "複数の案"),
        c("採用前に別の方法と利点を比較してください。", "exploration_request", "別の方法", operations=("explore", "compare")),
        c("Suggest several options for organizing this module.", "exploration_request", "several options"),
        c(
            "Brainstorm different approaches to improve reliability and then compare them.",
            "exploration_request",
            "Brainstorm",
            operations=("explore", "compare"),
            multiple=True,
        ),
        c("候補を3つ挙げ、短く比較してください。", "exploration_request", "候補を", operations=("explore", "compare"), response_length="short", evidence=(("exploration_request", "候補を"), ("short_response", "短く"))),
        c("いくつかの方法を表形式で整理してください。", "exploration_request", "いくつかの方法", formats=("table",), evidence=(("exploration_request", "いくつかの方法"), ("format_table", "表形式"))),
        c("Compare options for storing these events.", "exploration_request", "Compare options", operations=("explore", "compare")),
        c(
            "What are some other ways to reduce startup time, and then compare their trade-offs?",
            "exploration_request",
            "other ways",
            operations=("explore", "compare"),
            multiple=True,
        ),
        c("認証方式の選択肢を詳しく比較してください。", "exploration_request", "選択肢", operations=("explore", "compare"), response_length="long", evidence=(("exploration_request", "選択肢"), ("long_response", "詳しく"))),
        c("設計候補を挙げてから、それぞれの弱点も説明してください。", "exploration_request", "候補を", multiple=True, contrast_group="sealed-explore-explain-ja"),
        c("List possible strategies and compare their trade-offs.", "exploration_request", "possible strategies", operations=("explore", "compare")),
        c("Offer alternatives, then briefly explain the strongest one.", "exploration_request", "alternatives", multiple=True, response_length="short", evidence=(("exploration_request", "alternatives"), ("short_response", "briefly")), contrast_group="sealed-explore-explain-en"),
    ),
}


def split_for_index(index: int) -> str:
    return SPLITS[index // 4]


def language_for_index(index: int) -> str:
    return "ja" if index % 4 < 2 else "en"


def evidence_spans(
    text: str,
    evidence: Tuple[Tuple[str, str], ...],
) -> List[dict]:
    result = []
    for signal, phrase in evidence:
        start = text.find(phrase)
        if start < 0:
            raise ValueError(f"evidence phrase not found: {phrase!r} in {text!r}")
        result.append(
            {"signal": signal, "start": start, "end": start + len(phrase)}
        )
    return sorted(result, key=lambda item: (item["start"], item["end"], item["signal"]))


def main() -> None:
    cases = []
    for intent, specs in CASES.items():
        if len(specs) != 12:
            raise ValueError(f"{intent} must contain exactly 12 cases")
        for index, spec in enumerate(specs):
            split = split_for_index(index)
            language = language_for_index(index)
            operations = spec.operations or (intent,)
            cases.append(
                {
                    "id": f"plm-{split}-{intent}-{index % 4 + 1:02d}",
                    "split": split,
                    "source_group": f"plm-v1-{split}-draft",
                    "contrast_group": spec.contrast_group,
                    "language": language,
                    "input": spec.text,
                    "expected": {
                        "primary_intent": intent,
                        "operations": list(operations),
                        "information_state": {
                            "missing_required_information": spec.missing,
                            "contains_unverified_claims": spec.unverified,
                            "requires_current_information": spec.current,
                            "multiple_intents": spec.multiple,
                        },
                        "constraints": {
                            "response_length": spec.response_length,
                            "formats": list(spec.formats),
                            "must": list(spec.must),
                            "must_not": list(spec.must_not),
                        },
                        "risk": {
                            "level": spec.risk_level,
                            "flags": list(spec.risk_flags),
                        },
                        "evidence": evidence_spans(
                            spec.text,
                            spec.evidence,
                        ),
                        "unknowns": list(spec.unknowns),
                        "conflicts": list(spec.conflicts),
                    },
                }
            )

    payload = {
        "schema_version": "pattern-language-benchmark.v1",
        "frozen_at": "2026-06-12T08:30:00+00:00",
        "authoring_method": (
            "specification-derived AI-assisted draft; no teacher answers, "
            "logits, hidden reasoning, or copied source text"
        ),
        "review_status": "draft",
        "policy": (
            "train and validation may be used for baseline analysis; sealed "
            "must not be evaluated or used for tuning before human review "
            "and an explicit measurement decision"
        ),
        "cases": cases,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT} with {len(cases)} cases")


if __name__ == "__main__":
    main()
