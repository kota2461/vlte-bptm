"""Print the staging file as a review worksheet.

No-marker cases (the learned layer's territory) are listed FIRST since those
are where new data actually moves the model. For each entry the DRAFT intent
is a suggestion only — the reviewer confirms or corrects it.
"""

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.collection_store import DEFAULT_STAGING, load_staging


def main() -> None:
    payload = load_staging(ROOT / DEFAULT_STAGING)
    entries = payload["entries"]
    # high-value first: no-marker, then marker-fired
    entries = sorted(entries, key=lambda e: (e["markers_fired"], e["id"]))
    print(f"# review worksheet — {len(entries)} entries "
          f"(provenance: {payload['provenance']})")
    print("# DRAFT intent is a suggestion; confirm or correct each.\n")
    last_section = None
    for e in entries:
        section = "MARKER-FIRED (deterministic)" if e["markers_fired"] \
            else "NO-MARKER (learned-layer / high value)"
        if section != last_section:
            print(f"\n=== {section} ===")
            last_section = section
        print(f"  {e['id']}  [{e['draft_intent']:<9}] {e['input']}")
    print("\nApprove-as-draft or correct, then I record decisions and merge.")


if __name__ == "__main__":
    main()
