"""Create a rollback archive (workspace snapshot + SHA-256 manifest + RESTORE.md).

Mirrors the existing archive/ format (workspace-snapshot.v1). Snapshots the
whole workspace except caches/build-recovery/archive itself, records every
file's SHA-256, and captures the key state facts of this milestone.
"""

import hashlib
import io
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ARCHIVE_ID = "2026-06-16_v0.3.1-observability"
CREATED_FOR = (
    "v0.3.1 observability checkpoint: additive, NO behaviour change — route() "
    "trace (decided_by/margin/top-scores), ExecutionResult decided_by, server "
    "/route trace, build/observability_report.py weak-category miss "
    "aggregation. Frozen v0.3 decisions intact (byte-identical campaign "
    "numbers). Ready for real-data collection with full observability. "
    "Roadmap: docs/V0_4_ROADMAP_2026-06-16.md"
)

EXCLUDE_DIRS = {
    "archive", ".pytest_cache", "__pycache__", ".git", ".idea", ".vscode",
    "node_modules", "thought_state_register.egg-info",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".staging"}


def _excluded(rel: Path) -> bool:
    parts = rel.parts
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    if rel.suffix in EXCLUDE_SUFFIXES:
        return True
    # build recovery / restored working copies
    if parts and parts[0] == "build" and len(parts) > 1 and parts[1].startswith(
        "pattern_lab_recovery"
    ):
        return True
    return False


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _db_stats(db_path: Path) -> dict:
    if not db_path.exists():
        return {"present": False}
    con = sqlite3.connect(str(db_path))
    try:
        quick = con.execute("PRAGMA quick_check").fetchone()[0]
        stats: dict = {"present": True, "quick_check": quick}
        try:
            rows = con.execute(
                "SELECT review_status, COUNT(*) FROM candidates GROUP BY review_status"
            ).fetchall()
            stats["candidates"] = {r[0]: r[1] for r in rows}
        except sqlite3.Error as e:
            stats["candidates_error"] = str(e)
        return stats
    finally:
        con.close()


