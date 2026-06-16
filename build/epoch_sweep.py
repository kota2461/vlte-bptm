"""Epoch sweep: can the frozen 25-case regression recover without data changes?

Round 1b state: 226 approved patterns (Round 1 52 + reinforcement 8).
Anchors = boundary v2 revision 2 (52) + round 1b (8) = 60.
"""

import io
import json
import sys

from pattern_learning.boundary_curriculum_v2 import BOUNDARY_CURRICULUM_V2
from pattern_learning.boundary_reinforcement_r1b import (
    BOUNDARY_REINFORCEMENT_R1B,
)
from pattern_learning.database import PatternDatabase
from pattern_learning.evaluation import evaluate_router
from pattern_learning.trainer import RouterModel, train_router

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    cases = json.loads(
        open(
            "tests/fixtures/pattern_router_cases_v1.json", encoding="utf-8"
        ).read()
    )
    anchors_all = list(BOUNDARY_CURRICULUM_V2) + list(
        BOUNDARY_REINFORCEMENT_R1B
    )
    for epochs in (16, 32, 40, 48, 64):
        output = f"build/sweep226_{epochs}.json"
        train_router(database, output, epochs=epochs)
        model = RouterModel.load(output)
        regression = evaluate_router(model, cases)
        anchors = sum(
            model.predict(pattern.text).route == pattern.route
            for pattern in anchors_all
        )
        misses = [miss["name"] for miss in regression["misses"]]
        raw = int(round(regression["raw_accuracy"] * 25))
        print(
            f"epochs={epochs}: regression={raw}/25 "
            f"anchors={anchors}/60 misses={misses}"
        )


if __name__ == "__main__":
    main()
