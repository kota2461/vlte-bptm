"""Run Pattern Lab from this workspace's source tree."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pattern_learning.server import run_server


if __name__ == "__main__":
    run_server(
        ROOT / "data" / "pattern_lab.db",
        ROOT / "build" / "pattern_router_model.json",
    )
