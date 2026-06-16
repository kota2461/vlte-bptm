"""Merge batch-02 staging into the frozen accumulation campaign (one pass).

Backs up the pre-merge campaign, appends the staged cases (stripped to the
strict 9 case fields), sets status to ready_for_review (collection target
reached), validates via the contract parser, and writes the canonical form.
Idempotent: re-running skips ids already present.
"""

import io
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.conversation_accumulation import (
    parse_conversation_accumulation,
)

CAMPAIGN = ROOT / "data" / "conversation_accumulation_v1.json"
STAGING = ROOT / "build" / "batch02_staging.json"
BACKUP = ROOT / "build" / "conversation_accumulation_v1.pre-batch02.json"
CASE_FIELDS = (
    "id", "batch", "collected_at", "category", "language",
    "input", "expected", "critical_underprocessing", "review_status",
)


def main() -> None:
    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    if not BACKUP.exists():
        shutil.copy2(CAMPAIGN, BACKUP)
        print("backup written:", BACKUP.name)
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    staged = [
        {key: case[key] for key in CASE_FIELDS}
        for case in staging["cases"]
    ]
    existing_ids = {case["id"] for case in campaign["cases"]}
    new = [case for case in staged if case["id"] not in existing_ids]
    campaign["cases"] = list(campaign["cases"]) + new
    if len(campaign["cases"]) >= campaign["target_case_count"]:
        campaign["status"] = "ready_for_review"
    parsed = parse_conversation_accumulation(campaign)  # validates
    CAMPAIGN.write_text(
        json.dumps(parsed.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("appended:", len(new))
    print("merged cases:", len(parsed.cases))
    print("status:", parsed.status)
    print(
        "category balance:",
        dict(Counter(case.category for case in parsed.cases)),
    )


if __name__ == "__main__":
    main()
