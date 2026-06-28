from layered_thought_color.adoption_score import build_adoption_score


def test_adoption_score_is_reproducible_and_conservative():
    report = build_adoption_score(refresh=False, output_path=None)

    assert report["scores"]["adoption_value"] == 67
    assert report["scores"]["mainline_replacement"] == 60
    assert report["scores"]["research_lane"] == 70
    assert report["verdict"] == "experimental_auxiliary_candidate"
    assert report["components"]["safety_score"] == 1.0
    assert "Do not replace the main adapter." in report["recommendation"]

