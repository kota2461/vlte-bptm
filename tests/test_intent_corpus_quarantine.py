import json
from pathlib import Path

from semantic_routing.intent_model import load_intent_corpus


ROOT = Path(__file__).parents[1]
CORPUS_PATH = ROOT / "data" / "intent_training_corpus_v1.json"
QUARANTINE_PATH = ROOT / "data" / "intent_training_corpus_quarantine_v1.json"


HIGH_PRIORITY_INDICES = {90, 462, 473, 528, 551, 627, 659, 687, 717}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_intent_corpus_quarantine_overlay_is_reversible_and_active() -> None:
    payload = _load(QUARANTINE_PATH)

    assert payload["schema_version"] == "intent-corpus-quarantine.v1"
    assert payload["status"] == "active"
    assert payload["purpose"].startswith("Reversible quarantine overlay")
    assert payload["source_corpus"]["path"] == "data\\intent_training_corpus_v1.json"
    assert payload["restore"]["source_corpus_mutated"] is False
    assert payload["restore"]["method"] == (
        "set status to inactive or delete this overlay file"
    )
    assert payload["selection"]["scenario"] == "high_priority_actionable"
    assert set(payload["selection"]["removed_indices"]) == HIGH_PRIORITY_INDICES
    assert len(payload["entries"]) == 9


def test_quarantined_entries_match_original_corpus_snapshot() -> None:
    corpus = _load(CORPUS_PATH)
    quarantine = _load(QUARANTINE_PATH)

    for entry in quarantine["entries"]:
        original = corpus["examples"][entry["corpus_index"] - 1]
        assert entry["input"] == original["input"]
        assert entry["intent"] == original["intent"]
        assert entry["source"] == original.get("source")
        assert entry["original_review_status"] == "approved"
        assert entry["quarantine_reason"] in {
            "exclude_or_negative",
            "exclude_or_relabel_clarify",
        }


def test_load_intent_corpus_excludes_active_quarantine_entries() -> None:
    corpus = _load(CORPUS_PATH)
    approved_without_overlay = [
        example
        for example in corpus["examples"]
        if example["review_status"] == "approved"
    ]
    loaded = load_intent_corpus(CORPUS_PATH)
    loaded_inputs = {example["input"] for example in loaded}
    quarantined_inputs = {entry["input"] for entry in _load(QUARANTINE_PATH)["entries"]}

    assert len(approved_without_overlay) == 739
    assert len(loaded) == 730
    assert loaded_inputs.isdisjoint(quarantined_inputs)