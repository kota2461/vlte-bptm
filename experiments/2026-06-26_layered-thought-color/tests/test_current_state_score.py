from layered_thought_color.current_state_score import build_current_state_score


def test_current_state_score_includes_harvest_and_holdout():
    report = build_current_state_score(refresh=False, output_path=None)

    assert report["scores"]["current_experimental_value"] >= 70
    assert report["scores"]["growth_potential"] >= 80
    assert report["scores"]["mainline_replacement"] == 60
    assert report["scores"]["corpus_readiness"] >= 95
    assert report["scores"]["group_holdout_generalization"] < 50
    assert report["components"]["harvest"]["sample_count"] == 270
    assert report["verdict"] == "dual_lane_growth_candidate"

