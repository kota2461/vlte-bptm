import json

from layered_thought_color.compare import build_report
from layered_thought_color.data import copy_visible_benchmark
from layered_thought_color.paths import SOURCE_BENCHMARK


def test_copy_visible_benchmark_excludes_sealed(tmp_path):
    output = tmp_path / "visible.json"
    manifest_path = tmp_path / "manifest.json"

    manifest = copy_visible_benchmark(
        source_path=SOURCE_BENCHMARK,
        output_path=output,
        manifest_path=manifest_path,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert manifest["case_count"] == 56
    assert manifest["sealed_cases_copied"] is False
    assert manifest["sealed_labels_used_for_tuning"] is False
    assert {case["split"] for case in payload["cases"]} == {
        "train",
        "validation",
    }


def test_comparison_report_measures_main_and_thought_color():
    report = build_report(data_source="copy", output_path=None)
    validation = report["measurements"]["validation"]

    assert report["data"]["sealed_cases_used_for_training"] is False
    assert report["data"]["sealed_cases_used_for_evaluation"] is False
    assert validation["main_adapter"]["valid_packet_rate"] == 1.0
    assert validation["thought_color"]["valid_packet_rate"] == 1.0
    assert "intent_accuracy" in validation["thought_color_minus_main"]
    assert validation["thought_color_channels"]["case_count"] == 28

