"""Audit: is the route()/baseline measurement real, or served by the snapshot?

This is a read-only diagnostic (writes one report JSON). It answers two
questions the V11 status audit raised about baseline_snapshot.py:

  1. Coverage: how many sealed-v10 eval inputs are served from the
     LEGACY_PACKET_BY_DIGEST exact-match snapshot instead of the regex path?
  2. Regex-only capability: if the snapshot is disabled, what does route()
     actually score on the sealed-v10 corpus, and does the recovered regex
     still reproduce the pyc oracle (the *non-circular* recovery test)?

It does not mutate any tracked source; the snapshot-off measurements use the
use_legacy_snapshot gate (S5) rather than mutating module state.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from semantic_routing import baseline, parse_plm_sealed_fixture, route  # noqa: E402
from semantic_routing.evaluation import evaluate_plm_extractor  # noqa: E402
from semantic_routing.semantic_packet import request_digest  # noqa: E402

SEALED_V10 = ROOT / "tests" / "fixtures" / "pattern_language_sealed_v10.json"
ORACLE = ROOT / "build" / "baseline_source_recovery_oracle_v1.json"
OUT = ROOT / "build" / "audit_baseline_snapshot_oracle_validity_v1.json"

METRIC_KEYS = (
    "intent_accuracy",
    "critical_signal_recall",
    "operation_exact_match",
    "constraint_exact_match",
    "risk_exact_match",
)


def _metrics(report: dict) -> dict:
    return {k: report.get(k) for k in METRIC_KEYS}


def main() -> None:
    fixture = parse_plm_sealed_fixture(json.loads(SEALED_V10.read_text(encoding="utf-8")))
    cases = list(fixture.cases)

    # (1) snapshot coverage of the eval corpus
    in_snapshot = [c for c in cases if request_digest(c.input_text) in baseline.LEGACY_PACKET_BY_DIGEST]
    coverage = {
        "eval_case_count": len(cases),
        "served_from_snapshot": len(in_snapshot),
        "served_from_regex": len(cases) - len(in_snapshot),
        "snapshot_coverage_rate": round(len(in_snapshot) / len(cases), 6) if cases else 0.0,
        "total_snapshot_entries": len(baseline.LEGACY_PACKET_BY_DIGEST),
    }

    # (2a) measured metrics WITH snapshot (current behaviour)
    metrics_on = _metrics(evaluate_plm_extractor(cases, lambda t: route(t, use_legacy_snapshot=True).packet))

    # (2b) measured metrics with snapshot gated OFF (true regex/router capability)
    metrics_off = _metrics(evaluate_plm_extractor(cases, lambda t: route(t, use_legacy_snapshot=False).packet))

    # (3) NON-circular recovery test: does the regex reproduce the pyc oracle
    # when the snapshot is gated off for it?
    oracle_real = None
    if ORACLE.exists():
        oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
        core_fields = ("intent_candidates", "operations", "information_state", "constraints", "risk")

        def _core(p: dict) -> dict:
            out = {}
            for f in core_fields:
                out[f] = p.get(f)
            # primary intent only (ignore confidence noise) for a softer view
            ic = p.get("intent_candidates") or []
            out["_primary_intent"] = ic[0]["intent"] if ic else None
            return out

        full_mism = 0
        core_mism = 0
        intent_mism = 0
        total = 0
        for item in oracle["outputs"]:
            total += 1
            actual = baseline.extract_semantic_packet(item["input"], use_legacy_snapshot=False).as_dict()
            expected = dict(item["packet"])
            a = dict(actual)
            a.pop("request_digest", None)
            e = dict(expected)
            e.pop("request_digest", None)
            if a != e:
                full_mism += 1
            if _core(actual) != _core(expected):
                core_mism += 1
            ai = (actual.get("intent_candidates") or [{}])[0].get("intent")
            ei = (expected.get("intent_candidates") or [{}])[0].get("intent")
            if ai != ei:
                intent_mism += 1
        oracle_real = {
            "oracle_case_count": total,
            "regex_only_full_packet_mismatch_count": full_mism,
            "regex_only_core_field_mismatch_count": core_mism,
            "regex_only_primary_intent_mismatch_count": intent_mism,
            "regex_only_full_match_rate": round((total - full_mism) / total, 6) if total else 0.0,
            "regex_only_core_match_rate": round((total - core_mism) / total, 6) if total else 0.0,
            "regex_only_primary_intent_match_rate": round((total - intent_mism) / total, 6) if total else 0.0,
            "note": "Committed compare_baseline_source_recovery_oracle.py runs WITH "
            "the snapshot, comparing snapshot output against the pyc the snapshot "
            "was built from -> trivially 0 mismatches. These rows gate the snapshot "
            "off to test whether the recovered regex itself reproduces the pyc.",
        }

    deltas = {k: round((metrics_off[k] or 0) - (metrics_on[k] or 0), 6) for k in METRIC_KEYS}

    report = {
        "schema_version": "audit-baseline-snapshot-oracle-validity.v1",
        "eval_fixture": SEALED_V10.name,
        "snapshot_coverage": coverage,
        "measured_metrics_with_snapshot": metrics_on,
        "measured_metrics_regex_only": metrics_off,
        "metric_delta_regex_minus_snapshot": deltas,
        "oracle_recovery_noncircular": oracle_real,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
