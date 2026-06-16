"""Record PLM benchmark review and sealed rotation state."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = (
    ROOT / "tests" / "fixtures" / "pattern_language_benchmark_v1.json"
)
SEALED_V2 = (
    ROOT / "tests" / "fixtures" / "pattern_language_sealed_v2.json"
)
ADJUDICATION = ROOT / "build" / "plm_benchmark_v1_adjudication.json"
OUTPUT = (
    ROOT / "tests" / "fixtures" / "pattern_language_fixture_registry.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    adjudication = json.loads(ADJUDICATION.read_text(encoding="utf-8"))
    payload = {
        "schema_version": "pattern-language-fixture-registry.v1",
        "updated_at": "2026-06-13T05:45:00+00:00",
        "rules": [
            "human-reviewed train and validation labels are append-only",
            "a sealed fixture is measured at most once before rotation",
            "opening sealed cases for review consumes the fixture",
            "sealed labels are never used for tuning before rotation",
        ],
        "fixtures": {
            "pattern_language_benchmark_v1.json": {
                "sha256": _sha256(BENCHMARK),
                "case_count": 84,
                "review_status": "human_reviewed",
                "train_count": 28,
                "validation_count": 28,
                "sealed_count": 28,
                "sealed_status": "consumed",
                "sealed_consumed_at": adjudication[
                    "review_completed_at"
                ],
                "sealed_consumed_for": "human label review",
                "successor": "pattern_language_sealed_v2.json",
                "changed_label_count": adjudication["changed_count"],
            },
            "pattern_language_sealed_v2.json": {
                "sha256": _sha256(SEALED_V2),
                "case_count": 28,
                "status": "active",
                "role": "sealed measurement only",
                "predecessor": (
                    "pattern_language_benchmark_v1.json#sealed"
                ),
                "measured": False,
                "reviewed": False,
            },
        },
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
