"""Create a reversible quarantine overlay for high-priority corpus suspects.

The source corpus is not modified. The active overlay is read by
semantic_routing.intent_model.load_intent_corpus and excludes only the listed
corpus indices from training. To restore, change status to "inactive" or remove
this overlay file.
"""

import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CORPUS_PATH = ROOT / "data" / "intent_training_corpus_v1.json"
IMPACT_PATH = ROOT / "build" / "intent_data_cleaning_impact_v1.json"
OUT_PATH = ROOT / "data" / "intent_training_corpus_quarantine_v1.json"
SCENARIO_NAME = "high_priority_actionable"
SCHEMA_VERSION = "intent-corpus-quarantine.v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scenario(payload: Dict[str, Any]) -> Dict[str, Any]:
    for item in payload["scenario_ablations"]:
        if item["name"] == SCENARIO_NAME:
            return item
    raise ValueError(f"scenario not found: {SCENARIO_NAME}")


def _individual_by_index(payload: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    result: Dict[int, Dict[str, Any]] = {}
    for item in payload["individual_high_priority"]:
        result[int(item["row"]["corpus_index"])] = item
    return result


def _entries(
    *,
    corpus_payload: Dict[str, Any],
    impact_payload: Dict[str, Any],
    indices: List[int],
) -> List[Dict[str, Any]]:
    individual = _individual_by_index(impact_payload)
    entries = []
    for index in indices:
        example = corpus_payload["examples"][index - 1]
        evidence = individual.get(index)
        if evidence is None:
            raise ValueError(f"missing individual evidence for corpus_index {index}")
        row = evidence["row"]
        if row["input"] != example["input"]:
            raise ValueError(f"impact row does not match corpus_index {index}")
        entries.append(
            {
                "corpus_index": index,
                "input_sha256": _text_sha256(example["input"]),
                "input": example["input"],
                "intent": example["intent"],
                "source": example.get("source"),
                "language": example.get("language"),
                "original_review_status": example["review_status"],
                "quarantine_reason": row["recommendation"],
                "flags": row["flags"],
                "evidence_label": evidence["evidence_label"],
                "delta_vs_baseline": evidence["delta_vs_baseline"],
            }
        )
    return entries


def main() -> None:
    if OUT_PATH.exists():
        raise FileExistsError(
            f"{OUT_PATH.relative_to(ROOT)} already exists; mark it inactive or "
            "remove it before creating a new quarantine overlay"
        )

    corpus_payload = _load_json(CORPUS_PATH)
    impact_payload = _load_json(IMPACT_PATH)
    scenario = _scenario(impact_payload)
    indices = list(scenario["removed_indices"])
    entries = _entries(
        corpus_payload=corpus_payload,
        impact_payload=impact_payload,
        indices=indices,
    )
    by_intent: Dict[str, int] = {}
    for entry in entries:
        by_intent[entry["intent"]] = by_intent.get(entry["intent"], 0) + 1

    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Reversible quarantine overlay for high-priority intent corpus "
            "suspects. The source corpus is not mutated."
        ),
        "source_corpus": {
            "path": str(CORPUS_PATH.relative_to(ROOT)),
            "sha256_at_creation": _sha256(CORPUS_PATH),
            "schema_version": corpus_payload["schema_version"],
            "example_count": len(corpus_payload["examples"]),
        },
        "selection": {
            "source_report": str(IMPACT_PATH.relative_to(ROOT)),
            "scenario": SCENARIO_NAME,
            "entry_count": len(entries),
            "removed_indices": indices,
            "removed_by_intent": scenario["removed_by_intent"],
            "delta_vs_baseline": scenario["delta_vs_baseline"],
            "evidence_label": scenario["evidence_label"],
        },
        "restore": {
            "method": "set status to inactive or delete this overlay file",
            "source_corpus_mutated": False,
            "original_review_status_field": "original_review_status",
            "expected_restored_approved_count": len(
                [
                    example
                    for example in corpus_payload["examples"]
                    if example["review_status"] == "approved"
                ]
            ),
            "active_approved_count_after_quarantine": len(
                [
                    example
                    for index, example in enumerate(
                        corpus_payload["examples"], start=1
                    )
                    if example["review_status"] == "approved" and index not in indices
                ]
            ),
        },
        "summary": {
            "entry_count": len(entries),
            "by_intent": dict(sorted(by_intent.items())),
        },
        "entries": entries,
    }
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "entry_count": payload["summary"]["entry_count"],
                "by_intent": payload["summary"]["by_intent"],
                "active_approved_count_after_quarantine": payload["restore"][
                    "active_approved_count_after_quarantine"
                ],
                "restore": payload["restore"]["method"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()