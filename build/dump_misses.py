import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
report = json.load(
    open(Path(__file__).resolve().parents[1] / "build"
         / "adapter_performance_v1_report.json", encoding="utf-8")
)
for m in report["misses"]:
    e, a = m["expected"], m["actual"]
    print(f"[{m['category']:22s}] "
          f"exp {e['intent']}/{e['processing_class']}/{e['core_mode']:10s} "
          f"act {a['intent']}/{a['processing_class']}/{a['core_mode']:10s} "
          f":: {m['input'][:46]}")
