"""Shared paths for the isolated experiment."""

from __future__ import annotations

import sys
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parents[1]
DATA_DIR = EXPERIMENT_ROOT / "data"
REPORTS_DIR = EXPERIMENT_ROOT / "reports"

SOURCE_BENCHMARK = (
    REPO_ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
VISIBLE_BENCHMARK_COPY = DATA_DIR / "pattern_language_visible_v1.json"
VISIBLE_BENCHMARK_MANIFEST = (
    DATA_DIR / "pattern_language_visible_v1_manifest.json"
)
COMPARISON_REPORT = REPORTS_DIR / "thought_color_comparison_v0_1.json"


def ensure_repo_on_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)

