"""Generate the unopened successor PLM sealed fixture v2."""

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_sealed_fixture


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
V1_BENCHMARK = (
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
LEGACY_SEALED = (
    ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json"
)
DATABASE = ROOT / "data" / "pattern_lab.db"


@dataclass(frozen=True)
class Spec:
    intent: str
    language: str
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


SPECS = (
    Spec(
        "respond",
        "ja",
        "IPv6のアドレス長は何ビットですか。",
        (("direct_response_request", "何ビットですか"),),
    ),
    Spec(
        "respond",
        "ja",
        "恐縮ですが、Gitで直前のコミットを指す記号だけ教えてください。",
        (("direct_response_request", "教えてください"),),
        response_length="short",
    ),
    Spec(
        "respond",
        "en",
        "What file format normally uses the .toml extension?",
        (("direct_response_request", "What"),),
    ),
    Spec(
        "respond",
        "en",
        "Please name the protocol commonly used to send email.",
        (("direct_response_request", "name the"),),
    ),
    Spec(
        "explain",
        "ja",
        "なぜデータベースのインデックスは書き込みを遅くすることがあるのか説明してください。",
        (("explanation_request", "説明してください"),),
    ),
    Spec(
        "explain",
        "mixed",
        "API gatewayがrate limitingを行う仕組みを説明してください。",
        (("explanation_request", "仕組み"),),
    ),
    Spec(
        "explain",
        "en",
        "Explain why clock drift can break distributed leases.",
        (("explanation_request", "Explain"),),
    ),
    Spec(
        "explain",
        "en",
        "Describe how a circuit breaker prevents cascading failures.",
        (("explanation_request", "Describe how"),),
    ),
    Spec(
        "clarify",
        "ja",
        "来月の予算を見積もってください。ただし利用人数はまだ決めていません。",
        (("missing_information", "まだ決めていません"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "clarify",
        "mixed",
        "deploy手順を書いてほしいのですが、target environmentはまだ共有していません。先に質問してください。",
        (
            ("missing_information", "まだ共有していません"),
            ("constraint_ask_first", "先に質問"),
        ),
        missing=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "Calculate the retention cost, but the daily volume has not been provided.",
        (("missing_information", "not been provided"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Before giving migration commands, ask which database engine is in use.",
        (
            ("constraint_ask_first", "Before giving"),
            ("missing_information", "ask which"),
        ),
        missing=True,
        must=("ask_first",),
    ),
    Spec(
        "build",
        "ja",
        "確認済みの要件を、設定・テスト・公開の順に実装計画へしてください。",
        (("implementation_request", "実装計画"),),
    ),
    Spec(
        "build",
        "mixed",
        "このdraft API仕様をvalidateしつつ、問題なければ実装手順を作ってください。",
        (
            ("unverified_claim", "draft"),
            ("verification_request", "validate"),
            ("implementation_request", "実装手順"),
        ),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "build",
        "en",
        "Turn the approved requirements into an ordered implementation plan.",
        (("implementation_request", "implementation plan"),),
    ),
    Spec(
        "build",
        "en",
        "Validate the proposed schema and then produce a rollout plan.",
        (
            ("verification_request", "Validate"),
            ("unverified_claim", "proposed"),
            ("implementation_request", "rollout plan"),
        ),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "verify",
        "ja",
        "現在の個人情報保護法で、この保存方針が許されるか出典付きで確認してください。",
        (
            ("current_information", "現在"),
            ("legal_risk", "個人情報保護法"),
            ("constraint_cite_sources", "出典付き"),
            ("verification_request", "確認してください"),
        ),
        operations=("verify", "search"),
        unverified=True,
        current=True,
        must=("cite_sources",),
        risk_level="high",
        risk_flags=("legal", "current_information", "unverified_claim"),
    ),
    Spec(
        "verify",
        "mixed",
        "最新のPython releaseでこのAPIがdeprecatedか、公式source付きで確認してください。",
        (
            ("current_information", "最新"),
            ("unverified_claim", "deprecated"),
            ("constraint_cite_sources", "公式source付き"),
            ("verification_request", "確認してください"),
        ),
        operations=("verify", "search"),
        unverified=True,
        current=True,
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("current_information", "unverified_claim"),
    ),
    Spec(
        "verify",
        "en",
        "Check whether the reported totals match the ledger.",
        (
            ("verification_request", "Check"),
            ("unverified_claim", "reported"),
        ),
        operations=("verify", "calculate"),
        unverified=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify today's exchange rate before using it in the estimate.",
        (
            ("verification_request", "Verify"),
            ("current_information", "today"),
        ),
        operations=("verify", "search"),
        current=True,
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "summarize",
        "ja",
        "この長い議論を、決定事項と未解決点に分けて3行で要約してください。",
        (
            ("short_response", "3行"),
            ("summary_request", "要約してください"),
        ),
        response_length="short",
    ),
    Spec(
        "summarize",
        "mixed",
        "meeting notesをtableなしで簡潔にまとめてください。",
        (
            ("constraint_no_table", "tableなし"),
            ("short_response", "簡潔に"),
            ("summary_request", "まとめてください"),
        ),
        response_length="short",
        must_not=("no_table",),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the policy debate without endorsing either position.",
        (("summary_request", "Summarize"),),
        must=("preserve_neutrality",),
    ),
    Spec(
        "summarize",
        "en",
        "Condense the incident report into four bullet points.",
        (
            ("summary_request", "Condense"),
            ("format_bullets", "bullet points"),
        ),
        response_length="short",
        formats=("bullets",),
    ),
    Spec(
        "explore",
        "ja",
        "少子化対策について、価値判断を分けながら複数の選択肢を比較してください。",
        (
            ("exploration_request", "複数の選択肢"),
            ("comparison_request", "比較してください"),
        ),
        operations=("explore", "compare"),
        must=("preserve_neutrality",),
    ),
    Spec(
        "explore",
        "mixed",
        "将来のAI regulationについて複数scenarioを挙げ、断定せず比較してください。",
        (
            ("exploration_request", "複数scenario"),
            ("comparison_request", "比較してください"),
        ),
        operations=("explore", "compare"),
        must=("avoid_overclaim",),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm ways to reduce latency while preserving reliability, and then compare the trade-offs.",
        (
            ("exploration_request", "Brainstorm"),
            ("comparison_request", "compare the trade-offs"),
        ),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "en",
        "Our deployment process is obviously perfect; humor me with a few alternatives and their weaknesses.",
        (("exploration_request", "alternatives"),),
        operations=("explore", "compare"),
    ),
)


def _evidence(text: str, items: Tuple[Tuple[str, str], ...]) -> list[dict]:
    result = []
    for signal, phrase in items:
        start = text.find(phrase)
        if start < 0:
            raise ValueError(f"evidence phrase not found: {phrase!r}")
        result.append(
            {
                "signal": signal,
                "start": start,
                "end": start + len(phrase),
            }
        )
    return sorted(
        result,
        key=lambda item: (item["start"], item["end"], item["signal"]),
    )


def _approved_texts() -> set[str]:
    if not DATABASE.exists():
        return set()
    uri = DATABASE.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        rows = connection.execute("SELECT input_text FROM patterns").fetchall()
    return {str(row[0]) for row in rows}


def main() -> None:
    counters: dict[str, int] = {}
    cases = []
    for spec in SPECS:
        counters[spec.intent] = counters.get(spec.intent, 0) + 1
        cases.append(
            {
                "id": (
                    f"plm-sealed-v2-{spec.intent}-"
                    f"{counters[spec.intent]:02d}"
                ),
                "split": "sealed",
                "source_group": "plm-sealed-v2-authored",
                "contrast_group": None,
                "language": spec.language,
                "input": spec.text,
                "expected": {
                    "primary_intent": spec.intent,
                    "operations": list(spec.operations or (spec.intent,)),
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
                    "evidence": _evidence(spec.text, spec.evidence),
                    "unknowns": [],
                    "conflicts": [],
                },
            }
        )
    payload = {
        "schema_version": "pattern-language-sealed.v1",
        "fixture_id": "pattern-language-sealed-v2",
        "frozen_at": "2026-06-13T05:45:00+00:00",
        "predecessor": "pattern_language_benchmark_v1.json#sealed",
        "authoring_method": (
            "specification-derived successor authored after v1 human review; "
            "not evaluated, tuned against, or opened in the review UI"
        ),
        "policy": (
            "sealed measurement only; evaluate once, record the result, then "
            "mark consumed and rotate before any tuning"
        ),
        "cases": cases,
    }
    fixture = parse_plm_sealed_fixture(payload)
    if len(fixture.cases) != 28:
        raise ValueError("sealed v2 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v2 must contain four cases per intent")

    old = json.loads(V1_BENCHMARK.read_text(encoding="utf-8"))
    legacy = json.loads(LEGACY_SEALED.read_text(encoding="utf-8"))
    old_texts = {case["input"] for case in old["cases"]}
    legacy_texts = {case["input"] for case in legacy["cases"]}
    new_texts = {case.input_text for case in fixture.cases}
    if new_texts & old_texts:
        raise ValueError("sealed v2 overlaps PLM benchmark v1")
    if new_texts & legacy_texts:
        raise ValueError("sealed v2 overlaps legacy sealed v2")
    if new_texts & _approved_texts():
        raise ValueError("sealed v2 overlaps approved Pattern DB")

    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)} with {len(cases)} cases")


if __name__ == "__main__":
    main()
