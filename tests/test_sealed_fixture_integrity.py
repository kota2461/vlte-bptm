"""Enforce that sealed / blind fixtures are actually frozen (S3).

A sealed fixture (a versioned one-time measurement set, or the blind
accumulation campaign) must never change content -- silent mutation would leak
the held-out set into tuning or invalidate a measurement. Nothing in the
pipeline previously prevented a generator or a manual edit from rewriting one;
the "seal" was only a naming convention.

This test pins the timestamp-normalized content of every sealed fixture to a
committed manifest. Any content drift fails the suite. Re-sealing (deliberately
updating a sealed set) therefore requires an explicit, reviewable manifest diff
-- it can no longer happen silently. Volatile timestamp fields are normalized
out so the guard tracks substance, not authoring time.

To re-generate the manifest after an intentional, reviewed change:
    REGEN_SEALED_MANIFEST=1 python -B -m pytest tests/test_sealed_fixture_integrity.py
"""

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Lives in tests/ (not tests/fixtures/) so fixture-scanning generators do not
# census it as a benchmark fixture.
MANIFEST_PATH = ROOT / "tests" / "sealed_integrity_manifest_v1.json"

# Recursively dropped before hashing: authoring timestamps are not content.
_VOLATILE_KEYS = {
    "generated_at",
    "frozen_at",
    "measured_at",
    "measured",
    "created_at",
    "timestamp",
}

_SEAL_MARKERS = ('"same_batch_tuning_allowed": false',)
_SEARCH_DIRS = ("tests/fixtures", "data")


def _is_sealed(path: Path) -> bool:
    if "sealed" in path.name.lower():
        return True
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return any(marker in text for marker in _SEAL_MARKERS)


def iter_sealed_files() -> list[Path]:
    found: list[Path] = []
    for rel in _SEARCH_DIRS:
        for path in sorted((ROOT / rel).glob("*.json")):
            if path == MANIFEST_PATH:
                continue  # the manifest names itself "sealed_*"; never self-include
            if _is_sealed(path):
                found.append(path)
    return found


def _strip_volatile(value):
    if isinstance(value, dict):
        return {k: _strip_volatile(v) for k, v in value.items() if k not in _VOLATILE_KEYS}
    if isinstance(value, list):
        return [_strip_volatile(v) for v in value]
    return value


def normalized_digest(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(_strip_volatile(payload), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _current_manifest() -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): normalized_digest(path)
        for path in iter_sealed_files()
    }


def _maybe_regenerate() -> None:
    if not os.environ.get("REGEN_SEALED_MANIFEST"):
        return
    manifest = {
        "schema_version": "sealed-fixture-integrity-manifest.v1",
        "note": "Timestamp-normalized content digests of sealed/blind fixtures. "
        "A change here must be a deliberate, reviewed re-seal.",
        "files": _current_manifest(),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


_maybe_regenerate()
_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["files"]


def test_manifest_covers_exactly_the_sealed_fixtures() -> None:
    discovered = {p.relative_to(ROOT).as_posix() for p in iter_sealed_files()}
    recorded = set(_MANIFEST)
    missing = discovered - recorded
    stale = recorded - discovered
    assert not missing, f"sealed fixtures not registered in manifest: {sorted(missing)}"
    assert not stale, f"manifest lists fixtures that no longer exist/qualify: {sorted(stale)}"


def test_sealed_fixtures_match_manifest_digest() -> None:
    drifted = []
    for rel, expected in sorted(_MANIFEST.items()):
        actual = normalized_digest(ROOT / rel)
        if actual != expected:
            drifted.append(rel)
    assert not drifted, (
        "sealed fixture content changed (leak/mutation?): "
        f"{drifted}. If intentional, re-seal with REGEN_SEALED_MANIFEST=1."
    )
