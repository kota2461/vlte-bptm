"""Ingest pasted real-log inputs into the collection staging file.

  python build/ingest_logs.py [input_txt] [provenance]

Reads one input per line from `input_txt` (default build/incoming_logs.txt),
drops anything overlapping the campaign or existing corpus, attaches a DRAFT
intent + marker flag via the router, and writes the staging file. NOTHING is
approved here — review comes next.
"""

import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.collection_store import (
    DEFAULT_STAGING, ingest, load_campaign_inputs, load_corpus_inputs,
    save_staging,
)

INPUT = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "build/incoming_logs.txt")
PROVENANCE = sys.argv[2] if len(sys.argv) > 2 else "user-real-log-2026-06-15"


def main() -> None:
    if not INPUT.exists():
        print(f"missing input file: {INPUT} (paste one input per line)")
        return
    lines = INPUT.read_text(encoding="utf-8").splitlines()
    blocked = load_campaign_inputs() | load_corpus_inputs()
    payload = ingest(lines, provenance=PROVENANCE, blocked_inputs=blocked)
    save_staging(payload, ROOT / DEFAULT_STAGING)

    c = payload["counts"]
    print(f"staged {c['staged']} | skipped: dup {c['skipped_duplicate']}, "
          f"empty {c['skipped_empty']}, campaign/corpus-overlap "
          f"{c['skipped_blocked_overlap']}")
    by_intent = Counter(e["draft_intent"] for e in payload["entries"])
    no_marker = sum(1 for e in payload["entries"] if not e["markers_fired"])
    print("draft by_intent:", dict(sorted(by_intent.items())))
    print(f"no-marker (high-value learned-layer) cases: {no_marker}/{c['staged']}")
    if payload["skipped_blocked_examples"]:
        print("blocked (overlap) examples:", payload["skipped_blocked_examples"][:5])
    print(f"\nstaging -> {DEFAULT_STAGING}")
    print("next: python build/collection_worksheet.py  (then review)")


if __name__ == "__main__":
    main()
