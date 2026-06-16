"""Generate the foundation anchor suite fixture (v0.2.1 design).

Selection rule (deterministic, documented in the fixture):
- every rating-5 pattern from the tier-0 curricula (math-v1, language-v1)
- cases the CURRENT deployed model misroutes are excluded (ratchet) and
  listed in metadata.excluded so they stay visible as known gaps.
"""

import io
import json
import sys
from datetime import datetime, timezone

from pattern_learning.language_curriculum import LANGUAGE_CURRICULUM
from pattern_learning.math_curriculum import MATH_CURRICULUM
from pattern_learning.trainer import RouterModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUTPUT = "tests/fixtures/foundation_anchor_suite_v1.json"


def main() -> None:
    model = RouterModel.load("build/pattern_router_model.json")
    candidates = [
        ("math-v1", pattern)
        for pattern in MATH_CURRICULUM
        if pattern.rating == 5
    ] + [
        ("language-v1", pattern)
        for pattern in LANGUAGE_CURRICULUM
        if pattern.rating == 5
    ]
    cases = []
    excluded = []
    for source, pattern in candidates:
        predicted = model.predict(pattern.text).route
        entry = {
            "source": source,
            "input": pattern.text,
            "route": pattern.route,
        }
        if predicted == pattern.route:
            cases.append(entry)
        else:
            excluded.append({**entry, "predicted_at_freeze": predicted})

    fixture = {
        "schema_version": "foundation-anchor-suite.v1",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "selection_rule": (
            "rating-5 patterns from tier-0 curricula (math-v1, language-v1); "
            "cases the deployed model misrouted at freeze time are excluded "
            "(ratchet) and listed under metadata.excluded"
        ),
        "training_overlap": (
            "all cases are approved training patterns; this suite is a "
            "self-consistency contract, not a generalization estimate"
        ),
        "deployed_model_at_freeze": model.metadata.get("trained_at"),
        "excluded": excluded,
        "cases": cases,
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(fixture, handle, ensure_ascii=False, indent=1)
    print(f"cases: {len(cases)}  excluded: {len(excluded)}")
    for item in excluded:
        print("EXCLUDED:", json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
