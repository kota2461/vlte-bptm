"""Print a compact summary of the latest deployment gate report."""

import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

report = json.load(open("build/deployment_gate_report.json", encoding="utf-8"))
print("schema:", report["schema_version"])
print("passed:", report["passed"])
for name, check in report["checks"].items():
    line = f"  {name}: passed={check['passed']}"
    if "raw_accuracy" in check:
        line += (
            f" raw={check['raw_accuracy']:.3f}"
            f" abstained={check['abstained_to_clarify']}"
        )
    if name == "improvement_vs_deployed":
        for key, comp in check["comparisons"].items():
            if "current" in comp:
                line += f" {key}:{comp['current']:.3f}->{comp['candidate']:.3f}"
    print(line)
hashes = report["hashes"]
print("candidate sha:", hashes["candidate_sha256"][:12])
print("db sha:", (hashes["database_sha256"] or "-")[:12])
print("archived previous:", report.get("promotion", {}).get("archived_previous"))
print("sample_count:", report["candidate_sample_count"])
