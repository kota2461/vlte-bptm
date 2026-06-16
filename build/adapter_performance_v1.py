"""Adapter performance + integrity check on the frozen 50-case campaign.

MEASUREMENT ONLY. Runs the deterministic adapter (extract -> plan) over the
campaign and breaks accuracy down by category / source / language, lists the
misses, and times the adapter. Labels are still DRAFT (not human-ratified),
so this is a provisional pre-review baseline. The adapter is never tuned to
these cases (same_batch_tuning forbidden); sealed v2 is not touched.
"""

import io
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import build_processing_plan, extract_semantic_packet
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
    parse_conversation_accumulation,
)

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
STAGING = ROOT / "build" / "batch02_staging.json"
BENCHMARK = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
OUT = ROOT / "build" / "adapter_performance_v1_report.json"


def _rate(num, den):
    return round(num / den, 4) if den else 0.0


def main() -> None:
    # --- integrity (確認) ---
    raw = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    campaign = parse_conversation_accumulation(raw)  # round-trips / validates
    assert campaign.as_dict() == raw, "campaign does not round-trip"
    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    visible = {
        c["input"] for c in benchmark["cases"]
        if c["split"] in {"train", "validation"}
    }
    overlap = visible & {c.input_text for c in campaign.cases}
    print("== integrity ==")
    print("cases:", len(campaign.cases), "status:", campaign.status)
    print("round-trips:", True, "| visible-benchmark overlap:", overlap or "none")
    assert not overlap

    # source per id (batch-01 = original; batch-02 from staging _source)
    source_by_id = {c.case_id: "original_batch01" for c in campaign.cases}
    for c in json.loads(STAGING.read_text(encoding="utf-8"))["cases"]:
        source_by_id[c["id"]] = c.get("_source", "unknown")

    # --- accuracy (性能) ---
    agg = {
        "overall": defaultdict(int),
        "by_category": defaultdict(lambda: defaultdict(int)),
        "by_source": defaultdict(lambda: defaultdict(int)),
        "by_language": defaultdict(lambda: defaultdict(int)),
    }
    misses = []
    for case in campaign.cases:
        packet = extract_semantic_packet(case.input_text)
        plan = build_processing_plan(packet)
        sem = packet.primary_intent == case.expected.intent
        plan_ok = (
            plan.processing_class == case.expected.processing_class
            and plan.core_mode == case.expected.core_mode
        )
        e2e = sem and plan_ok
        crit = case.critical_underprocessing and not e2e
        src = source_by_id.get(case.case_id, "unknown")
        for scope, key in (
            ("overall", None),
            ("by_category", case.category),
            ("by_source", src),
            ("by_language", case.language),
        ):
            bucket = agg[scope] if key is None else agg[scope][key]
            bucket["n"] += 1
            bucket["semantic"] += sem
            bucket["plan"] += plan_ok
            bucket["e2e"] += e2e
            bucket["critical"] += crit
        if not e2e:
            misses.append({
                "id": case.case_id,
                "source": src,
                "category": case.category,
                "expected": case.expected.as_dict(),
                "actual": {
                    "intent": packet.primary_intent,
                    "processing_class": plan.processing_class,
                    "core_mode": plan.core_mode,
                },
                "critical": crit,
                "input": case.input_text,
            })

    # --- latency (性能: speed) ---
    reps = 20
    start = time.perf_counter()
    for _ in range(reps):
        for case in campaign.cases:
            build_processing_plan(extract_semantic_packet(case.input_text))
    elapsed = time.perf_counter() - start
    per_request_ms = elapsed / (reps * len(campaign.cases)) * 1000

    def fmt(b):
        return {
            "n": b["n"],
            "semantic_intent": _rate(b["semantic"], b["n"]),
            "processing_plan": _rate(b["plan"], b["n"]),
            "end_to_end": _rate(b["e2e"], b["n"]),
            "critical_underprocessing": b["critical"],
        }

    report = {
        "schema_version": "adapter-performance.v1",
        "note": "draft labels (pre-review baseline); adapter not tuned to these",
        "overall": fmt(agg["overall"]),
        "by_category": {k: fmt(v) for k, v in sorted(agg["by_category"].items())},
        "by_source": {k: fmt(v) for k, v in sorted(agg["by_source"].items())},
        "by_language": {k: fmt(v) for k, v in sorted(agg["by_language"].items())},
        "latency_ms_per_request": round(per_request_ms, 4),
        "miss_count": len(misses),
        "misses": misses,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")

    print("\n== overall ==", json.dumps(fmt(agg["overall"]), ensure_ascii=False))
    print(f"latency: {per_request_ms:.3f} ms/request (deterministic)")
    print("\n== by category ==")
    for k, v in sorted(agg["by_category"].items()):
        f = fmt(v)
        print(f"  {k:24s} e2e {f['end_to_end']:.2f}  sem {f['semantic_intent']:.2f}"
              f"  plan {f['processing_plan']:.2f}  crit {f['critical_underprocessing']} /{f['n']}")
    print("\n== by source ==")
    for k, v in sorted(agg["by_source"].items()):
        f = fmt(v)
        print(f"  {k:26s} e2e {f['end_to_end']:.2f}  ({f['n']} cases, crit {f['critical_underprocessing']})")
    print("\n== by language ==")
    for k, v in sorted(agg["by_language"].items()):
        f = fmt(v)
        print(f"  {k:8s} e2e {f['end_to_end']:.2f}  ({f['n']} cases)")
    print(f"\nreport: {OUT}")


if __name__ == "__main__":
    main()
