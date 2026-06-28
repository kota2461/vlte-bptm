"""Inspect recoverability of the live baseline pyc without mutating code."""

import dis
import json
import marshal
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "semantic_routing" / "__pycache__"
OUT_JSON = ROOT / "build" / "baseline_pyc_recovery_inspection_v1.json"
OUT_DIS = ROOT / "build" / "baseline_pyc_recovery_disassembly_v1.txt"


def _chosen_pyc() -> Path:
    candidates = sorted(
        (p for p in CACHE.glob("baseline.cpython-310.pyc.*") if p.stat().st_size > 50000),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("no baseline pyc candidates")
    return candidates[0]


def _code_objects(code: types.CodeType) -> dict[str, types.CodeType]:
    return {c.co_name: c for c in code.co_consts if isinstance(c, types.CodeType)}


def _jsonable_const(value):
    if isinstance(value, types.CodeType):
        return {"code_object": value.co_name, "firstlineno": value.co_firstlineno}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, tuple):
        return [_jsonable_const(v) for v in value]
    return repr(value)


def main() -> None:
    pyc = _chosen_pyc()
    module = marshal.loads(pyc.read_bytes()[16:])
    funcs = _code_objects(module)
    report = {
        "schema_version": "baseline-pyc-recovery-inspection.v1",
        "status": "diagnostic_completed_no_mutation",
        "chosen_pyc": str(pyc.relative_to(ROOT)).replace("\\", "/"),
        "chosen_pyc_size": pyc.stat().st_size,
        "module_firstlineno": module.co_firstlineno,
        "functions": {},
    }
    selected = [
        "_v7_generalization_profile",
        "_v8_recovery_profile",
        "_v9_primary_review_profile",
        "_v9_constraint_operation_extension_profile",
        "extract_semantic_packet",
    ]
    with OUT_DIS.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"chosen_pyc: {report['chosen_pyc']}\n\n")
        for name in selected:
            code = funcs[name]
            report["functions"][name] = {
                "firstlineno": code.co_firstlineno,
                "argcount": code.co_argcount,
                "nlocals": code.co_nlocals,
                "names": list(code.co_names),
                "varnames": list(code.co_varnames),
                "consts": [_jsonable_const(c) for c in code.co_consts],
                "instruction_count": sum(1 for _ in dis.get_instructions(code)),
            }
            fh.write("=" * 80 + "\n")
            fh.write(f"{name} firstlineno={code.co_firstlineno}\n")
            fh.write("-" * 80 + "\n")
            dis.dis(code, file=fh)
            fh.write("\n\n")
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "chosen_pyc": report["chosen_pyc"], "outputs": [str(OUT_JSON.relative_to(ROOT)), str(OUT_DIS.relative_to(ROOT))]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()