def main() -> None:
    archive_dir = ROOT / "archive" / ARCHIVE_ID
    snapshot = archive_dir / "snapshot"
    if archive_dir.exists():
        print(f"ABORT: {archive_dir} already exists; refusing to overwrite.")
        return
    snapshot.mkdir(parents=True)

    files: dict = {}
    total_bytes = 0
    for src in sorted(ROOT.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(ROOT)
        if _excluded(rel):
            continue
        dst = snapshot / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        sha = _sha256(dst)
        size = dst.stat().st_size
        files[str(rel).replace("\\", "/")] = {"sha256": sha, "bytes": size}
        total_bytes += size

    # state facts
    intent_model = ROOT / "build" / "intent_model_v1.json"
    intent_meta = json.loads(intent_model.read_text(encoding="utf-8"))["metadata"] \
        if intent_model.exists() else {}
    router_model = ROOT / "build" / "pattern_router_model.json"
    gate_report = ROOT / "build" / "intent_gate_report.json"
    gate_decision = (
        json.loads(gate_report.read_text(encoding="utf-8")).get("decision")
        if gate_report.exists() else None
    )

    state = {
        "tests_passed": 320,
        "database": _db_stats(ROOT / "data" / "pattern_lab.db"),
        "deployed_pattern_router_model": {
            "sha256": _sha256(router_model) if router_model.exists() else None,
        },
        "deployed_intent_model": {
            "path": "build/intent_model_v1.json",
            "sha256": _sha256(intent_model) if intent_model.exists() else None,
            "schema_version": intent_meta.get("schema_version"),
            "sample_count": intent_meta.get("sample_count"),
            "metrics": intent_meta.get("metrics"),
        },
        "intent_deployment_gate": {
            "report_schema": "intent-model-deployment-gate.v1",
            "decision": gate_decision,
            "report_sha256": _sha256(gate_report) if gate_report.exists() else None,
            "fixtures": {
                "intent_foundation_anchors_v1.json": _sha256(
                    ROOT / "tests/fixtures/intent_foundation_anchors_v1.json"),
                "intent_hybrid_regression_v1.json": _sha256(
                    ROOT / "tests/fixtures/intent_hybrid_regression_v1.json"),
            },
        },
        "milestone": (
            "v0.3 router functional end-to-end + direct LLM-free fast path "
            "for trivial smalltalk (greetings answer in ~ms with no LLM, "
            "vs 5-8s on a reasoning backend). gate-promoted gated-hybrid "
            "intent model + tier map + route_and_execute + calculator tool "
            "+ HTTP service. sealed v2 remains closed (0.90; baseline 0.82)."
        ),
    }

    manifest = {
        "schema_version": "workspace-snapshot.v1",
        "archive_id": ARCHIVE_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_for": CREATED_FOR,
        "exclusions": sorted(EXCLUDE_DIRS) + sorted(EXCLUDE_SUFFIXES)
        + ["build/pattern_lab_recovery*/"],
        "state": state,
        "snapshot": {
            "file_count": len(files),
            "total_bytes": total_bytes,
            "files": files,
        },
    }
    (archive_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    restore = f"""# 復元手順: {ARCHIVE_ID}

このアーカイブは、**v0.3 初号機(gated ハイブリッド意図モデル)を意図モデル
デプロイゲートで正式昇格した直後**のワークスペース全体スナップショットである。

## 固定状態

- v0.3 first model: gate-promoted (`build/intent_model_v1.json`)
- intent model SHA-256: `{state['deployed_intent_model']['sha256']}`
- intent model k-fold (off-campaign): `{(intent_meta.get('metrics') or {}).get('kfold_accuracy')}`
- intent gate decision: `{gate_decision}` (schema intent-model-deployment-gate.v1)
- pattern router model SHA-256: `{state['deployed_pattern_router_model']['sha256']}`
- executor reasoning-budget: direction (1) wired (`semantic_routing/executor.py`)
- LM Studio end-to-end: verified (external executor; output NOT training data)
- sealed v2: 依然 closed(accuracy gate 未達)
- test suite: 276 passed
- SQLite `PRAGMA quick_check`: `{state['database'].get('quick_check')}`

全ファイルの SHA-256 と件数は `MANIFEST.json` に記録している
(file_count={len(files)}, total_bytes={total_bytes})。

## 推奨する完全復元(別ディレクトリへ展開)

```powershell
$source = "archive\\{ARCHIVE_ID}\\snapshot"
$destination = "D:\\Thought State Register restored {ARCHIVE_ID[:10]}"
New-Item -ItemType Directory -Path $destination
Copy-Item "$source\\*" $destination -Recurse
Set-Location $destination
$env:PYTHONDONTWRITEBYTECODE = "1"
python -B -m pytest -p no:cacheprovider -q
```

## 既存ワークスペースへ戻す場合

```powershell
Copy-Item "archive\\{ARCHIVE_ID}\\snapshot\\*" "." -Recurse -Force
```

## 意図モデルだけ戻す場合

```powershell
Copy-Item `
  "archive\\{ARCHIVE_ID}\\snapshot\\build\\intent_model_v1.json" `
  "build\\intent_model_v1.json" -Force
```

## Hash 検証

```powershell
$archive = "archive\\{ARCHIVE_ID}"
$manifest = Get-Content "$archive\\MANIFEST.json" -Raw | ConvertFrom-Json
$failures = @()
foreach ($property in $manifest.snapshot.files.PSObject.Properties) {{
  $path = Join-Path "$archive\\snapshot" $property.Name
  $actual = (Get-FileHash $path -Algorithm SHA256).Hash
  if ($actual -ne $property.Value.sha256) {{ $failures += $property.Name }}
}}
if ($failures.Count) {{ $failures; throw "snapshot hash verification failed" }}
"snapshot hash verification passed"
```
"""
    (archive_dir / "RESTORE.md").write_text(restore, encoding="utf-8")

    print(f"archive created: archive/{ARCHIVE_ID}")
    print(f"  files: {len(files)}  bytes: {total_bytes}")
    print(f"  intent model SHA: {state['deployed_intent_model']['sha256']}")
    print(f"  gate decision: {gate_decision}")
    print(f"  db quick_check: {state['database'].get('quick_check')}")


if __name__ == "__main__":
    main()
