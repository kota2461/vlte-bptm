"""Evaluate the deterministic PLM baseline without opening the sealed split."""

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import (
    evaluate_plm_extractor,
    extract_semantic_packet,
    load_plm_benchmark,
)


BENCHMARK_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
ACTIVE_SEALED_PATH = (
    ROOT / "tests" / "fixtures" / "sealed_boundary_slice_v2.json"
)
ACTIVE_PLM_SEALED_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
)
DATABASE_PATH = ROOT / "data" / "pattern_lab.db"
OUTPUT_PATH = ROOT / "build" / "plm_baseline_v0_1_report.json"


def _approved_pattern_texts(path: Path) -> set[str]:
    if not path.exists():
        return set()
    uri = path.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        rows = connection.execute("SELECT input_text FROM patterns").fetchall()
    return {str(row[0]) for row in rows}


def _sealed_texts(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(case["input"]) for case in payload["cases"]}


def main() -> None:
    benchmark_bytes = BENCHMARK_PATH.read_bytes()
    benchmark = load_plm_benchmark(BENCHMARK_PATH)
    train = benchmark.cases_for_splits(("train",))
    validation = benchmark.cases_for_splits(("validation",))
    visible = benchmark.cases_for_splits()
    visible_texts = {case.input_text for case in visible}
    approved_overlap = sorted(
        visible_texts & _approved_pattern_texts(DATABASE_PATH)
    )
    active_sealed_overlap = sorted(
        visible_texts & _sealed_texts(ACTIVE_SEALED_PATH)
    )
    active_plm_sealed_overlap = sorted(
        visible_texts & _sealed_texts(ACTIVE_PLM_SEALED_PATH)
    )

    report = {
        "schema_version": "pattern-language-baseline-report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark": {
            "path": str(BENCHMARK_PATH.relative_to(ROOT)),
            "sha256": hashlib.sha256(benchmark_bytes).hexdigest(),
            "review_status": benchmark.review_status,
            "total_case_count": len(benchmark.cases),
            "evaluated_splits": ["train", "validation"],
            "evaluated_case_count": len(visible),
            "sealed_case_count": len(
                benchmark.cases_for_splits(("sealed",))
            ),
            "sealed_status": "consumed",
            "sealed_successor": "pattern_language_sealed_v2.json",
            "sealed_evaluated": False,
        },
        "adapter": {
            "kind": "deterministic_signal_extractor",
            "version": "0.1",
        },
        "data_isolation": {
            "approved_pattern_overlap_count": len(approved_overlap),
            "approved_pattern_overlap": approved_overlap,
            "active_sealed_v2_overlap_count": len(active_sealed_overlap),
            "active_sealed_v2_overlap": active_sealed_overlap,
            "active_plm_sealed_v2_overlap_count": len(
                active_plm_sealed_overlap
            ),
            "active_plm_sealed_v2_overlap": active_plm_sealed_overlap,
        },
        "measurements": {
            "train": evaluate_plm_extractor(
                train,
                extract_semantic_packet,
            ),
            "validation": evaluate_plm_extractor(
                validation,
                extract_semantic_packet,
            ),
            "visible_combined": evaluate_plm_extractor(
                visible,
                extract_semantic_packet,
            ),
        },
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
