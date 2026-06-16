"""Greeting response test: router route + approved exemplar responses."""

import io
import sys

from pattern_learning.database import PatternDatabase
from pattern_learning.trainer import RouterModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

GREETINGS = (
    "こんにちは",
    "おはようございます",
    "Hello!",
    "Good morning!",
    "Thank you so much!",
    "はじめまして、よろしくお願いします",
)


def main() -> None:
    database = PatternDatabase("data/pattern_lab.db")
    model = RouterModel.load("build/pattern_router_model.json")
    exemplars = {
        pattern["input_text"]: pattern["thought_form"].get("candidates", [])
        for pattern in database.training_examples()
    }
    for text in GREETINGS:
        prediction = model.predict(text)
        answers = exemplars.get(text) or ["-"]
        print(f"{text}  ->  route={prediction.route}  応答例: {answers[0]}")


if __name__ == "__main__":
    main()
