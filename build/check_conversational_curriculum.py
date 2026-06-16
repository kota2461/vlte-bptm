import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from semantic_routing.intent_conversational_curriculum import (
    conversational_examples,
)
from semantic_routing.semantic_packet import INTENTS
from semantic_routing.conversation_accumulation import (
    load_conversation_accumulation,
)

ex = conversational_examples()
assert all(e["intent"] in INTENTS for e in ex), "bad intent label"
campaign = {
    c.input_text
    for c in load_conversation_accumulation(
        ROOT / "data" / "conversation_accumulation_v1.json"
    ).cases
}
overlap = sorted({e["input"] for e in ex} & campaign)
print("total:", len(ex))
print("by_intent:", dict(sorted(Counter(e["intent"] for e in ex).items())))
print("by_lang:", dict(sorted(Counter(e["language"] for e in ex).items())))
print("campaign overlap:", overlap or "none")
