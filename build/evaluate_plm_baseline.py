"""Evaluate the deterministic PLM baseline without opening the sealed split."""

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import (
    evaluate_plm_extractor,
    extract_semantic_packet,
    load_plm_benchmark,
)
from semantic_routing.reproducibility import reproducible_now_iso


BENCHMARK_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
GATE_REGISTRY_PATH = (
    ROOT / "tests" / "fixtures" / "gate_fixture_registry.json"
)
CONSUMED_PLM_SEALED_V2_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
)
REGISTRY_PATH = (
    ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
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


def _active_plm_sealed(registry: dict) -> tuple[str, dict] | None:
    active = [
        (name, entry)
        for name, entry in registry["fixtures"].items()
        if entry.get("role") == "sealed measurement only"
        and entry.get("status") == "active"
    ]
    if len(active) > 1:
        raise ValueError("expected at most one active PLM sealed fixture")
    return active[0] if active else None


def _active_boundary_sealed(registry: dict) -> tuple[str, dict]:
    active = [
        (name, entry)
        for name, entry in registry["fixtures"].items()
        if entry.get("role") == "sealed measurement only; NOT a promotion gate check"
        and entry.get("status") == "active"
    ]
    if len(active) != 1:
        raise ValueError("expected exactly one active boundary sealed fixture")
    return active[0]


def main() -> None:
    benchmark_bytes = BENCHMARK_PATH.read_bytes()
    benchmark = load_plm_benchmark(BENCHMARK_PATH)
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    gate_registry = json.loads(GATE_REGISTRY_PATH.read_text(encoding="utf-8"))
    active_plm_sealed = _active_plm_sealed(registry)
    if active_plm_sealed is None:
        active_plm_sealed_name = None
        active_plm_sealed_entry = None
    else:
        active_plm_sealed_name, active_plm_sealed_entry = active_plm_sealed
    active_boundary_name, active_boundary = _active_boundary_sealed(gate_registry)
    train = benchmark.cases_for_splits(("train",))
    validation = benchmark.cases_for_splits(("validation",))
    visible = benchmark.cases_for_splits()
    visible_texts = {case.input_text for case in visible}
    approved_overlap = sorted(
        visible_texts & _approved_pattern_texts(DATABASE_PATH)
    )
    consumed_plm_sealed_v2_overlap = sorted(
        visible_texts & _sealed_texts(CONSUMED_PLM_SEALED_V2_PATH)
    )
    report = {
        "schema_version": "pattern-language-baseline-report.v1",
        "generated_at": reproducible_now_iso(),
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
            "sealed_successor": "pattern_language_sealed_v3.json",
            "sealed_evaluated": False,
        },
        "adapter": {
            "kind": "deterministic_signal_extractor",
            "version": "0.1",
        },
        "data_isolation": {
            "approved_pattern_overlap_count": len(approved_overlap),
            "approved_pattern_overlap": approved_overlap,
            "active_sealed_v2_opened": False,
            "active_sealed_v2_name": active_boundary_name,
            "active_sealed_v2_sha256": active_boundary["sha256"],
            "active_sealed_v2_status": active_boundary["status"],
            "active_sealed_v2_overlap_checked": False,
            "active_sealed_v2_overlap_count": None,
            "active_sealed_v2_overlap": None,
            "active_sealed_v2_overlap_check_skipped_reason": (
                "active sealed boundary fixture remains unopened"
            ),
            "consumed_plm_sealed_v2_overlap_count": len(
                consumed_plm_sealed_v2_overlap
            ),
            "consumed_plm_sealed_v2_overlap": (
                consumed_plm_sealed_v2_overlap
            ),
            "active_plm_sealed_available": active_plm_sealed_entry is not None,
            "active_plm_sealed_opened": False,
            "active_plm_sealed_name": active_plm_sealed_name,
            "active_plm_sealed_sha256": (
                active_plm_sealed_entry["sha256"]
                if active_plm_sealed_entry is not None
                else None
            ),
            "active_plm_sealed_status": (
                active_plm_sealed_entry["status"]
                if active_plm_sealed_entry is not None
                else None
            ),
            "active_plm_sealed_measured": (
                active_plm_sealed_entry["measured"]
                if active_plm_sealed_entry is not None
                else None
            ),
            "active_plm_sealed_overlap_checked": False,
            "active_plm_sealed_overlap_count": None,
            "active_plm_sealed_overlap": None,
            "active_plm_sealed_overlap_check_skipped_reason": (
                "active sealed fixture remains unopened"
            ),
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
        newline="\n",
    )
    print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
