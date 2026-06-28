"""Generate the unopened successor PLM sealed fixture v6.

The fixture is authored after the V6 non-sealed replay gate and sealed v6
rotation review pass. It does not reuse visible benchmark, prior sealed,
Failure Memory, puzzle, V5, or V6 non-sealed lane texts. It is not evaluated
here.
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


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v6.json"
V1_BENCHMARK = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
LEGACY_SEALED = ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json"
SEALED_V2 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
SEALED_V3 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v3.json"
SEALED_V4 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json"
SEALED_V5 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v5.json"
V4_FAILURE_MEMORY = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
V4_PUZZLE_SEED = ROOT / "tests" / "fixtures" / "v4_puzzle_task_seed_v1.json"
V4_PUZZLE_FAILURE = ROOT / "tests" / "fixtures" / "v4_puzzle_failure_memory_v1.json"
V5_CHALLENGE = ROOT / "tests" / "fixtures" / "v5_critical_operations_fixture_v1.json"
V6_REQUIRED_LANES = (
    ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_boundary_priority_review_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_structural_build_30_adopted_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_router_debate_adopted_benchmark_v1.json",
)
V6_DIAGNOSTIC_LANES = (
    ROOT / "tests" / "fixtures" / "v6_boundary_false_positive_candidate_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_contrast_negative_benchmark_v1.json",
    ROOT / "tests" / "fixtures" / "v6_router_debate_candidate_benchmark_v1.json",
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
        "HTTPヘッダーのETagは何を表しますか。",
        (("direct_response_request", "何を表しますか"),),
    ),
    Spec(
        "respond",
        "en",
        "Give a short definition of a feature flag.",
        (("direct_response_request", "Give"), ("short_response", "short")),
        response_length="short",
    ),
    Spec(
        "respond",
        "mixed",
        "In a README, what does the label beta usually mean?",
        (("direct_response_request", "what does"),),
    ),
    Spec(
        "respond",
        "ja",
        "Apache 2.0ライセンスとは何ですか。一般的な説明だけで大丈夫です。",
        (("direct_response_request", "何ですか"), ("low_risk_scope", "一般的な説明だけ")),
        must=("general_information_only",),
    ),
    Spec(
        "explain",
        "ja",
        "なぜキャッシュのTTLを短くすると負荷が増えることがありますか。",
        (("explanation_request", "なぜ"),),
    ),
    Spec(
        "explain",
        "en",
        "Explain how a retry storm can make an outage worse.",
        (("explanation_request", "Explain"),),
    ),
    Spec(
        "explain",
        "mixed",
        "Why can an AI persona feel helpful without implying the user is dependent?",
        (("explanation_request", "Why"), ("low_risk_scope", "without implying")),
    ),
    Spec(
        "explain",
        "ja",
        "医療AIのUI設計で、診断ではなく注意喚起が重要な理由を説明してください。",
        (("explanation_request", "理由を説明"), ("medical_boundary", "診断ではなく")),
        must=("avoid_diagnosis",),
    ),
    Spec(
        "clarify",
        "ja",
        "見積もりを出したいのですが、対象人数と期間が未定です。",
        (("missing_information", "未定"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Before drafting the migration plan, ask which services are in scope.",
        (("constraint_ask_first", "Before drafting"), ("missing_information", "which services")),
        operations=("clarify", "build"),
        missing=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "mixed",
        "Create the CSV export, but the required columns are not listed.",
        (("implementation_request", "Create"), ("missing_information", "not listed")),
        operations=("clarify", "build"),
        missing=True,
        multiple=True,
    ),
    Spec(
        "clarify",
        "ja",
        "現在の契約条項に違反があるか確認したいです。対象国が分かりません。",
        (("current_information", "現在の"), ("missing_information", "対象国が分かりません")),
        operations=("clarify", "verify"),
        missing=True,
        current=True,
        risk_level="high",
        risk_flags=("legal", "current_information"),
    ),
    Spec(
        "build",
        "ja",
        "READMEに`risk_note`という設定名を追加する短い説明文を作ってください。",
        (("implementation_request", "作ってください"), ("metalinguistic_label", "`risk_note`")),
        response_length="short",
    ),
    Spec(
        "build",
        "en",
        "Add a table column named latest_status for local workflow notes.",
        (("implementation_request", "Add"), ("local_reference", "local workflow")),
    ),
    Spec(
        "build",
        "mixed",
        "Make a checklist for reviewing AI chat boundary samples without escalating normal chat to risk.",
        (("implementation_request", "Make a checklist"), ("low_risk_scope", "without escalating")),
        formats=("bullets",),
    ),
    Spec(
        "build",
        "ja",
        "検証してから、議論ログを候補レビュー表に変換してください。",
        (("verification_request", "検証してから"), ("implementation_request", "変換してください")),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "verify",
        "ja",
        "今日のNode.js LTS版を公式情報で確認してください。",
        (("current_information", "今日の"), ("verification_request", "確認してください")),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether 18 * 24 equals 432 before I paste it into the report.",
        (("verification_request", "Check"), ("calculation_request", "18 * 24")),
        operations=("verify", "calculate"),
        unverified=True,
    ),
    Spec(
        "verify",
        "ja",
        "この医療助言が安全か、公式ガイドラインで確認してください。",
        (("medical_risk", "医療助言"), ("verification_request", "確認してください")),
        operations=("verify", "search"),
        unverified=True,
        current=True,
        must=("cite_sources",),
        risk_level="high",
        risk_flags=("medical", "current_information", "unverified_claim"),
    ),
    Spec(
        "verify",
        "mixed",
        "Verify whether Apache 2.0 permits commercial use; cite sources.",
        (("verification_request", "Verify"), ("constraint_cite_sources", "cite sources")),
        operations=("verify", "search"),
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("license",),
    ),
    Spec(
        "summarize",
        "ja",
        "この会議メモを3つの箇条書きで要約してください。",
        (("summary_request", "要約してください"), ("format_bullets", "箇条書き")),
        response_length="short",
        formats=("bullets",),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the debate log as JSON with decision and open_questions.",
        (("summary_request", "Summarize"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "summarize",
        "mixed",
        "Give a neutral summary of the political argument without choosing a side.",
        (("summary_request", "summary"), ("neutrality_constraint", "without choosing a side")),
        must=("preserve_neutrality",),
        risk_level="medium",
        risk_flags=("political",),
    ),
    Spec(
        "summarize",
        "ja",
        "表にせず、ログの時系列だけを短くまとめてください。",
        (("summary_request", "まとめてください"), ("constraint_no_table", "表にせず")),
        response_length="short",
        must_not=("no_table",),
    ),
    Spec(
        "explore",
        "ja",
        "AI人格化の軽症例と依存リスクの境界を比較してください。",
        (("exploration_request", "境界"), ("comparison_request", "比較してください")),
        operations=("explore", "compare"),
        risk_level="medium",
        risk_flags=("ai_dependency_boundary",),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm router themes that separate current-information questions from local file references.",
        (("exploration_request", "Brainstorm"), ("comparison_request", "separate")),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "mixed",
        "Compare two approaches: store knowledge in a library versus teaching every fact to the router.",
        (("comparison_request", "Compare"),),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "ja",
        "将来予測を断定しすぎないための回答方針を複数案で検討してください。",
        (("exploration_request", "検討してください"), ("overclaim_control", "断定しすぎない")),
        must=("avoid_overclaim",),
        risk_level="medium",
        risk_flags=("future_prediction",),
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
                "id": f"plm-sealed-v6-{spec.intent}-{counters[spec.intent]:02d}",
                "split": "sealed",
                "source_group": "plm-sealed-v6-authored",
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
        "fixture_id": "pattern-language-sealed-v6",
        "frozen_at": "2026-06-24T09:10:00+00:00",
        "predecessor": "pattern_language_sealed_v5.json",
        "authoring_method": (
            "specification-derived successor authored after V6 non-sealed "
            "replay gate and sealed rotation review; not evaluated, tuned "
            "against, or opened in the review UI"
        ),
        "policy": (
            "sealed measurement only; evaluate once, record the result, then "
            "mark consumed and rotate before any tuning"
        ),
        "cases": cases,
    }
    fixture = parse_plm_sealed_fixture(payload)
    if len(fixture.cases) != 28:
        raise ValueError("sealed v6 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v6 must contain four cases per intent")
    return payload


def validate_no_overlap(payload: dict) -> None:
    new_texts = {case["input"] for case in payload["cases"]}
    if len(new_texts) != len(payload["cases"]):
        raise ValueError("sealed v6 contains duplicate inputs")
    overlap_sources = {
        "PLM benchmark v1": _texts_from_json(V1_BENCHMARK),
        "legacy sealed boundary v2": _texts_from_json(LEGACY_SEALED),
        "PLM sealed v2": _texts_from_json(SEALED_V2),
        "PLM sealed v3": _texts_from_json(SEALED_V3),
        "PLM sealed v4": _texts_from_json(SEALED_V4),
        "PLM sealed v5": _texts_from_json(SEALED_V5),
        "V4 failure memory": _texts_from_json(V4_FAILURE_MEMORY),
        "V4 puzzle seed": _texts_from_json(V4_PUZZLE_SEED),
        "V4 puzzle failure memory": _texts_from_json(V4_PUZZLE_FAILURE),
        "V5 non-sealed challenge": _texts_from_json(V5_CHALLENGE),
        "intent corpus quarantine": _texts_from_json(QUARANTINE),
        "approved Pattern DB": _approved_texts(),
    }
    for index, path in enumerate(V6_REQUIRED_LANES, start=1):
        overlap_sources[f"V6 required lane {index}"] = _texts_from_json(path)
    for index, path in enumerate(V6_DIAGNOSTIC_LANES, start=1):
        overlap_sources[f"V6 diagnostic lane {index}"] = _texts_from_json(path)

    for label, texts in overlap_sources.items():
        overlap = sorted(new_texts & texts)
        if overlap:
            raise ValueError(f"sealed v6 overlaps {label}: {overlap[0]!r}")


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
