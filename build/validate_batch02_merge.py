"""Prove batch-02 staging merges cleanly WITHOUT writing the frozen campaign.

Builds a throwaway merged campaign dict (real header + existing + staged
cases, with the staging-only `_label_note` keys stripped) and runs the
strict contract parser. Reports the merged count and category balance.
"""

import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing import build_processing_plan, extract_semantic_packet
from semantic_routing.conversation_accumulation import (
    parse_conversation_accumulation,
)

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
STAGING = ROOT / "build" / "batch02_staging.json"
BENCHMARK = ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"

CASE_FIELDS = {
    "id", "batch", "collected_at", "category", "language",
    "input", "expected", "critical_underprocessing", "review_status",
}


def main() -> None:
    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    staging = json.loads(STAGING.read_text(encoding="utf-8"))

    staged = [
        {key: case[key] for key in CASE_FIELDS}
        for case in staging["cases"]
    ]
    merged = dict(campaign)
    merged["cases"] = list(campaign["cases"]) + staged

    parsed = parse_conversation_accumulation(merged)  # raises on any violation
    print("merge validates OK")
    print("cases:", len(campaign["cases"]), "->", len(parsed.cases))
    print(
        "category balance:",
        dict(Counter(case.category for case in parsed.cases)),
    )

    # Contamination: no staged input may appear in the visible benchmark.
    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    visible = {
        case["input"]
        for case in benchmark["cases"]
        if case["split"] in {"train", "validation"}
    }
    overlap = sorted(visible & {case["input"] for case in staged})
    print("visible-benchmark overlap:", overlap or "none")
    assert not overlap, "staged case overlaps the visible benchmark"

    # Informational only: where the current adapter stands on the staged
    # cases. We do NOT tune to these (same_batch_tuning forbidden).
    correct = 0
    for case in staged:
        packet = extract_semantic_packet(case["input"])
        plan = build_processing_plan(packet)
        exp = case["expected"]
        ok = (
            packet.primary_intent == exp["intent"]
            and plan.processing_class == exp["processing_class"]
            and plan.core_mode == exp["core_mode"]
        )
        correct += ok
    print(
        f"current adapter on staged (informational, not tuned): "
        f"{correct}/{len(staged)}"
    )

    # campaign file is untouched
    assert json.loads(CAMPAIGN.read_text(encoding="utf-8")) == campaign
    print("frozen campaign file untouched:", True)


if __name__ == "__main__":
    main()
