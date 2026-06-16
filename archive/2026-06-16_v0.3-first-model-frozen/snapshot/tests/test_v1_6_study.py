import json
import subprocess
import sys
from pathlib import Path

import pytest

from thought_core.accuracy_audit import (
    RESPONSE_ACCURACY_AUDIT_SCHEMA_VERSION,
    build_response_accuracy_audit,
    wilson_interval,
)
from thought_core.independent_study import (
    DEFAULT_INDEPENDENT_STUDY_POLICY_PATH,
    DEFAULT_RUNTIME_SELECTION_POLICY_PATH,
    INDEPENDENT_STUDY_POLICY_SCHEMA_VERSION,
    INDEPENDENT_STUDY_REPORT_SCHEMA_VERSION,
    evaluate_independent_study,
    load_independent_study_policy,
    load_runtime_selection_policy,
)


ROOT = Path(__file__).parents[1]
POLICY_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "v1_6_independent_study_policy.json"
)
STUDY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_6_independent_study.json"
)
ROUTER_FIXTURE = (
    Path(__file__).parent / "fixtures" / "pattern_router_cases_v1.json"
)
CORE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_0a_cases.json"
)


def _study_payload() -> dict:
    return json.loads(STUDY_FIXTURE.read_text(encoding="utf-8"))


def test_independent_study_policy_matches_v1_6_fixture() -> None:
    fixture = json.loads(POLICY_FIXTURE.read_text(encoding="utf-8"))
    policy = load_independent_study_policy()

    assert DEFAULT_INDEPENDENT_STUDY_POLICY_PATH.is_file()
    assert fixture["schema_version"] == (
        INDEPENDENT_STUDY_POLICY_SCHEMA_VERSION
    )
    assert policy.as_dict() == fixture


def test_runtime_selection_policy_remains_unapproved_draft() -> None:
    policy = load_runtime_selection_policy()

    assert DEFAULT_RUNTIME_SELECTION_POLICY_PATH.is_file()
    assert policy["status"] == "draft"
    assert policy["class_modes"] == {}
    assert policy["approved_by"] is None
    assert policy["approved_at_utc"] is None
    assert policy["automatic_activation"] is False


def test_runtime_selection_policy_rejects_automatic_activation(
    tmp_path,
) -> None:
    payload = json.loads(
        DEFAULT_RUNTIME_SELECTION_POLICY_PATH.read_text(encoding="utf-8")
    )
    payload["automatic_activation"] = True
    path = tmp_path / "unsafe-selection-policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="cannot activate automatically"):
        load_runtime_selection_policy(path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update(schema_version="unknown"),
            "unsupported",
        ),
        (
            lambda payload: payload.update(minimum_reviewers_per_case=1),
            "at least 2",
        ),
        (
            lambda payload: payload.update(confidence_level=1.0),
            "confidence_level",
        ),
        (
            lambda payload: payload.update(bootstrap_iterations=10),
            "bootstrap_iterations",
        ),
        (
            lambda payload: payload.update(store_raw_output=True),
            "store_raw_output",
        ),
        (
            lambda payload: payload.update(unknown_field=True),
            "fields do not match",
        ),
    ],
)
def test_independent_study_policy_rejects_unsafe_config(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(
        DEFAULT_INDEPENDENT_STUDY_POLICY_PATH.read_text(encoding="utf-8")
    )
    mutate(payload)
    path = tmp_path / "bad-study-policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_independent_study_policy(path)


def test_independent_study_contract_fixture_is_not_policy_evidence() -> None:
    report = evaluate_independent_study(_study_payload())

    assert report["schema_version"] == (
        INDEPENDENT_STUDY_REPORT_SCHEMA_VERSION
    )
    assert report["evidence_eligible_for_policy"] is False
    assert report["case_count"] == 4
    assert report["input_class_count"] == 4
    assert report["privacy"]["raw_input_stored"] is False
    assert report["privacy"]["raw_output_stored"] is False
    assert report["privacy"]["automatic_learning"] is False
    assert report["selection_policy"]["status"] == "draft"
    assert report["selection_policy"]["automatic_activation"] is False
    assert all(
        item["status"] == "contract_fixture_only"
        and item["active_mode"] == "horizontal"
        for item in report["selection_policy"]["class_policies"].values()
    )


def test_independent_study_reports_agreement_and_uncertainty() -> None:
    report = evaluate_independent_study(_study_payload())

    assert report["agreement"][
        "pairwise_quadratic_weighted_kappa_mean"
    ] == pytest.approx(0.708609)
    assert report["agreement"][
        "preference_pairwise_agreement"
    ] == pytest.approx(0.833333)
    runtime_agreement = report["agreement"][
        "runtime_majority_preference_agreement"
    ]
    assert runtime_agreement["rate"] == pytest.approx(0.75)
    assert runtime_agreement["interval"]["lower"] < 0.75
    assert runtime_agreement["interval"]["upper"] > 0.75
    vertical_gain = report["quality_comparisons"][
        "vertical_minus_horizontal"
    ]["quality_gain"]
    hybrid_gain = report["quality_comparisons"][
        "hybrid_minus_horizontal"
    ]["quality_gain"]
    assert vertical_gain["lower"] < 0 < vertical_gain["upper"]
    assert hybrid_gain["lower"] < 0 < hybrid_gain["upper"]


def test_independent_study_finds_class_specific_pareto_frontiers() -> None:
    report = evaluate_independent_study(_study_payload())
    frontiers = report["input_class_pareto_frontiers"]

    assert frontiers["direct_response"]["frontier_modes"] == [
        "horizontal"
    ]
    assert frontiers["verification"]["frontier_modes"] == [
        "horizontal",
        "vertical",
    ]
    assert frontiers["verification"]["dominated_modes"]["hybrid"] == [
        "vertical"
    ]


def test_independent_origin_still_requires_enough_cases() -> None:
    payload = _study_payload()
    payload["evidence_origin"] = "independent_blind_collection"
    for reviewer in payload["reviewers"]:
        reviewer["independent_from_generation"] = True

    report = evaluate_independent_study(payload)

    assert report["evidence_eligible_for_policy"] is True
    assert all(
        item["status"] == "insufficient_cases"
        for item in report["selection_policy"]["class_policies"].values()
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update(raw_output="forbidden"),
            "study fields",
        ),
        (
            lambda payload: payload["privacy"].update(
                raw_output_stored=True
            ),
            "privacy policy",
        ),
        (
            lambda payload: payload["reviewers"][0].update(consented=False),
            "provide consent",
        ),
        (
            lambda payload: payload["cases"][0]["candidates"][0].update(
                response_text="forbidden"
            ),
            "candidate fields",
        ),
        (
            lambda payload: payload["cases"][0]["reviews"][0].update(
                mode="horizontal"
            ),
            "review fields",
        ),
    ],
)
def test_independent_study_rejects_privacy_or_blinding_violation(
    mutate,
    message,
) -> None:
    payload = _study_payload()
    mutate(payload)

    with pytest.raises(ValueError, match=message):
        evaluate_independent_study(payload)


