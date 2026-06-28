from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "build/adopt_v6_boundary_false_positive_candidates.py",
    "build/adopt_v6_boundary_priority_review_candidates.py",
    "build/adopt_v6_router_debate_candidates.py",
    "build/adopt_v6_structural_build_30_candidates.py",
    "build/measure_v6_scores.py",
    "build/run_v7_nonsealed_replay_gate.py",
    "build/create_v7_targets_and_roadmap.py",
    "build/run_v8_nonsealed_replay_gate.py",
    "build/create_v8_targets_and_roadmap.py",
    "build/adopt_v9_accumulated_primary_review_candidates.py",
    "build/create_v9_constraint_operation_extension.py",
    "build/run_v9_nonsealed_replay_gate.py",
    "build/create_v9_targets_and_roadmap.py",
    "build/adopt_v10_thought_color_bridge_candidates.py",
    "build/run_v10_mainline_replay_gate.py",
    "build/create_v10_targets_and_roadmap.py",
    "build/create_v11_code_audit_triage.py",
    "build/create_v11_targets_and_roadmap.py",
]

for script in SCRIPTS:
    print(f"== {script}")
    completed = subprocess.run(
        [sys.executable, "-B", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)