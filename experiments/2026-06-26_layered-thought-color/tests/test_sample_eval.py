from layered_thought_color.sample_eval import build_sample_eval_report


def test_sample_pool_eval_runs_all_fit_and_group_holdout():
    report = build_sample_eval_report(output_path=None)

    assert report["sample_pool"]["case_count"] == 32
    assert report["all_fit"]["full_code_accuracy"] == 1.0
    assert report["group_holdout"]["case_count"] == 32
    assert report["group_holdout"]["group_count"] == 8
    assert 0.0 <= report["group_holdout"]["base_accuracy"] <= 1.0
    assert 0.0 <= report["group_holdout"]["full_code_accuracy"] <= 1.0