def test_independent_study_cli() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core.independent_study",
            "--input-file",
            str(STUDY_FIXTURE),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    report = json.loads(completed.stdout)

    assert report["case_count"] == 4
    assert report["evidence_eligible_for_policy"] is False


def test_wilson_interval_exposes_small_sample_uncertainty() -> None:
    interval = wilson_interval(8, 8)

    assert interval["lower"] == pytest.approx(0.675592)
    assert interval["upper"] == pytest.approx(1.0)


def test_current_response_accuracy_audit_separates_regression_and_cross_set() -> None:
    report = build_response_accuracy_audit(
        router_fixture_path=ROUTER_FIXTURE,
        core_fixture_path=CORE_FIXTURE,
        model_path=ROOT / "build" / "pattern_router_model.json",
        database_path=ROOT / "data" / "pattern_lab.db",
    )

    assert report["schema_version"] == (
        RESPONSE_ACCURACY_AUDIT_SCHEMA_VERSION
    )
    assert report["core_router"]["acceptance_regression"]["accuracy"] == 1.0
    assert report["core_router"]["cross_boundary_fixture"][
        "accuracy"
    ] == pytest.approx(0.36)
    assert report["pattern_router"]["boundary_regression_raw"][
        "accuracy"
    ] == 1.0
    # v1.6監査時の基準値0.625をフロアとする。デプロイモデルの正当な再学習で
    # 改善した場合は通し、基準値を割る劣化だけを検出する。
    assert report["pattern_router"]["cross_core_fixture_raw"][
        "accuracy"
    ] >= 0.625
    assert report["pattern_router"]["boundary_training_overlap"][
        "exact_match_count"
    ] == 11
    assert report["semantic_response_quality"]["status"] == (
        "not_established"
    )
    assert report["conclusion"][
        "production_response_accuracy_established"
    ] is False


def test_response_accuracy_audit_cli() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "thought_core.accuracy_audit"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    report = json.loads(completed.stdout)

    assert report["core_router"]["cross_boundary_fixture"][
        "correct_count"
    ] == 9
    deployed_metadata = json.loads(
        (ROOT / "build" / "pattern_router_model.json").read_text(
            encoding="utf-8"
        )
    )["metadata"]
    # 固定値ではなくデプロイ済みモデルのholdout件数と一致することを検証する。
    # データ件数が増える正当な再学習のたびに壊れない。
    assert report["pattern_router"]["measurement_holdout"][
        "case_count"
    ] == deployed_metadata["validation_count"]
