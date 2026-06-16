"""Evaluate a model on the active sealed boundary slice.

Usage: python build/sealed_eval.py <label> [model_path] [sealed_path]
Default model is the deployed one. Writes build/sealed_vN_<label>.json and
prints a summary. Verifies the sealed fixture's SHA against the gate
registry before measuring. If sealed_path is omitted, the one active sealed
fixture in the registry is selected; consumed fixtures are not reused.
"""

import io
import json
import sys
from collections import defaultdict

from pattern_learning.deployment import file_sha256, load_registry
from pattern_learning.trainer import RouterModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FIXTURE_DIR = "tests/fixtures"


def active_sealed_fixture(registry: dict) -> str:
    active = [
        name
        for name, entry in registry["fixtures"].items()
        if "sealed" in entry.get("role", "").lower()
        and entry.get("status", "active") == "active"
    ]
    if len(active) != 1:
        raise SystemExit(
            f"expected exactly one active sealed fixture, found {active}"
        )
    return f"{FIXTURE_DIR}/{active[0]}"


def main(
    label: str,
    model_path: str = "build/pattern_router_model.json",
    sealed_path: str | None = None,
) -> None:
    registry = load_registry()
    sealed_path = sealed_path or active_sealed_fixture(registry)
    sealed_name = sealed_path.replace("\\", "/").rsplit("/", 1)[-1]
    entry = registry["fixtures"].get(sealed_name)
    if entry is None or "sealed" not in entry.get("role", "").lower():
        raise SystemExit("sealed fixture is not registered")
    if entry.get("status", "active") != "active":
        raise SystemExit("sealed fixture is consumed; use the active successor")
    actual = file_sha256(sealed_path)
    if actual != entry["sha256"]:
        raise SystemExit("sealed fixture SHA mismatch; integrity violation")

    payload = json.loads(open(sealed_path, encoding="utf-8").read())
    model = RouterModel.load(model_path)
    cases = []
    by_slice: dict = defaultdict(lambda: [0, 0])
    by_language: dict = defaultdict(lambda: [0, 0])
    pair_results: dict = defaultdict(list)
    for case in payload["cases"]:
        predicted = model.predict(case["input"]).route
        ok = predicted == case["route"]
        cases.append({**case, "predicted": predicted, "correct": ok})
        by_slice[case["slice"]][0] += ok
        by_slice[case["slice"]][1] += 1
        by_language[case["language"]][0] += ok
        by_language[case["language"]][1] += 1
        pair_results[case["group"]].append(ok)
    total_ok = sum(case["correct"] for case in cases)
    result = {
        "schema_version": "sealed-slice-eval.v1",
        "label": label,
        "sealed_fixture": sealed_name,
        "sealed_fixture_version": entry["version"],
        "sealed_sha256": actual,
        "model_path": model_path,
        "model_sha256": file_sha256(model_path),
        "total": {"correct": total_ok, "count": len(cases)},
        "by_slice": {
            key: {"correct": values[0], "count": values[1]}
            for key, values in sorted(by_slice.items())
        },
        "by_language": {
            key: {"correct": values[0], "count": values[1]}
            for key, values in sorted(by_language.items())
        },
        "pairs_both_correct": sum(
            all(flags) for flags in pair_results.values()
        ),
        "pair_count": len(pair_results),
        "cases": cases,
    }
    sealed_version = entry["version"].split(".", 1)[0]
    output = f"build/sealed_{sealed_version}_{label}.json"
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=1)
    print(f"[{label}] total {total_ok}/{len(cases)}")
    for key, values in sorted(by_slice.items()):
        print(f"  {key}: {values[0]}/{values[1]}")
    for key, values in sorted(by_language.items()):
        print(f"  lang {key}: {values[0]}/{values[1]}")
    print(
        f"  pairs both correct: {result['pairs_both_correct']}"
        f"/{result['pair_count']}"
    )
    misses = [case for case in cases if not case["correct"]]
    for miss in misses:
        print(f"  MISS [{miss['route']}->{miss['predicted']}] {miss['input']}")


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else "adhoc",
        sys.argv[2]
        if len(sys.argv) > 2
        else "build/pattern_router_model.json",
        sys.argv[3] if len(sys.argv) > 3 else None,
    )
