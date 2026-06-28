"""Generate the unopened successor PLM sealed fixture v3.

The fixture is authored after sealed v2 measurement, but it does not reuse v2
texts and is not evaluated here. It is a fresh sealed measurement target for a
future adapter revision.
"""

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import parse_plm_sealed_fixture  # noqa: E402


OUTPUT = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v3.json"
V1_BENCHMARK = (
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
LEGACY_SEALED = (
    ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json"
)
SEALED_V2 = (
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
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
        "en",
        "Which header usually carries a bearer token in an HTTP request?",
        (("direct_response_request", "Which"),),
    ),
    Spec(
        "respond",
        "en",
        "Give me a concise definition of eventual consistency.",
        (
            ("direct_response_request", "Give me"),
            ("short_response", "concise"),
        ),
        response_length="short",
    ),
    Spec(
        "respond",
        "mixed",
        "In a PR review, tell me what LGTM normally means.",
        (("direct_response_request", "tell me"),),
    ),
    Spec(
        "respond",
        "en",
        "Name the command commonly used to inspect Git history.",
        (("direct_response_request", "Name the"),),
    ),
    Spec(
        "explain",
        "en",
        "Explain how idempotency keys prevent duplicate payments.",
        (("explanation_request", "Explain"),),
    ),
    Spec(
        "explain",
        "en",
        "Walk me through why a queue consumer might process the same message twice.",
        (("explanation_request", "Walk me through"),),
    ),
    Spec(
        "explain",
        "mixed",
        "In OAuth, describe how the refresh token flow works.",
        (("explanation_request", "describe how"),),
    ),
    Spec(
        "explain",
        "en",
        "Why can a cache stampede overload the database after a deploy?",
        (("explanation_request", "Why"),),
    ),
    Spec(
        "clarify",
        "en",
        "Estimate monthly storage cost, but the object count has not been provided.",
        (("missing_information", "not been provided"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Before writing the migration command, ask first which database engine is running.",
        (
            ("constraint_ask_first", "Before writing"),
            ("missing_information", "which database engine"),
        ),
        missing=True,
        must=("ask_first",),
    ),
    Spec(
        "clarify",
        "en",
        "I need an alert rule, but the target error budget is not stated.",
        (("missing_information", "not stated"),),
        missing=True,
    ),
    Spec(
        "clarify",
        "en",
        "Calculate the refund amount, but the original payment total is missing.",
        (("missing_information", "missing"),),
        operations=("clarify", "calculate"),
        missing=True,
    ),
    Spec(
        "build",
        "en",
        "Create an implementation plan for rotating the API keys.",
        (("implementation_request", "implementation plan"),),
    ),
    Spec(
        "build",
        "en",
        "Validate the proposed rollout and then produce a rollback checklist.",
        (
            ("verification_request", "Validate"),
            ("unverified_claim", "proposed"),
            ("implementation_request", "rollback checklist"),
        ),
        operations=("build", "verify"),
        unverified=True,
        multiple=True,
    ),
    Spec(
        "build",
        "en",
        "Turn these requirements into ordered tasks for the release.",
        (("implementation_request", "ordered tasks"),),
    ),
    Spec(
        "build",
        "mixed",
        "Review the assumptions and then prepare the deployment runbook.",
        (
            ("verification_request", "Review"),
            ("implementation_request", "prepare"),
        ),
        operations=("build", "verify"),
        multiple=True,
    ),
    Spec(
        "verify",
        "en",
        "Verify the current SOC 2 status with sources before recommending the vendor.",
        (
            ("verification_request", "Verify"),
            ("current_information", "current"),
            ("constraint_cite_sources", "with sources"),
        ),
        operations=("verify", "search"),
        current=True,
        must=("cite_sources",),
        risk_level="medium",
        risk_flags=("current_information",),
    ),
    Spec(
        "verify",
        "en",
        "Check whether the reported invoice totals match the ledger.",
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
        "Is this legal clause still valid under current California privacy law?",
        (
            ("legal_risk", "legal"),
            ("verification_request", "valid"),
            ("current_information", "current"),
        ),
        operations=("verify", "search"),
        current=True,
        risk_level="high",
        risk_flags=("legal", "current_information"),
    ),
    Spec(
        "verify",
        "en",
        "Validate the proposed medication dosage against the latest label.",
        (
            ("verification_request", "Validate"),
            ("unverified_claim", "proposed"),
            ("medical_risk", "medication"),
            ("current_information", "latest"),
        ),
        operations=("verify", "search"),
        unverified=True,
        current=True,
        risk_level="high",
        risk_flags=("medical", "current_information", "unverified_claim"),
    ),
    Spec(
        "summarize",
        "en",
        "Summarize the incident timeline in three lines.",
        (
            ("summary_request", "Summarize"),
            ("short_response", "three lines"),
        ),
        response_length="short",
    ),
    Spec(
        "summarize",
        "en",
        "Condense the meeting notes into bullet points without using a table.",
        (
            ("summary_request", "Condense"),
            ("format_bullets", "bullet points"),
            ("constraint_no_table", "without using a table"),
        ),
        response_length="short",
        formats=("bullets",),
        must_not=("no_table",),
    ),
    Spec(
        "summarize",
        "en",
        "Give a neutral recap of the policy argument.",
        (("summary_request", "recap"),),
        must=("preserve_neutrality",),
    ),
    Spec(
        "summarize",
        "mixed",
        "Summarize the release notes as JSON.",
        (
            ("summary_request", "Summarize"),
            ("format_json", "JSON"),
        ),
        formats=("json",),
    ),
    Spec(
        "explore",
        "en",
        "Brainstorm alternatives to reduce build time and compare the trade-offs.",
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
        "Compare three options for handling retries without overclaiming a winner.",
        (("exploration_request", "Compare three options"),),
        operations=("explore", "compare"),
        must=("avoid_overclaim",),
    ),
    Spec(
        "explore",
        "en",
        "List possible strategies for lowering cloud cost, and then compare risks.",
        (
            ("exploration_request", "possible strategies"),
            ("comparison_request", "compare risks"),
        ),
        operations=("explore", "compare"),
        multiple=True,
    ),
    Spec(
        "explore",
        "mixed",
        "The current design is supposedly perfect; suggest other ways and point out weaknesses.",
        (
            ("exploration_request", "other ways"),
            ("comparison_request", "point out"),
        ),
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
    return sorted(
        result,
        key=lambda item: (item["start"], item["end"], item["signal"]),
    )


def _texts_from_json(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(case["input"]) for case in payload["cases"]}


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
                    f"plm-sealed-v3-{spec.intent}-"
                    f"{counters[spec.intent]:02d}"
                ),
                "split": "sealed",
                "source_group": "plm-sealed-v3-authored",
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
        "fixture_id": "pattern-language-sealed-v3",
        "frozen_at": "2026-06-18T12:00:00+00:00",
        "predecessor": "pattern_language_sealed_v2.json",
        "authoring_method": (
            "specification-derived successor authored after v2 measurement; "
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
        raise ValueError("sealed v3 must contain exactly 28 cases")
    if set(counters.values()) != {4} or len(counters) != 7:
        raise ValueError("sealed v3 must contain four cases per intent")

    new_texts = {case.input_text for case in fixture.cases}
    if len(new_texts) != len(fixture.cases):
        raise ValueError("sealed v3 contains duplicate inputs")

    overlap_sources = {
        "PLM benchmark v1": _texts_from_json(V1_BENCHMARK),
        "legacy sealed boundary v2": _texts_from_json(LEGACY_SEALED),
        "PLM sealed v2": _texts_from_json(SEALED_V2),
        "approved Pattern DB": _approved_texts(),
    }
    for label, texts in overlap_sources.items():
        overlap = sorted(new_texts & texts)
        if overlap:
            raise ValueError(f"sealed v3 overlaps {label}: {overlap[0]!r}")

    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)} with {len(cases)} cases")


if __name__ == "__main__":
    main()
