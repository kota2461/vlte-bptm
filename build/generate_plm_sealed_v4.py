"""Generate the unopened successor PLM sealed fixture v4.

The fixture is authored after V3 sealed measurement and V4 failure-memory
review. It does not reuse V1/V2/V3 sealed or visible benchmark texts and is not
evaluated here. It is a fresh sealed measurement target for the next adapter
revision.
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


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v4.json"
V1_BENCHMARK = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
LEGACY_SEALED = ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json"
SEALED_V2 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
SEALED_V3 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v3.json"
V4_FAILURE_MEMORY = ROOT / "tests" / "fixtures" / "v4_failure_memory_fixture_v1.json"
V4_PUZZLE_SEED = ROOT / "tests" / "fixtures" / "v4_puzzle_task_seed_v1.json"
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
        "en",
        "What does a 409 Conflict response usually indicate in an API?",
        (("direct_response_request", "What does"),),
    ),
    Spec(
        "respond",
        "en",
        "Give a short definition of cache invalidation.",
        (("direct_response_request", "Give"), ("short_response", "short")),
        response_length="short",
    ),
    Spec(
        "respond",
        "mixed",
        "In a code review, what does NIT usually mean?",
        (("direct_response_request", "what does"),),
    ),
    Spec(
        "respond",
        "en",
        "Name the HTTP method commonly used for partial updates.",
        (("direct_response_request", "Name"),),
    ),
    Spec(
        "explain",
        "en",
        "Explain why optimistic locking can prevent lost updates.",
        (("explanation_request", "Explain"),),
    ),
    Spec(
        "explain",
        "en",
        "Walk through how exponential backoff reduces retry storms.",
        (("explanation_request", "Walk through"),),
    ),
    Spec(
        "explain",
        "en",
        "Describe why idempotent webhooks are easier to replay safely.",
        (("explanation_request", "Describe why"),),
    ),
    Spec(
        "explain",
        "en",
        "Why can clock skew cause token validation failures?",
        (("explanation_request", "Why"),),
    ),
    Spec(
        "clarify",
        "en",
        "Calculate the monthly API cost, but the request volume is not provided.",
        (("missing_information", "not provided"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Before drafting the rollback command, ask which cluster should receive it.",
        (("constraint_ask_first", "Before drafting"), ("missing_information", "ask which cluster")),
        missing=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "I need a migration estimate, but the database size is missing.",
        (("missing_information", "missing"),),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Estimate the backup window; the transfer speed is not stated.",
        (("missing_information", "not stated"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "build",
        "en",
        "Create a rollout checklist for enabling feature flags.",
        (("implementation_request", "Create"),),
    ),
    Spec(
        "build",
        "en",
        "Review the proposed caching approach and then produce an implementation plan.",
        (("verification_request", "Review"), ("unverified_claim", "proposed"), ("implementation_request", "implementation plan")),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "build",
        "en",
        "Turn these acceptance criteria into ordered engineering tasks.",
        (("implementation_request", "ordered engineering tasks"),),
    ),
    Spec(
        "build",
        "en",
        "Validate the draft API contract before preparing the integration plan.",
        (("verification_request", "Validate"), ("unverified_claim", "draft"), ("implementation_request", "integration plan")),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify the latest Node.js LTS version with sources before updating the docs.",
        (("verification_request", "Verify"), ("current_information", "latest"), ("constraint_cite_sources", "with sources")),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether the reported subtotal equals the line items.",
        (("verification_request", "Check"), ("unverified_claim", "reported")),
        operations=("verify", "calculate"),
        unverified=True,
    ),
    Spec(
        "verify",
        "en",
        "Confirm whether this privacy policy clause is still valid under current EU law.",
        (("legal_risk", "privacy policy"), ("verification_request", "Confirm"), ("current_information", "current")),
        operations=("verify", "search"),
        current=True,
        risk_level="high",
        risk_flags=("legal", "current_information"),
    ),
    Spec(
        "verify",
        "en",
        "Validate the proposed insulin dosage against the official label before responding.",
        (("verification_request", "Validate"), ("unverified_claim", "proposed"), ("medical_risk", "insulin dosage")),
        operations=("verify", "search"),
        unverified=True,
        current=True,
        risk_level="high",
        risk_flags=("medical", "current_information", "unverified_claim"),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the outage notes in exactly three bullets.",
        (("summary_request", "Summarize"), ("short_response", "three bullets"), ("format_bullets", "bullets")),
        response_length="short",
        formats=("bullets",),
    ),
    Spec(
        "summarize",
        "en",
        "Condense this design memo into JSON.",
        (("summary_request", "Condense"), ("format_json", "JSON")),
        formats=("json",),
    ),
    Spec(
        "summarize",
        "en",
        "Give a neutral recap of the budget disagreement.",
        (("summary_request", "recap"),),
        must=("preserve_neutrality",),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the meeting transcript without using a table.",
        (("summary_request", "Summarize"), ("constraint_no_table", "without using a table")),
        must_not=("no_table",),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm ways to reduce memory usage and compare trade-offs.",
        (("exploration_request", "Brainstorm"), ("comparison_request", "compare trade-offs")),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "en",
        "Compare options for launch timing without overclaiming the best choice.",
        (("exploration_request", "Compare options"),),
        operations=("explore", "compare"),
        must=("avoid_overclaim",),
    ),
    Spec(
        "explore",
        "en",
        "List alternative database designs and compare migration risks.",
        (("exploration_request", "alternative database designs"), ("comparison_request", "compare migration risks")),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "en",
        "The proposed architecture is supposedly flawless; suggest weaknesses and alternatives.",
        (("unverified_claim", "supposedly"), ("exploration_request", "alternatives")),
        operations=("explore", "compare"),
        unverified=True,
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
    for case in payload.get("cases", []):
        for key in keys:
            if key in case:
                texts.add(str(case[key]))
    for case in payload.get("tasks", []):
        for key in keys:
            if key in case:
                texts.add(str(case[key]))
    for case in payload.get("items", []):
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
                "id": f"plm-sealed-v4-{spec.intent}-{counters[spec.intent]:02d}",
                "split": "sealed",
                "source_group": "plm-sealed-v4-authored",
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
        "fixture_id": "pattern-language-sealed-v4",
        "frozen_at": "2026-06-21T06:00:00+00:00",
        "predecessor": "pattern_language_sealed_v3.json",
        "authoring_method": (
            "specification-derived successor authored after V3 measurement and V4 "
            "non-sealed failure-memory evaluation; not evaluated, tuned against, "
            "or opened in the review UI"
        ),
        "policy": (
            "sealed measurement only; evaluate once, record the result, then "
            "mark consumed and rotate before any tuning"
        ),
        "cases": cases,
    }
    fixture = parse_plm_sealed_fixture(payload)
    if len(fixture.cases) != 28:
        raise ValueError("sealed v4 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v4 must contain four cases per intent")
    return payload


def validate_no_overlap(payload: dict) -> None:
    new_texts = {case["input"] for case in payload["cases"]}
    if len(new_texts) != len(payload["cases"]):
        raise ValueError("sealed v4 contains duplicate inputs")
    overlap_sources = {
        "PLM benchmark v1": _texts_from_json(V1_BENCHMARK),
        "legacy sealed boundary v2": _texts_from_json(LEGACY_SEALED),
        "PLM sealed v2": _texts_from_json(SEALED_V2),
        "PLM sealed v3": _texts_from_json(SEALED_V3),
        "V4 failure memory": _texts_from_json(V4_FAILURE_MEMORY),
        "V4 puzzle seed": _texts_from_json(V4_PUZZLE_SEED),
        "approved Pattern DB": _approved_texts(),
    }
    for label, texts in overlap_sources.items():
        overlap = sorted(new_texts & texts)
        if overlap:
            raise ValueError(f"sealed v4 overlaps {label}: {overlap[0]!r}")


def main() -> None:
    payload = build_payload()
    validate_no_overlap(payload)
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)} with {len(payload['cases'])} cases")


if __name__ == "__main__":
    main()
