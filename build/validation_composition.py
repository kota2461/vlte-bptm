"""Diagnose the validation-accuracy drop: split composition analysis.

The improvement check compared validation_accuracy measured on DIFFERENT
holdout sets (236-corpus split vs 254-corpus split). This script shows how
many of the newly added round-2 examples landed in the candidate's
validation split.
"""

import io
import sys
from collections import Counter

from pattern_learning.database import PatternDatabase
from pattern_learning.trainer import _split_examples

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

NEW_SOURCES = (
    "curriculum://route-boundaries-round2-user",
    "curriculum://english-nonrespond-round2b",
)


def main() -> None:
    examples = PatternDatabase("data/pattern_lab.db").training_examples()
    train, validation = _split_examples(examples)
    print(f"corpus: {len(examples)}  train: {len(train)}  "
          f"validation: {len(validation)}")
    by_source = Counter(
        "round2-new"
        if example["source"]["url"] in NEW_SOURCES
        else "existing"
        for example in validation
    )
    print("validation composition:", dict(by_source))
    new_in_validation = [
        example
        for example in validation
        if example["source"]["url"] in NEW_SOURCES
    ]
    for example in new_in_validation:
        print(f"  new-in-validation [{example['route']}] "
              f"{example['input_text']}")


if __name__ == "__main__":
    main()
