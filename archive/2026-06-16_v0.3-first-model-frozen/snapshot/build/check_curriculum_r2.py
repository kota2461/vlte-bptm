import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.intent_conversational_curriculum_r2 import (
    conversational_examples_r2,
)
from semantic_routing.semantic_packet import INTENTS
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

ex = conversational_examples_r2()
assert all(e["intent"] in INTENTS for e in ex), "bad intent"

campaign = {
    c.input_text
    for c in load_conversation_accumulation(
        ROOT / "data" / "conversation_accumulation_v1.json"
    ).cases
}
corpus = {
    e["input"]
    for e in json.loads(
        (ROOT / "data" / "intent_training_corpus_v1.json").read_text(
            encoding="utf-8"
        )
    )["examples"]
}
texts = {e["input"] for e in ex}
print("total:", len(ex))
print("by_intent:", dict(sorted(Counter(e["intent"] for e in ex).items())))
print("by_lang:", dict(sorted(Counter(e["language"] for e in ex).items())))
print("overlap vs campaign:", sorted(texts & campaign) or "none")
print("overlap vs existing corpus:", sorted(texts & corpus) or "none")
