"""Diagnose (a): which live routing literals are pure overfit vs general.

The V11 profile-literal audit counts "fixture-like" literals statically (by
word shape). This goes further: it takes every alternation branch of every
marker regex actually used by the router (semantic_routing.baseline._MARKER_DATA)
and counts how many distinct fixture inputs each branch matches. That empirical
coverage is the real overfit signal:

    matches 0 inputs  -> dead literal (safe to remove)
    matches 1 input   -> pure single-sentence overfit (the forbidden
                         "one regex per failed fixture sentence")
    matches >= 2       -> at least minimally general (review, keep candidate)

Read-only: writes one report JSON, mutates nothing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing import baseline  # noqa: E402
from semantic_routing.reproducibility import reproducible_now_iso  # noqa: E402

FIXTURE_DIR = ROOT / "tests" / "fixtures"
OUT = ROOT / "build" / "diagnose_overfit_literals_v1.json"

# Inputs are sealed in measurement, but reading them to *count regex coverage*
# is a read-only diagnostic (no labels touched, no tuning). Use the full input
# universe so coverage is not understated.


def _collect_inputs(value: object, out: list[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "input" and isinstance(v, str) and v.strip():
                out.append(v)
            else:
                _collect_inputs(v, out)
    elif isinstance(value, list):
        for v in value:
            _collect_inputs(v, out)


def _corpus() -> list[str]:
    seen: set[str] = set()
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        items: list[str] = []
        _collect_inputs(payload, items)
        seen.update(items)
    return sorted(seen)


def _split_top_level_alternation(pattern: str) -> list[str]:
    """Split a regex on '|' only at paren/bracket depth 0."""
    branches: list[str] = []
    depth = 0
    in_class = False
    cur: list[str] = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            cur.append(pattern[i : i + 2])
            i += 2
            continue
        if in_class:
            cur.append(ch)
            if ch == "]":
                in_class = False
        elif ch == "[":
            in_class = True
            cur.append(ch)
        elif ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == "|" and depth == 0:
            branches.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    branches.append("".join(cur))
    return [b for b in branches if b]


def _iter_marker_regexes(value: object):
    """Yield (signal_name, regex_pattern) from the _MARKER_DATA structure."""
    if isinstance(value, dict):
        for v in value.values():
            yield from _iter_marker_regexes(v)
    elif isinstance(value, list):
        for v in value:
            yield from _iter_marker_regexes(v)
    elif isinstance(value, tuple):
        # markers are (signal_name, pattern) tuples
        if len(value) == 2 and all(isinstance(x, str) for x in value) and "|" in value[1] + "(":
            yield value[0], value[1]
        else:
            for v in value:
                yield from _iter_marker_regexes(v)


def main() -> None:
    corpus = _corpus()
    branches: list[dict] = []
    seen_branch: set[tuple[str, str]] = set()
    for signal, pattern in _iter_marker_regexes(baseline._MARKER_DATA):
        for branch in _split_top_level_alternation(pattern):
            key = (signal, branch)
            if key in seen_branch:
                continue
            seen_branch.add(key)
            try:
                rx = re.compile(branch, re.I)
            except re.error:
                continue
            hits = [inp for inp in corpus if rx.search(inp)]
            branches.append({"signal": signal, "branch": branch, "match_count": len(hits)})

    dead = [b for b in branches if b["match_count"] == 0]
    overfit = [b for b in branches if b["match_count"] == 1]
    narrow = [b for b in branches if b["match_count"] in (2, 3)]
    general = [b for b in branches if b["match_count"] >= 4]

    report = {
        "schema_version": "diagnose-overfit-literals.v1",
        "generated_at": reproducible_now_iso(),
        "corpus_input_count": len(corpus),
        "total_branches": len(branches),
        "summary": {
            "dead_0_matches": len(dead),
            "pure_overfit_1_match": len(overfit),
            "narrow_2_3_matches": len(narrow),
            "general_4plus_matches": len(general),
        },
        "by_signal_overfit_counts": _by_signal(overfit + dead),
        "dead_literals": sorted(dead, key=lambda b: b["signal"]),
        "pure_overfit_literals": sorted(overfit, key=lambda b: b["signal"]),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print("corpus inputs:", len(corpus), "total branches:", len(branches))
    print("report ->", OUT.relative_to(ROOT).as_posix())


def _by_signal(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for it in items:
        counts[it["signal"]] = counts.get(it["signal"], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


if __name__ == "__main__":
    main()
