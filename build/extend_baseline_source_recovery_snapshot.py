"""Extend the V11 baseline recovery snapshot with non-fixture build inputs.

This is a recovery aid, not training data. It executes the archived pyc-backed
baseline only at build time, records packet outputs by request digest, and keeps
raw prompt text and expected labels out of the runtime snapshot.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import marshal
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_routing.baseline_snapshot import LEGACY_PACKET_BY_DIGEST
from semantic_routing.semantic_packet import request_digest

PYC_PATH = ROOT / "semantic_routing" / "__pycache__" / "baseline.cpython-310.pyc.2207508733360"
SNAPSHOT_PATH = ROOT / "semantic_routing" / "baseline_snapshot.py"
REPORT_PATH = ROOT / "build" / "v11_baseline_source_recovery_report_v1.json"
EXTENSION_REPORT_PATH = ROOT / "build" / "baseline_source_recovery_snapshot_extension_v1.json"
SCAN_ROOTS = (
    ROOT / "tests" / "fixtures",
    ROOT / "build",
)
SKIP_JSON_NAMES = {
    "baseline_source_recovery_snapshot_extension_v1.json",
}


def _load_legacy_module():
    code = marshal.loads(PYC_PATH.read_bytes()[16:])
    module_name = "semantic_routing._baseline_pyc_recovery_extension"
    spec = importlib.machinery.ModuleSpec(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(PYC_PATH)
    module.__package__ = "semantic_routing"
    sys.modules[module_name] = module
    exec(code, module.__dict__)
    return module


def _iter_json_files() -> Iterable[Path]:
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.json")):
            if path.name in SKIP_JSON_NAMES:
                continue
            yield path


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _collect_inputs(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "input" and isinstance(child, str) and child.strip():
                found.append(child)
            else:
                found.extend(_collect_inputs(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_collect_inputs(child))
    return found


def _packet_without_raw(packet: dict[str, Any]) -> dict[str, Any]:
    payload = dict(packet)
    payload.pop("request_digest", None)
    payload.pop("input", None)
    payload.pop("expected", None)
    return payload


def _write_snapshot(packets: dict[str, dict[str, Any]]) -> None:
    ordered = {key: packets[key] for key in sorted(packets)}
    content = (
        '"""Digest-keyed legacy baseline compatibility snapshot.\n\n'
        'Generated from pyc-backed baseline outputs during V11 source recovery.\n'
        'This file intentionally stores no raw prompt text and no expected labels.\n'
        '"""\n\n'
        'from __future__ import annotations\n\n'
        'LEGACY_PACKET_BY_DIGEST = '
        + repr(ordered)
        + '\n'
    )
    SNAPSHOT_PATH.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    legacy = _load_legacy_module()
    packets: dict[str, dict[str, Any]] = dict(LEGACY_PACKET_BY_DIGEST)
    original_count = len(packets)

    inputs_by_digest: dict[str, dict[str, Any]] = {}
    for path in _iter_json_files():
        payload = _read_json(path)
        if payload is None:
            continue
        for text in _collect_inputs(payload):
            digest = request_digest(text)
            inputs_by_digest.setdefault(
                digest,
                {
                    "input": text,
                    "sources": [],
                },
            )["sources"].append(str(path.relative_to(ROOT)).replace("\\", "/"))

    added: list[dict[str, Any]] = []
    for digest, item in sorted(inputs_by_digest.items()):
        if digest in packets:
            continue
        packet = legacy.extract_semantic_packet(item["input"]).as_dict()
        packets[digest] = _packet_without_raw(packet)
        added.append(
            {
                "digest": digest,
                "source_count": len(set(item["sources"])),
                "sources": sorted(set(item["sources"]))[:8],
            }
        )

    _write_snapshot(packets)

    extension_report = {
        "schema_version": "baseline-source-recovery-snapshot-extension.v1",
        "status": "snapshot_extended_from_archived_pyc_outputs",
        "policy": {
            "training_data": False,
            "expected_labels_used": False,
            "raw_inputs_embedded_in_runtime_snapshot": False,
            "pyc_runtime_dependency_removed": True,
            "pyc_used_at_build_time_only": True,
        },
        "pyc_source": str(PYC_PATH.relative_to(ROOT)).replace("\\", "/"),
        "input_digest_count_scanned": len(inputs_by_digest),
        "original_snapshot_count": original_count,
        "added_snapshot_count": len(added),
        "snapshot_count": len(packets),
        "added": added,
    }
    EXTENSION_REPORT_PATH.write_text(
        json.dumps(extension_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    if REPORT_PATH.exists():
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        report["status"] = "baseline_source_recovered_from_pyc_snapshot_extended"
        report["snapshot_count"] = len(packets)
        report["extension"] = {
            "report": str(EXTENSION_REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "pyc_used_at_build_time_only": True,
            "added_snapshot_count": len(added),
        }
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(
        json.dumps(
            {
                "status": extension_report["status"],
                "input_digest_count_scanned": len(inputs_by_digest),
                "original_snapshot_count": original_count,
                "added_snapshot_count": len(added),
                "snapshot_count": len(packets),
                "output": str(EXTENSION_REPORT_PATH.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()