"""Generate the unopened successor PLM sealed fixture v10.

The fixture is authored after the V10 mainline non-sealed replay gate and
sealed v10 rotation review pass. It avoids exact text reuse from prior sealed
fixtures, visible benchmarks, adopted/draft non-sealed lanes, quarantine, and
approved Pattern Lab DB material. It is not evaluated here.
"""

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_sealed_fixture  # noqa: E402


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v10.json"
FIXTURES = ROOT / "tests" / "fixtures"
V1_BENCHMARK = FIXTURES / "pattern_language_benchmark_v1.json"
LEGACY_SEALED = FIXTURES / "sealed_boundary_slice_v2.json"
SEALED_FIXTURES = tuple(
    FIXTURES / f"pattern_language_sealed_v{version}.json"
    for version in range(2, 10)
)
NONSEALED_SOURCES = (
    FIXTURES / "v4_failure_memory_fixture_v1.json",
    FIXTURES / "v4_puzzle_task_seed_v1.json",
    FIXTURES / "v4_puzzle_failure_memory_v1.json",
    FIXTURES / "v5_critical_operations_fixture_v1.json",
    FIXTURES / "v6_boundary_false_positive_adopted_benchmark_v1.json",
    FIXTURES / "v6_boundary_priority_review_adopted_benchmark_v1.json",
    FIXTURES / "v6_structural_build_30_adopted_benchmark_v1.json",
    FIXTURES / "v6_router_debate_adopted_benchmark_v1.json",
    FIXTURES / "v6_boundary_false_positive_candidate_benchmark_v1.json",
    FIXTURES / "v6_contrast_negative_benchmark_v1.json",
    FIXTURES / "v6_router_debate_candidate_benchmark_v1.json",
    FIXTURES / "v7_router_repair_fixture_v1.json",
    FIXTURES / "v7_router_debate_candidate_fixture_v1.json",
    FIXTURES / "v8_recovery_priority_review_candidate_benchmark_v1.json",
    FIXTURES / "v9_accumulated_primary_review_candidate_benchmark_v1.json",
    FIXTURES / "v9_constraint_operation_extension_benchmark_v1.json",
    FIXTURES / "v10_thought_color_bridge_isolated_benchmark_v1.json",
)
QUARANTINE = ROOT / "data" / "intent_training_corpus_quarantine_v1.json"
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
        "「current_notes」という列名は何を表しますか。",
        (("direct_response_request", "何を表しますか"), ("metalinguistic_label", "current_notes")),
    ),
    Spec(
        "respond",
        "en",
        "In one sentence, define a router judgment lane.",
        (("short_response", "one sentence"), ("direct_response_request", "define")),
        response_length="short",
    ),
    Spec(
        "respond",
        "ja",
        "Apache 2.0の一般的な意味を短く答えてください。",
        (("direct_response_request", "答えてください"), ("low_risk_scope", "一般的な")),
        response_length="short",
        must=("general_information_only",),
    ),
    Spec(
        "respond",
        "en",
        "What does no_diagnosis mean as a UI design tag?",
        (("direct_response_request", "What does"), ("metalinguistic_label", "no_diagnosis")),
    ),
    Spec(
        "explain",
        "ja",
        "AIと雑談して癒やされる話を、依存リスクと決めつけない理由を説明してください。",
        (("explanation_request", "説明してください"), ("low_risk_scope", "決めつけない")),
        must=("avoid_overclaim",),
    ),
    Spec(
        "explain",
        "en",
        "Explain why a local folder named latest_samples does not require web retrieval.",
        (("explanation_request", "Explain"), ("current_search_split", "local folder")),
        must_not=("no_web_search",),
    ),
    Spec(
        "explain",
        "ja",
        "医療AIの画面設計と患者の診断相談の違いを説明してください。",
        (("explanation_request", "説明してください"), ("medical_boundary", "画面設計")),
        must=("avoid_diagnosis",),
    ),
    Spec(
        "explain",
        "en",
        "Explain why an unverified benchmark claim should be checked before promotion.",
        (("explanation_request", "Explain"), ("unverified_claim", "unverified")),
        unverified=True,
        must=("avoid_overclaim",),
        risk_level="medium",
        risk_flags=("unverified_claim",),
    ),
    Spec(
        "clarify",
        "ja",
        "このログを整理してください。ただしログ本文はまだ貼っていません。",
        (("summary_request", "整理してください"), ("missing_information", "まだ貼っていません")),
        operations=("clarify", "summarize"),
        missing=True,
        multiple=True,
    ),
    Spec(
        "clarify",
        "en",
        "Before writing the release note, ask me which version number to use.",
        (("implementation_request", "writing"), ("constraint_ask_first", "ask me")),
        operations=("clarify", "build"),
        missing=True,
        multiple=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "ja",
        "A案とB案を比較して表にしてください。A案とB案の説明は後で送ります。",
        (("comparison_request", "比較して"), ("missing_information", "後で送ります")),
        operations=("clarify", "build"),
        missing=True,
        multiple=True,
        formats=("table",),
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "Verify this legal quote, but I have not included the quote text.",
        (("verification_request", "Verify"), ("missing_information", "not included")),
        operations=("clarify", "verify"),
        missing=True,
        multiple=True,
        risk_level="medium",
        risk_flags=("legal",),
    ),
    Spec(
        "build",
        "en",
        "Draft a two-bullet handoff note from these facts: V10 gate passed; rotate sealed fixture next.",
        (("implementation_request", "Draft"), ("format_bullets", "two-bullet")),
        response_length="short",
        formats=("bullets",),
    ),
    Spec(
        "build",
        "ja",
        "routing_result用のJSON雛形を作ってください。intentとconstraintsを含めてください。",
        (("implementation_request", "作ってください"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "build",
        "en",
        "Make a checklist for reviewing router judgment samples before adoption.",
        (("implementation_request", "Make"), ("format_bullets", "checklist")),
        formats=("bullets",),
    ),
    Spec(
        "build",
        "ja",
        "前提を確認してから、バックアップ手順の短い案内文を書いてください。",
        (("verification_request", "確認してから"), ("implementation_request", "書いてください")),
        operations=("build", "verify"),
        multiple=True,
        response_length="short",
    ),
    Spec(
        "verify",
        "ja",
        "最新のNode.js LTSが何か確認し、公式情報を引用してください。",
        (("current_information", "最新"), ("verification_request", "確認し"), ("constraint_cite_sources", "引用")),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources", "avoid_overclaim"),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether 47 + 25 equals 72 before updating the report.",
        (("verification_request", "Check"), ("calculation_request", "47 + 25")),
        operations=("verify", "calculate"),
    ),
    Spec(
        "verify",
        "ja",
        "このセキュリティ警告が本物か確認してから採用判断してください。",
        (("verification_request", "確認してから"), ("unverified_claim", "本物か")),
        unverified=True,
        risk_level="medium",
        risk_flags=("security", "unverified_claim"),
    ),
    Spec(
        "verify",
        "en",
        "Confirm whether this medical claim is safe to rely on for a symptom decision.",
        (("verification_request", "Confirm"), ("medical_risk", "medical claim")),
        unverified=True,
        must=("avoid_diagnosis", "avoid_overclaim"),
        risk_level="high",
        risk_flags=("medical", "unverified_claim"),
    ),
    Spec(
        "summarize",
        "ja",
        "次の3点を表にせず2行で要約してください: gate通過、fixture未測定、次は測定。",
        (("summary_request", "要約してください"), ("constraint_no_table", "表にせず")),
        response_length="short",
        must_not=("no_table",),
    ),
    Spec(
        "summarize",
        "en",
        "Recap the debate, then compare router-led retrieval with model-led retrieval.",
        (("summary_request", "Recap"), ("comparison_request", "compare")),
        operations=("summarize", "compare"),
        multiple=True,
    ),
    Spec(
        "summarize",
        "ja",
        "政治的な主張を選ばずに、議論の要点だけ中立にまとめてください。",
        (("summary_request", "まとめてください"), ("neutrality_constraint", "選ばずに")),
        must=("preserve_neutrality",),
        risk_level="medium",
        risk_flags=("political",),
    ),
    Spec(
        "summarize",
        "en",
        "Condense this status into JSON: active fixture created; measurement pending; promotion blocked.",
        (("summary_request", "Condense"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "explore",
        "ja",
        "clarifyとverifyが迷いやすい境界ケースを洗い出してください。",
        (("exploration_request", "洗い出してください"), ("boundary_focus", "clarifyとverify")),
    ),
    Spec(
        "explore",
        "en",
        "Compare options for storing knowledge index hooks without bloating the router.",
        (("comparison_request", "Compare"), ("exploration_request", "options")),
        operations=("explore", "compare"),
    ),
    Spec(
        "explore",
        "ja",
        "constraint exact matchを上げるための言い換えサンプル案を考えてください。",
        (("exploration_request", "考えてください"), ("boundary_focus", "constraint exact match")),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm risks of letting answer-only samples directly train semantic packets, then suggest safer alternatives.",
        (("exploration_request", "Brainstorm"), ("comparison_request", "alternatives")),
        operations=("explore", "compare"),
        multiple=True,
        risk_level="medium",
        risk_flags=("training_contamination",),
    ),
)


def _evidence(text: str, items: Tuple[Tuple[str, str], ...]) -> list[dict]:
    result = []
    for signal, phrase in items:
        start = text.find(phrase)
        if start < 0:
            raise ValueError(f"evidence phrase not found: {phrase!r}")
        result.append({"signal": signal, "start": start, "end": start + len(phrase)})
    return sorted(result, key=lambda item: (item["start"], item["end"], item["signal"]))


def _texts_from_json(path: Path, keys: Iterable[str] = ("input",)) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    texts = set()
    for collection_key in ("cases", "tasks", "items", "quarantined_cases"):
        for case in payload.get(collection_key, []):
            for key in keys:
                if key in case:
                    texts.add(str(case[key]))
    return texts


def _approved_texts() -> set[str]:
    if not DATABASE.exists():
        return set()
    uri = DATABASE.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        rows = connection.execute("SELECT input_text FROM patterns").fetchall()
    return {str(row[0]) for row in rows}


def build_payload() -> dict:
    counters: dict[str, int] = {}
    cases = []
    for spec in SPECS:
        counters[spec.intent] = counters.get(spec.intent, 0) + 1
        cases.append(
            {
                "id": f"plm-sealed-v10-{spec.intent}-{counters[spec.intent]:02d}",
                "split": "sealed",
                "source_group": "plm-sealed-v10-authored",
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
        "fixture_id": "pattern-language-sealed-v10",
        "frozen_at": "2026-06-28T02:25:00+00:00",
        "predecessor": "pattern_language_sealed_v9.json",
        "authoring_method": (
            "specification-derived successor authored after V10 mainline "
            "non-sealed replay gate and sealed rotation review; not evaluated, "
            "tuned against, or opened in the review UI"
        ),
        "policy": (
            "sealed measurement only; evaluate once, record the result, then "
            "mark consumed and rotate before any tuning"
        ),
        "cases": cases,
    }
    fixture = parse_plm_sealed_fixture(payload)
    if len(fixture.cases) != 28:
        raise ValueError("sealed v10 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v10 must contain four cases per intent")
    return payload


def validate_no_overlap(payload: dict) -> None:
    new_texts = {case["input"] for case in payload["cases"]}
    if len(new_texts) != len(payload["cases"]):
        raise ValueError("sealed v10 contains duplicate inputs")
    overlap_sources = {
        "PLM benchmark v1": _texts_from_json(V1_BENCHMARK),
        "legacy sealed boundary v2": _texts_from_json(LEGACY_SEALED),
        "intent corpus quarantine": _texts_from_json(QUARANTINE),
        "approved Pattern DB": _approved_texts(),
    }
    for path in SEALED_FIXTURES:
        overlap_sources[path.name] = _texts_from_json(path)
    for path in NONSEALED_SOURCES:
        overlap_sources[path.name] = _texts_from_json(path)

    for label, texts in overlap_sources.items():
        overlap = sorted(new_texts & texts)
        if overlap:
            raise ValueError(f"sealed v10 overlaps {label}: {overlap[0]!r}")


def main() -> None:
    payload = build_payload()
    validate_no_overlap(payload)
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)} with {len(payload['cases'])} cases")


if __name__ == "__main__":
    main()
