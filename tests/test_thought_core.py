import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import pytest

from thought_core.bits import THOUGHT_CODE_WIDTH, ThoughtCode
from thought_core.action_vector import (
    ACTION_AXES,
    ACTION_VECTOR_SCHEMA_VERSION,
    ActionVector,
)
from thought_core.channel_schema import (
    CHANNEL_SCHEMA_CONFIG_VERSION,
    CHANNEL_SEMANTICS,
    DEFAULT_CHANNEL_SCHEMA_PATH,
    load_channel_schemas,
)
from thought_core.demo import process
from thought_core.encoder import THRESHOLD_PROFILES, encode
from thought_core.integrator import (
    DEFAULT_INHIBITION_POLICY,
    DEFAULT_INHIBITION_MATRIX,
    integrate,
    load_inhibition_matrix,
    load_inhibition_policy,
)
from thought_core.hybrid import (
    DEFAULT_HYBRID_STACK_MESH_PATH,
    HYBRID_EVALUATION_SCHEMA_VERSION,
    HYBRID_STACK_MESH_SCHEMA_VERSION,
    build_hybrid_stack_mesh,
    evaluate_hybrid_candidate_coverage,
    load_hybrid_config,
)
from thought_core.mesh import (
    DEFAULT_HORIZONTAL_MESH_PATH,
    HORIZONTAL_MESH_SCHEMA_VERSION,
    build_horizontal_mesh,
    decide_axis_votes,
    load_horizontal_mesh_config,
)
from thought_core.order_builder import LLM_ORDER_SCHEMA_VERSION, _select_mode
from thought_core.observation import (
    OBSERVATION_SCHEMA_VERSION,
    THRESHOLD_COMPARISON_SCHEMA_VERSION,
    compare_threshold_profiles,
    observe_inputs,
)
from thought_core.observation_store import (
    DEFAULT_PRIVACY_POLICY_PATH,
    DEFAULT_OBSERVATION_PRIVACY_POLICY,
    OBSERVATION_STORE_EXPORT_SCHEMA_VERSION,
    OBSERVATION_STORE_SCHEMA_VERSION,
    PRIVACY_POLICY_SCHEMA_VERSION,
    ObservationStore,
    load_observation_privacy_policy,
    prepare_persistent_observation,
)
from thought_core.unit_catalog import (
    DEFAULT_UNIT_CATALOG_PATH,
    UNIT_CATALOG_SCHEMA_VERSION,
    load_unit_catalog,
)
from thought_core.state import UnitActivation
from thought_core.selector import (
    DEFAULT_UNIT_SELECTION_POLICY,
    load_unit_selection_policy,
    select_units,
)
from thought_core.units import (
    DEFAULT_CHANNEL_SCHEMAS,
    DEFAULT_UNIT_DEFINITIONS,
    PATTERN_CHANNELS,
    PATTERN_HEIGHT,
    PATTERN_SHAPE,
    PATTERN_WIDTH,
    DEFAULT_UNITS,
)
from thought_core.vertical_stack import (
    DEFAULT_VERTICAL_STACK_PATH,
    VERTICAL_OUTPUT_SCHEMA_VERSION,
    VERTICAL_PROGRESS_SCHEMA_VERSION,
    VERTICAL_STACK_SCHEMA_VERSION,
    build_vertical_stack,
    evaluate_vertical_outputs,
    load_vertical_stack_config,
)

CHANNEL_SCHEMA_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_1_channel_schemas.json"
)
OUTPUT_SCHEMA_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_1_output_schemas.json"
)
UNIT_CATALOG_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_1_pattern_units.json"
)
OBSERVATION_SCHEMA_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_2_observation_schema.json"
)
THRESHOLD_SCHEMA_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_2_threshold_profile_schema.json"
)
HORIZONTAL_MESH_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_2_horizontal_mesh.json"
)
HYBRID_STACK_MESH_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_4_hybrid_stack_mesh.json"
)
HYBRID_EVALUATION_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_4_hybrid_evaluation.json"
)
OBSERVATION_PRIVACY_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "v1_2_observation_privacy_policy.json"
)
VERTICAL_STACK_FIXTURE = (
    Path(__file__).parent / "fixtures" / "v1_3_vertical_stack.json"
)


def test_thought_code_is_deterministic_unsigned_64_bit_routing_key() -> None:
    first = ThoughtCode.from_text("same input")
    second = ThoughtCode.from_text("same input")

    assert first == second
    assert 0 <= first.value < (1 << THOUGHT_CODE_WIDTH)
    assert first.as_dict()["role"] == "external_routing_key"


def test_pattern_unit_shape_is_separate_from_thought_code_width() -> None:
    unit = DEFAULT_UNITS[0]

    assert THOUGHT_CODE_WIDTH == 64
    assert unit.shape == PATTERN_SHAPE
    assert unit.shape == (PATTERN_CHANNELS, PATTERN_HEIGHT, PATTERN_WIDTH)
    assert unit.pattern.summary()["spatial_semantics"] is False
    assert unit.channel_schema
    assert unit.channel_schema_version == CHANNEL_SCHEMA_CONFIG_VERSION
    assert unit.channel_semantics == CHANNEL_SEMANTICS
    assert unit.process_mode == "horizontal"


def test_channel_schema_registry_matches_frozen_v1_1_fixture() -> None:
    fixture = json.loads(CHANNEL_SCHEMA_FIXTURE.read_text(encoding="utf-8"))

    assert fixture["schema_version"] == CHANNEL_SCHEMA_CONFIG_VERSION
    assert fixture["channel_count"] == PATTERN_CHANNELS
    assert fixture["channel_semantics"] == CHANNEL_SEMANTICS
    assert set(DEFAULT_CHANNEL_SCHEMAS) == set(fixture["units"])
    for unit in DEFAULT_UNITS:
        expected = fixture["units"][unit.unit_id]
        schema = DEFAULT_CHANNEL_SCHEMAS[unit.unit_id]
        assert schema.schema_id == expected["schema_id"]
        assert list(schema.prototype_channels) == expected["prototype_channels"]
        assert unit.channel_schema == schema.schema_id
        assert unit.preferred_channels == schema.prototype_channels
        assert schema.spatial_semantics is False
        assert schema.unassigned_channel_role == "no_named_semantics"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update(
                {"schema_version": "pattern-channel-schemas.v999"}
            ),
            "unsupported",
        ),
        (
            lambda payload: payload.update({"spatial_semantics": True}),
            "spatial_semantics",
        ),
        (
            lambda payload: payload["units"]["verify"].update(
                {"prototype_channels": [True, 2]}
            ),
            "integer",
        ),
        (
            lambda payload: payload["units"]["verify"].update(
                {"prototype_channels": [0, 64]}
            ),
            "range",
        ),
    ],
)
def test_channel_schema_config_rejects_invalid_contract(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(DEFAULT_CHANNEL_SCHEMA_PATH.read_text(encoding="utf-8"))
    mutate(payload)
    bad = tmp_path / "bad-channel-schema.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_channel_schemas(bad)


def test_action_vector_and_llm_order_schemas_match_v1_1_fixture() -> None:
    fixture = json.loads(OUTPUT_SCHEMA_FIXTURE.read_text(encoding="utf-8"))
    action_contract = fixture["action_vector"]
    order_contract = fixture["llm_order"]

    assert action_contract["schema_version"] == ACTION_VECTOR_SCHEMA_VERSION
    assert action_contract["axes"] == list(ACTION_AXES)
    assert order_contract["schema_version"] == LLM_ORDER_SCHEMA_VERSION

    payload = process("この設計をレビューしてください").as_dict()
    assert (
        payload["action_vector_schema_version"]
        == ACTION_VECTOR_SCHEMA_VERSION
    )
    assert list(payload["action_vector"]) == action_contract["axes"]
    assert all(
        action_contract["value_range"][0]
        <= value
        <= action_contract["value_range"][1]
        for value in payload["action_vector"].values()
    )
    assert set(payload["llm_order"]) == set(order_contract["required_fields"])
    assert payload["llm_order"]["schema_version"] == LLM_ORDER_SCHEMA_VERSION
    assert (
        payload["llm_order"]["action_vector_schema_version"]
        == ACTION_VECTOR_SCHEMA_VERSION
    )
    assert payload["llm_order"]["mode"] in order_contract["modes"]


def test_pattern_unit_catalog_matches_frozen_v1_1_fixture() -> None:
    fixture = json.loads(UNIT_CATALOG_FIXTURE.read_text(encoding="utf-8"))

    assert fixture["schema_version"] == UNIT_CATALOG_SCHEMA_VERSION
    assert [unit.unit_id for unit in DEFAULT_UNITS] == [
        unit["unit_id"] for unit in fixture["units"]
    ]
    assert len(DEFAULT_UNIT_DEFINITIONS) == len(fixture["units"])
    for definition, unit, expected in zip(
        DEFAULT_UNIT_DEFINITIONS,
        DEFAULT_UNITS,
        fixture["units"],
    ):
        assert definition.unit_id == expected["unit_id"]
        assert definition.unit_type == expected["unit_type"]
        assert definition.label == expected["label"]
        assert list(definition.keywords) == expected["keywords"]
        assert dict(definition.action_weights) == expected["action_weights"]
        assert definition.channel_schema == expected["channel_schema"]
        assert definition.process_mode == expected["process_mode"]
        assert unit.catalog_schema_version == UNIT_CATALOG_SCHEMA_VERSION


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update({"process_mode": "vertical"}),
            "horizontal",
        ),
        (
            lambda payload: payload["units"].append(payload["units"][0]),
            "duplicate",
        ),
        (
            lambda payload: payload["units"][0].update(
                {"unit_type": "different"}
            ),
            "equal",
        ),
        (
            lambda payload: payload["units"][0]["action_weights"].update(
                {"reply": True}
            ),
            "weights",
        ),
    ],
)
def test_pattern_unit_catalog_rejects_invalid_contract(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(DEFAULT_UNIT_CATALOG_PATH.read_text(encoding="utf-8"))
    mutate(payload)
    bad = tmp_path / "bad-unit-catalog.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_unit_catalog(bad)


def test_observation_report_aggregates_without_retaining_inputs() -> None:
    inputs = [
        "この設計をレビューしてください",
        "情報が不足しているので質問してください",
    ]
    report = observe_inputs(inputs)
    fixture = json.loads(
        OBSERVATION_SCHEMA_FIXTURE.read_text(encoding="utf-8")
    )

    assert report["schema_version"] == OBSERVATION_SCHEMA_VERSION
    assert report["pipeline_version"] == "1.6"
    assert report["sample_count"] == 2
    assert report["privacy"] == fixture["privacy"]
    assert set(report["aggregates"]) == set(fixture["required_aggregates"])
    assert len(report["aggregates"]["active_bit_frequency"]) == 64
    assert set(report["aggregates"]["selected_unit_frequency"]) == {
        unit.unit_id for unit in DEFAULT_UNITS
    }
    assert sum(
        item["count"]
        for item in report["aggregates"][
            "threshold_profile_frequency"
        ].values()
    ) == 2
    serialized = json.dumps(report, ensure_ascii=False)
    assert all(text not in serialized for text in inputs)
    assert "user_input" not in serialized


def test_observation_report_is_deterministic() -> None:
    inputs = ["こんにちは", "実装してください", "短く要約してください"]
    assert observe_inputs(inputs) == observe_inputs(inputs)


def test_observation_cli_reads_acceptance_fixture() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core.observation",
            "--input-file",
            str(Path(__file__).parent / "fixtures" / "v1_0a_cases.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    report = json.loads(completed.stdout)

    assert report["schema_version"] == OBSERVATION_SCHEMA_VERSION
    assert report["sample_count"] == 8
    assert report["privacy"]["raw_input_stored"] is False


def test_threshold_profile_comparison_is_review_only() -> None:
    cases = json.loads(
        (
            Path(__file__).parent / "fixtures" / "v1_0a_cases.json"
        ).read_text(encoding="utf-8")
    )
    fixture = json.loads(
        THRESHOLD_SCHEMA_FIXTURE.read_text(encoding="utf-8")
    )
    report = compare_threshold_profiles(cases)

    assert report["schema_version"] == THRESHOLD_COMPARISON_SCHEMA_VERSION
    assert list(report["profiles"]) == fixture["profiles"]
    assert report["sample_count"] == len(cases)
    assert report["decision"]["automatic_adjustment"] is False
    assert report["profiles"]["auto"]["expected_mode_accuracy"] == 1.0
    for metrics in report["profiles"].values():
        assert set(metrics) == set(fixture["required_metrics"])
        assert metrics["active_bit_count"]["minimum"] >= 4
        assert metrics["active_bit_count"]["maximum"] <= 36
    serialized = json.dumps(report, ensure_ascii=False)
    assert all(
        case["input"] not in serialized
        for case in cases
        if case["input"]
    )


def test_threshold_profile_comparison_cli() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core.observation",
            "--compare-profiles",
            "--input-file",
            str(Path(__file__).parent / "fixtures" / "v1_0a_cases.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    report = json.loads(completed.stdout)

    assert report["schema_version"] == THRESHOLD_COMPARISON_SCHEMA_VERSION
    assert report["decision"]["automatic_adjustment"] is False


def test_observation_privacy_policy_matches_v1_2_fixture() -> None:
    fixture = json.loads(
        OBSERVATION_PRIVACY_FIXTURE.read_text(encoding="utf-8")
    )
    policy = load_observation_privacy_policy()

    assert fixture["schema_version"] == PRIVACY_POLICY_SCHEMA_VERSION
    assert (
        fixture["storage_schema_version"]
        == OBSERVATION_STORE_SCHEMA_VERSION
        == policy.storage_schema_version
    )
    assert policy.minimum_cohort_size == fixture["minimum_cohort_size"]
    assert policy.minimum_cell_count == fixture["minimum_cell_count"]
    assert policy.bucket_hours == fixture["bucket_hours"]
    assert policy.retention_days == fixture["retention_days"]
    assert policy.immutable_buckets is fixture["immutable_buckets"]
    assert list(policy.persisted_aggregates) == fixture[
        "persisted_aggregates"
    ]
    assert list(policy.excluded_aggregates) == fixture[
        "excluded_aggregates"
    ]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update({"opt_in_only": False}),
            "opt_in_only",
        ),
        (
            lambda payload: payload.update({"minimum_cell_count": 9}),
            "cannot exceed",
        ),
        (
            lambda payload: payload["persisted_aggregates"].append(
                "selected_unit_combination_frequency"
            ),
            "disjoint",
        ),
    ],
)
def test_observation_privacy_policy_rejects_unsafe_config(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(
        DEFAULT_PRIVACY_POLICY_PATH.read_text(encoding="utf-8")
    )
    mutate(payload)
    bad = tmp_path / "bad-observation-privacy.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_observation_privacy_policy(bad)


def test_persistent_observation_rejects_small_cohort() -> None:
    report = observe_inputs(["one", "two"])

    with pytest.raises(ValueError, match="at least 8"):
        prepare_persistent_observation(report)


def test_persistent_observation_suppresses_sensitive_detail() -> None:
    cases = json.loads(
        (
            Path(__file__).parent / "fixtures" / "v1_0a_cases.json"
        ).read_text(encoding="utf-8")
    )
    report = observe_inputs(case["input"] for case in cases)
    record = prepare_persistent_observation(
        report,
        observed_at=datetime(2026, 6, 11, 12, tzinfo=timezone.utc),
    )

    assert record["schema_version"] == OBSERVATION_STORE_SCHEMA_VERSION
    assert record["bucket_start_utc"] == "2026-06-11T00:00:00Z"
    assert record["bucket_end_utc"] == "2026-06-12T00:00:00Z"
    assert record["cohort_size_band"] == "8-15"
    assert "sample_count" not in record
    assert "selected_unit_combination_frequency" not in record["aggregates"]
    serialized = json.dumps(record, ensure_ascii=False)
    assert '"rate"' not in serialized
    assert all(
        case["input"] not in serialized
        for case in cases
        if case["input"]
    )
    for aggregate in record["aggregates"].values():
        assert all(
            cell["count"]
            >= DEFAULT_OBSERVATION_PRIVACY_POLICY.minimum_cell_count
            for cell in aggregate.values()
        )


def test_persistent_observation_rejects_forbidden_nested_field() -> None:
    report = observe_inputs(["sample"] * 8)
    report["aggregates"]["active_bit_frequency"]["input"] = {
        "count": 8,
        "rate": 1.0,
    }

    with pytest.raises(ValueError, match="forbidden"):
        prepare_persistent_observation(report)


def test_persistent_observation_rejects_unknown_category() -> None:
    report = observe_inputs(["sample"] * 8)
    report["aggregates"]["selected_unit_frequency"]["private label"] = {
        "count": 8,
        "rate": 1.0,
    }

    with pytest.raises(ValueError, match="unsupported cells"):
        prepare_persistent_observation(report)


def test_observation_store_is_local_immutable_and_input_free(
    tmp_path,
) -> None:
    inputs = [f"private sample {index}" for index in range(8)]
    report = observe_inputs(inputs)
    store = ObservationStore(tmp_path / "observations.db")
    observed_at = datetime(2026, 6, 11, 12, tzinfo=timezone.utc)

    stored = store.persist(report, observed_at=observed_at)
    exported = store.export()

    assert stored["cohort_size_band"] == "8-15"
    assert exported["schema_version"] == OBSERVATION_STORE_EXPORT_SCHEMA_VERSION
    assert exported["bucket_count"] == 1
    assert exported["buckets"][0]["bucket_start_utc"] == (
        "2026-06-11T00:00:00Z"
    )
    with pytest.raises(ValueError, match="immutable"):
        store.persist(report, observed_at=observed_at)
    database_bytes = store.path.read_bytes()
    assert all(text.encode("utf-8") not in database_bytes for text in inputs)


def test_observation_store_automatically_purges_expired_buckets(
    tmp_path,
) -> None:
    report = observe_inputs(["retention sample"] * 8)
    store = ObservationStore(tmp_path / "retention.db")
    store.persist(
        report,
        observed_at=datetime(2026, 4, 1, 12, tzinfo=timezone.utc),
    )
    store.persist(
        report,
        observed_at=datetime(2026, 6, 11, 12, tzinfo=timezone.utc),
    )

    exported = store.export()
    assert exported["bucket_count"] == 1
    assert exported["buckets"][0]["bucket_start_utc"] == (
        "2026-06-11T00:00:00Z"
    )


def test_observation_store_management_does_not_create_missing_database(
    tmp_path,
) -> None:
    store = ObservationStore(tmp_path / "missing.db")

    with pytest.raises(ValueError, match="does not exist"):
        store.export()
    assert store.purge() == 0
    assert not store.path.exists()


def test_observation_cli_explicitly_persists_and_lists_store(
    tmp_path,
) -> None:
    database = tmp_path / "cli-observations.db"
    fixture = Path(__file__).parent / "fixtures" / "v1_0a_cases.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core.observation",
            "--input-file",
            str(fixture),
            "--store",
            str(database),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    stored = json.loads(completed.stdout)

    assert stored["schema_version"] == OBSERVATION_STORE_SCHEMA_VERSION
    assert stored["cohort_size_band"] == "8-15"
    assert "sample_count" not in stored
    assert "selected_unit_combination_frequency" not in stored["aggregates"]
    assert "stored privacy-minimized observation bucket" in completed.stderr
    listed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core.observation",
            "--list-store",
            str(database),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    exported = json.loads(listed.stdout)
    assert exported["bucket_count"] == 1
    assert "selected_unit_combination_frequency" not in (
        exported["buckets"][0]["aggregates"]
    )


def test_horizontal_mesh_config_matches_v1_2_fixture() -> None:
    fixture = json.loads(HORIZONTAL_MESH_FIXTURE.read_text(encoding="utf-8"))
    config = load_horizontal_mesh_config()

    assert fixture["schema_version"] == HORIZONTAL_MESH_SCHEMA_VERSION
    assert list(config.control_axis_priority) == fixture[
        "control_axis_priority"
    ]
    assert list(config.fallback_axis_priority) == fixture[
        "fallback_axis_priority"
    ]
    assert dict(config.axis_to_mode) == fixture["axis_to_mode"]
    assert config.decision_method == fixture["decision_method"]
    assert config.normalization == fixture["normalization"]


@pytest.mark.parametrize(
    ("votes", "axis", "mode", "loser_axis", "loser_reason"),
    [
        (
            {"ask": 0.1, "reply": 0.9},
            "ask",
            "clarify",
            "reply",
            "suppressed_by_positive_control_vote",
        ),
        (
            {"reply": 0.5, "explain": 0.5},
            "reply",
            "respond",
            "explain",
            "tie_broken_by_priority",
        ),
        (
            {"verify": 0.4, "plan": 0.4},
            "verify",
            "verify",
            "plan",
            "tie_broken_by_priority",
        ),
        (
            {"creative": 0.3, "caution": 0.3},
            "creative",
            "explore",
            "caution",
            "tie_broken_by_priority",
        ),
    ],
)
def test_horizontal_mesh_priority_contract(
    votes,
    axis,
    mode,
    loser_axis,
    loser_reason,
) -> None:
    complete_votes = {name: 0.0 for name in ACTION_AXES}
    complete_votes.update(votes)

    winner_axis, winner_mode, candidates = decide_axis_votes(complete_votes)
    by_axis = {candidate["axis"]: candidate for candidate in candidates}

    assert (winner_axis, winner_mode) == (axis, mode)
    assert by_axis[axis]["selected"] is True
    assert by_axis[loser_axis]["reason"] == loser_reason


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update(
                {"schema_version": "horizontal-unit-mesh.v999"}
            ),
            "unsupported",
        ),
        (
            lambda payload: payload["control_axis_priority"].append("reply"),
            "unique",
        ),
        (
            lambda payload: payload["axis_to_mode"].pop("ask"),
            "cover",
        ),
        (
            lambda payload: payload.update({"normalization": "none"}),
            "normalization",
        ),
    ],
)
def test_horizontal_mesh_config_rejects_invalid_contract(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(
        DEFAULT_HORIZONTAL_MESH_PATH.read_text(encoding="utf-8")
    )
    mutate(payload)
    bad = tmp_path / "bad-horizontal-mesh.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_horizontal_mesh_config(bad)


def test_pipeline_horizontal_mesh_matches_action_vector_and_order() -> None:
    payload = process("この設計をレビューしてください").as_dict()
    mesh = payload["horizontal_mesh"]
    selected = [
        candidate for candidate in mesh["candidates"]
        if candidate["selected"]
    ]

    assert mesh["schema_version"] == HORIZONTAL_MESH_SCHEMA_VERSION
    assert mesh["votes"] == payload["action_vector"]
    assert mesh["winning_mode"] == payload["llm_order"]["mode"]
    assert len(selected) == 1
    assert selected[0]["axis"] == mesh["winning_axis"]
    assert (
        payload["llm_order"]["metadata"][
            "horizontal_mesh_schema_version"
        ]
        == HORIZONTAL_MESH_SCHEMA_VERSION
    )
    assert set(mesh["unit_contributions"]) == {
        unit["unit_id"] for unit in payload["selected_units"]
    }


def test_horizontal_mesh_preserves_legacy_mode_selection_for_axis_grid() -> None:
    for values in product((0.0, 0.25, 0.5), repeat=len(ACTION_AXES)):
        votes = dict(zip(ACTION_AXES, values))
        _axis, mesh_mode, _candidates = decide_axis_votes(votes)
        assert mesh_mode == _select_mode(ActionVector(votes))


def test_vertical_stack_config_matches_v1_3_fixture() -> None:
    fixture = json.loads(VERTICAL_STACK_FIXTURE.read_text(encoding="utf-8"))
    config = load_vertical_stack_config()

    assert fixture["schema_version"] == VERTICAL_STACK_SCHEMA_VERSION
    assert fixture["output_schema_version"] == VERTICAL_OUTPUT_SCHEMA_VERSION
    assert config.max_depth == fixture["max_depth"]
    assert dict(config.root_unit_by_mode) == fixture["root_unit_by_mode"]
    assert {
        unit_id: list(dependencies)
        for unit_id, dependencies in config.input_dependencies.items()
    } == fixture["input_dependencies"]
    assert config.verifier_unit_id == fixture[
        "verification_policy"
    ]["verifier_unit_id"]
    assert list(config.verification_targets) == fixture[
        "verification_policy"
    ]["required_before"]
    assert config.blocking_signal_unit_id == fixture[
        "blocking_policy"
    ]["signal_unit_id"]
    assert list(config.blocking_targets) == fixture[
        "blocking_policy"
    ]["blocks_targets"]
    assert config.blocking_minimum_relative_score == fixture[
        "blocking_policy"
    ]["minimum_relative_score"]
    assert list(config.stop_reasons) == fixture["stop_reasons"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update(
                {"schema_version": "vertical-unit-stack.v999"}
            ),
            "unsupported",
        ),
        (
            lambda payload: payload.update({"max_depth": 1}),
            "exceeds",
        ),
        (
            lambda payload: payload["input_dependencies"].update(
                {"verify": ["build"]}
            ),
            "cycle",
        ),
        (
            lambda payload: payload["output_contracts"].pop("verify"),
            "cover",
        ),
        (
            lambda payload: payload["output_contracts"]["verify"][
                "required_fields"
            ].update({"status": "boolean"}),
            "override",
        ),
    ],
)
def test_vertical_stack_config_rejects_invalid_contract(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(
        DEFAULT_VERTICAL_STACK_PATH.read_text(encoding="utf-8")
    )
    mutate(payload)
    bad = tmp_path / "bad-vertical-stack.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_vertical_stack_config(bad)


def test_vertical_build_stack_inserts_verify_before_target() -> None:
    plan = build_vertical_stack("build")
    payload = plan.as_dict()

    assert payload["schema_version"] == VERTICAL_STACK_SCHEMA_VERSION
    assert payload["output_schema_version"] == VERTICAL_OUTPUT_SCHEMA_VERSION
    assert payload["status"] == "ready"
    assert payload["execution_order"] == ["verify", "build"]
    assert payload["initial_unit_id"] == "verify"
    assert payload["steps"][0]["role"] == "verification_gate"
    assert payload["steps"][1]["input_dependencies"] == ["verify"]
    assert set(
        payload["steps"][0]["output_contract"]["required_fields"]
    ) >= {
        "schema_version",
        "unit_id",
        "status",
        "assumptions",
        "evidence",
        "verified",
        "verified_assumptions",
        "risk_flags",
    }


def test_vertical_stack_blocks_unresolved_clarification_signal() -> None:
    activations = [
        UnitActivation(
            "build",
            "Implementation",
            0.7,
            0.7,
            PATTERN_SHAPE,
        ),
        UnitActivation(
            "clarify",
            "Clarification",
            0.65,
            0.65,
            PATTERN_SHAPE,
        ),
    ]
    plan = build_vertical_stack("build", activations)

    assert plan.status == "blocked"
    assert plan.final_mode == "clarify"
    assert plan.initial_unit_id is None
    assert plan.stop_reason == "unresolved_clarification"
    progress = evaluate_vertical_outputs(plan, {})
    assert progress.status == "blocked"
    assert progress.stop_reason == "unresolved_clarification"


def _vertical_output(unit_id: str, **fields) -> dict:
    config = load_vertical_stack_config()
    output = {
        "schema_version": config.output_contracts[unit_id].schema_version,
        "unit_id": unit_id,
        "status": "completed",
        "assumptions": [],
        "evidence": [],
    }
    output.update(fields)
    return output


def test_vertical_stack_progresses_only_after_contract_validation() -> None:
    plan = build_vertical_stack("build")
    waiting = evaluate_vertical_outputs(plan, {})

    assert waiting.as_dict()["schema_version"] == (
        VERTICAL_PROGRESS_SCHEMA_VERSION
    )
    assert waiting.status == "waiting"
    assert waiting.next_unit_id == "verify"

    verify_output = _vertical_output(
        "verify",
        verified=True,
        verified_assumptions=["repository-is-available-private-marker"],
        risk_flags=[],
    )
    ready_for_build = evaluate_vertical_outputs(
        plan,
        {"verify": verify_output},
    )
    assert ready_for_build.status == "waiting"
    assert ready_for_build.completed_unit_ids == ("verify",)
    assert ready_for_build.next_unit_id == "build"

    complete = evaluate_vertical_outputs(
        plan,
        {
            "verify": verify_output,
                "build": _vertical_output(
                    "build",
                    assumptions=[
                        "repository-is-available-private-marker"
                    ],
                    implementation_plan={"steps": ["inspect", "edit", "test"]},
                ),
        },
    )
    assert complete.status == "completed"
    assert complete.completed_unit_ids == ("verify", "build")


def test_vertical_stack_stops_on_failed_verification() -> None:
    plan = build_vertical_stack("build")
    progress = evaluate_vertical_outputs(
        plan,
        {
            "verify": _vertical_output(
                "verify",
                verified=False,
                verified_assumptions=[],
                risk_flags=["missing evidence"],
            )
        },
    )

    assert progress.status == "blocked"
    assert progress.stop_reason == "verification_failed"
    assert progress.failed_unit_id == "verify"


def test_vertical_stack_stops_unverified_assumption_propagation() -> None:
    plan = build_vertical_stack("build")
    progress = evaluate_vertical_outputs(
        plan,
        {
            "verify": _vertical_output(
                "verify",
                verified=True,
                verified_assumptions=[],
                risk_flags=[],
            ),
            "build": _vertical_output(
                "build",
                assumptions=["untested premise"],
                implementation_plan={"steps": []},
            ),
        },
    )

    assert progress.status == "blocked"
    assert progress.stop_reason == "unverified_assumption"
    assert progress.failed_unit_id == "build"


def test_vertical_stack_rejects_invalid_output_contract() -> None:
    plan = build_vertical_stack("build")
    progress = evaluate_vertical_outputs(
        plan,
        {
            "verify": {
                "schema_version": "wrong",
                "unit_id": "verify",
            }
        },
    )

    assert progress.status == "blocked"
    assert progress.stop_reason == "invalid_output_contract"
    assert progress.failed_unit_id == "verify"
    with pytest.raises(ValueError, match="must be an object"):
        evaluate_vertical_outputs(plan, [])
    extra = _vertical_output(
        "verify",
        verified=True,
        verified_assumptions=[],
        risk_flags=[],
    )
    extra["hidden_premise"] = "not allowed"
    assert evaluate_vertical_outputs(
        plan,
        {"verify": extra},
    ).stop_reason == "invalid_output_contract"
    invalid_array = _vertical_output(
        "verify",
        verified=True,
        verified_assumptions=[{"not": "a string"}],
        risk_flags=[],
    )
    assert evaluate_vertical_outputs(
        plan,
        {"verify": invalid_array},
    ).stop_reason == "invalid_output_contract"


def test_vertical_pipeline_dispatches_one_validated_step_at_a_time() -> None:
    text = "この機能を実装してください"
    initial = process(text, processing_mode="vertical").as_dict()

    assert initial["pipeline_version"] == "1.6"
    assert initial["diagnostics"]["processing_mode"] == "vertical"
    assert initial["vertical_stack"]["execution_order"] == [
        "verify",
        "build",
    ]
    assert initial["vertical_stack"]["progress"]["status"] == "waiting"
    assert initial["vertical_stack"]["progress"]["next_unit_id"] == "verify"
    assert initial["llm_order"]["mode"] == "verify"
    assert "Execute only the next unit, verify" in (
        initial["llm_order"]["instruction"]
    )
    assert [stage["stage"] for stage in initial["trace"]] == [
        "input",
        "active_bits",
        "selected_units",
        "inhibition_integration",
        "horizontal_mesh",
        "vertical_stack",
        "action_vector",
        "llm_order",
    ]

    verify_output = _vertical_output(
        "verify",
        verified=True,
        verified_assumptions=["repository-is-available-private-marker"],
        risk_flags=[],
    )
    build_ready = process(
        text,
        processing_mode="vertical",
        vertical_outputs={"verify": verify_output},
    ).as_dict()

    assert build_ready["vertical_stack"]["progress"][
        "completed_unit_ids"
    ] == ["verify"]
    assert build_ready["vertical_stack"]["progress"]["next_unit_id"] == (
        "build"
    )
    assert build_ready["llm_order"]["mode"] == "build"
    assert "Execute only the next unit, build" in (
        build_ready["llm_order"]["instruction"]
    )
    assert "repository-is-available-private-marker" not in json.dumps(
        build_ready
    )

    completed = process(
        text,
        processing_mode="vertical",
        vertical_outputs={
            "verify": verify_output,
            "build": _vertical_output(
                "build",
                assumptions=["repository-is-available-private-marker"],
                implementation_plan={"steps": ["inspect", "edit", "test"]},
            ),
        },
    ).as_dict()
    assert completed["vertical_stack"]["progress"]["status"] == "completed"
    assert completed["vertical_stack"]["progress"]["next_unit_id"] is None
    assert completed["llm_order"]["mode"] == "build"
    assert "No further unit dispatch is required" in (
        completed["llm_order"]["instruction"]
    )


def test_horizontal_pipeline_remains_backward_compatible() -> None:
    payload = process("この機能を実装してください").as_dict()

    assert "vertical_stack" not in payload
    assert "hybrid_stack_mesh" not in payload
    assert payload["diagnostics"]["processing_mode"] == "horizontal"
    assert "vertical_stack" not in [
        stage["stage"] for stage in payload["trace"]
    ]
    with pytest.raises(ValueError, match="vertical_outputs require"):
        process(
            "test",
            vertical_outputs={
                "verify": _vertical_output(
                    "verify",
                    verified=True,
                    verified_assumptions=[],
                    risk_flags=[],
                )
            },
        )
    with pytest.raises(ValueError, match="processing_mode"):
        process("test", processing_mode="recursive")


def test_vertical_cli_accepts_previous_unit_outputs(tmp_path) -> None:
    outputs = tmp_path / "vertical-outputs.json"
    outputs.write_text(
        json.dumps(
            {
                "verify": _vertical_output(
                    "verify",
                    verified=True,
                    verified_assumptions=[],
                    risk_flags=[],
                )
            }
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core",
            "--json",
            "--processing-mode",
            "vertical",
            "--vertical-outputs-file",
            str(outputs),
            "この機能を実装してください",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(completed.stdout)

    assert payload["vertical_stack"]["progress"]["next_unit_id"] == "build"
    assert payload["llm_order"]["mode"] == "build"


def _activation(unit_id: str, score: float) -> UnitActivation:
    unit = next(unit for unit in DEFAULT_UNITS if unit.unit_id == unit_id)
    return UnitActivation(
        unit_id=unit.unit_id,
        label=unit.label,
        raw_score=score,
        integrated_score=score,
        pattern_shape=unit.shape,
        unit_type=unit.unit_type,
        channel_schema=unit.channel_schema,
        channel_schema_version=unit.channel_schema_version,
        channel_semantics=unit.channel_semantics,
        prototype_channels=unit.preferred_channels,
        catalog_schema_version=unit.catalog_schema_version,
        process_mode=unit.process_mode,
    )


def test_hybrid_config_matches_v1_4_fixture() -> None:
    fixture = json.loads(
        HYBRID_STACK_MESH_FIXTURE.read_text(encoding="utf-8")
    )
    config = load_hybrid_config()

    assert fixture["schema_version"] == HYBRID_STACK_MESH_SCHEMA_VERSION
    assert config.candidate_score_method == fixture[
        "candidate_score_method"
    ]
    assert list(config.candidate_unit_priority) == fixture[
        "candidate_unit_priority"
    ]
    assert list(config.control_candidate_units) == fixture[
        "control_candidate_units"
    ]
    assert list(config.fallback_candidate_units) == fixture[
        "fallback_candidate_units"
    ]
    assert config.relative_score_threshold == fixture[
        "relative_score_threshold"
    ]
    assert config.minimum_score == fixture["minimum_score"]
    assert config.budget.max_stacks == fixture["budgets"]["max_stacks"]
    assert config.budget.max_total_steps == fixture["budgets"][
        "max_total_steps"
    ]
    assert config.budget.max_stack_depth == fixture["budgets"][
        "max_stack_depth"
    ]
    assert config.budget.max_dispatches_per_call == fixture["budgets"][
        "max_dispatches_per_call"
    ]
    assert config.scheduler == fixture["scheduler"]
    assert config.integrator == fixture["integrator"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update(
                {"schema_version": "hybrid-stack-mesh.v999"}
            ),
            "unsupported",
        ),
        (
            lambda payload: payload["control_candidate_units"].append(
                "respond"
            ),
            "disjoint",
        ),
        (
            lambda payload: payload["budgets"].update(
                {"max_dispatches_per_call": 2}
            ),
            "exactly one",
        ),
        (
            lambda payload: payload["budgets"].update(
                {"max_stack_depth": 5}
            ),
            "exceeds",
        ),
    ],
)
def test_hybrid_config_rejects_invalid_contract(
    tmp_path,
    mutate,
    message,
) -> None:
    payload = json.loads(
        DEFAULT_HYBRID_STACK_MESH_PATH.read_text(encoding="utf-8")
    )
    mutate(payload)
    bad = tmp_path / "bad-hybrid.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_hybrid_config(bad)


def test_hybrid_selects_multiple_control_stacks_within_budget() -> None:
    activations = [
        _activation("build", 0.9),
        _activation("summarize", 0.82),
        _activation("respond", 0.5),
    ]
    mesh = build_horizontal_mesh(activations)
    decision = build_hybrid_stack_mesh(activations, mesh)
    payload = decision.as_dict()

    assert payload["schema_version"] == HYBRID_STACK_MESH_SCHEMA_VERSION
    assert payload["status"] == "waiting"
    assert payload["budgets"]["used_stacks"] == 2
    assert payload["budgets"]["used_steps"] == 3
    assert [stack["stack_id"] for stack in payload["stacks"]] == [
        "build",
        "summarize",
    ]
    assert payload["next_dispatch"] == {
        "stack_id": "build",
        "unit_id": "verify",
    }
    by_unit = {
        candidate["unit_id"]: candidate
        for candidate in payload["considered_candidates"]
    }
    assert by_unit["respond"]["selected"] is False
    assert by_unit["respond"]["reason"] == (
        "fallback_suppressed_by_control_candidates"
    )


def test_hybrid_does_not_duplicate_dependency_as_root_stack() -> None:
    activations = [
        _activation("verify", 0.92),
        _activation("build", 0.88),
        _activation("respond", 0.3),
    ]
    mesh = build_horizontal_mesh(activations)
    payload = build_hybrid_stack_mesh(activations, mesh).as_dict()
    by_unit = {
        candidate["unit_id"]: candidate
        for candidate in payload["considered_candidates"]
    }

    assert [stack["stack_id"] for stack in payload["stacks"]] == ["build"]
    assert by_unit["verify"]["selected"] is False
    assert by_unit["verify"]["reason"] == (
        "covered_by_selected_dependency"
    )


def test_hybrid_budget_prefers_stack_covering_dependency_branch() -> None:
    activations = [
        _activation("summarize", 1.0),
        _activation("explore", 0.95),
        _activation("verify", 0.9),
        _activation("build", 0.8),
    ]
    mesh = build_horizontal_mesh(activations)
    payload = build_hybrid_stack_mesh(activations, mesh).as_dict()

    assert [stack["stack_id"] for stack in payload["stacks"]] == [
        "build",
        "summarize",
    ]
    by_unit = {
        candidate["unit_id"]: candidate
        for candidate in payload["considered_candidates"]
    }
    assert by_unit["build"]["selection_score"] == pytest.approx(1.7)
    assert by_unit["build"]["covered_unit_ids"] == ["verify", "build"]
    assert by_unit["verify"]["reason"] == (
        "covered_by_selected_dependency"
    )
    assert by_unit["explore"]["reason"] == "stack_budget_exceeded"


def test_hybrid_namespaces_outputs_and_schedules_one_dispatch() -> None:
    activations = [
        _activation("build", 0.9),
        _activation("summarize", 0.82),
    ]
    mesh = build_horizontal_mesh(activations)
    verify = _vertical_output(
        "verify",
        verified=True,
        verified_assumptions=["repo"],
        risk_flags=[],
    )
    build = _vertical_output(
        "build",
        assumptions=["repo"],
        implementation_plan={"private": "build-output-marker-914"},
    )
    summarize = _vertical_output(
        "summarize",
        summary="summary-output-marker-914",
    )

    initial = build_hybrid_stack_mesh(activations, mesh)
    after_verify = build_hybrid_stack_mesh(
        activations,
        mesh,
        outputs={"build": {"verify": verify}},
    )
    after_build = build_hybrid_stack_mesh(
        activations,
        mesh,
        outputs={"build": {"verify": verify, "build": build}},
    )
    completed = build_hybrid_stack_mesh(
        activations,
        mesh,
        outputs={
            "build": {"verify": verify, "build": build},
            "summarize": {"summarize": summarize},
        },
    )

    assert initial.next_dispatch == {
        "stack_id": "build",
        "unit_id": "verify",
    }
    assert after_verify.next_dispatch == {
        "stack_id": "build",
        "unit_id": "build",
    }
    assert after_build.next_dispatch == {
        "stack_id": "summarize",
        "unit_id": "summarize",
    }
    assert completed.status == "completed"
    assert completed.winning_stack_id == "build"
    assert completed.final_mode == "build"
    serialized = json.dumps(completed.as_dict())
    assert "build-output-marker-914" not in serialized
    assert "summary-output-marker-914" not in serialized


def test_hybrid_uses_completed_alternative_after_primary_failure() -> None:
    activations = [
        _activation("build", 0.9),
        _activation("summarize", 0.82),
    ]
    mesh = build_horizontal_mesh(activations)
    failed_verify = _vertical_output(
        "verify",
        verified=False,
        verified_assumptions=[],
        risk_flags=["missing evidence"],
    )
    summarize = _vertical_output("summarize", summary="safe alternative")

    waiting = build_hybrid_stack_mesh(
        activations,
        mesh,
        outputs={"build": {"verify": failed_verify}},
    )
    completed = build_hybrid_stack_mesh(
        activations,
        mesh,
        outputs={
            "build": {"verify": failed_verify},
            "summarize": {"summarize": summarize},
        },
    )

    assert waiting.status == "waiting"
    assert waiting.next_dispatch == {
        "stack_id": "summarize",
        "unit_id": "summarize",
    }
    assert completed.status == "completed"
    assert completed.winning_stack_id == "summarize"
    assert completed.final_mode == "summarize"


def test_hybrid_falls_back_safely_when_every_stack_is_blocked() -> None:
    activations = [_activation("build", 0.9)]
    mesh = build_horizontal_mesh(activations)
    failed = build_hybrid_stack_mesh(
        activations,
        mesh,
        outputs={
            "build": {
                "verify": _vertical_output(
                    "verify",
                    verified=False,
                    verified_assumptions=[],
                    risk_flags=["missing evidence"],
                )
            }
        },
    )

    assert failed.status == "fallback"
    assert failed.winning_stack_id is None
    assert failed.stop_reason == "verification_failed"
    assert failed.final_mode == "verify"
    assert failed.next_dispatch is None


def test_hybrid_uses_horizontal_mode_when_no_candidate_meets_minimum() -> None:
    activations = [_activation("respond", 0.05)]
    mesh = build_horizontal_mesh(activations)
    decision = build_hybrid_stack_mesh(activations, mesh)

    assert decision.status == "fallback"
    assert decision.stop_reason == "no_eligible_candidates"
    assert decision.final_mode == mesh.winning_mode == "respond"


def test_hybrid_rejects_outputs_for_unselected_stack() -> None:
    activations = [_activation("respond", 0.7)]
    mesh = build_horizontal_mesh(activations)

    with pytest.raises(ValueError, match="unselected stack"):
        build_hybrid_stack_mesh(
            activations,
            mesh,
            outputs={"build": {}},
        )


def test_hybrid_fixed_evaluation_improves_branch_coverage() -> None:
    fixture = json.loads(
        HYBRID_EVALUATION_FIXTURE.read_text(encoding="utf-8")
    )
    cases = []
    for case in fixture:
        cases.append(
            {
                **case,
                "activations": [
                    _activation(unit_id, score)
                    for unit_id, score in case["activations"].items()
                ],
            }
        )
    report = evaluate_hybrid_candidate_coverage(cases)

    assert report["schema_version"] == HYBRID_EVALUATION_SCHEMA_VERSION
    assert report["case_count"] == 3
    assert report["budget_compliant"] is True
    assert report["horizontal_branch_recall"] == pytest.approx(0.6)
    assert report["hybrid_branch_recall"] == pytest.approx(1.0)
    assert report["hybrid_branch_recall"] > report[
        "horizontal_branch_recall"
    ]


def test_hybrid_pipeline_dispatches_namespaced_stacks() -> None:
    text = "設計案を比較して要約してください"
    initial = process(text, processing_mode="hybrid").as_dict()

    assert initial["pipeline_version"] == "1.6"
    assert initial["diagnostics"]["processing_mode"] == "hybrid"
    assert initial["hybrid_stack_mesh"]["budgets"] == {
        "max_stacks": 2,
        "max_total_steps": 3,
        "max_stack_depth": 2,
        "max_dispatches_per_call": 1,
        "used_stacks": 2,
        "used_steps": 3,
    }
    assert initial["hybrid_stack_mesh"]["next_dispatch"] == {
        "stack_id": "build",
        "unit_id": "verify",
    }
    assert initial["llm_order"]["mode"] == "verify"
    assert [stage["stage"] for stage in initial["trace"]] == [
        "input",
        "active_bits",
        "selected_units",
        "inhibition_integration",
        "horizontal_mesh",
        "hybrid_stack_mesh",
        "action_vector",
        "llm_order",
    ]

    failed_verify = _vertical_output(
        "verify",
        verified=False,
        verified_assumptions=[],
        risk_flags=["missing evidence"],
    )
    after_failure = process(
        text,
        processing_mode="hybrid",
        hybrid_outputs={
            "build": {"verify": failed_verify},
        },
    ).as_dict()
    assert after_failure["hybrid_stack_mesh"]["next_dispatch"] == {
        "stack_id": "summarize",
        "unit_id": "summarize",
    }
    assert after_failure["llm_order"]["mode"] == "summarize"

    marker = "hybrid-summary-private-marker-721"
    summarize = _vertical_output("summarize", summary=marker)
    completed_alternative = process(
        text,
        processing_mode="hybrid",
        hybrid_outputs={
            "summarize": {"summarize": summarize},
            "build": {"verify": failed_verify},
        },
    ).as_dict()
    assert completed_alternative["hybrid_stack_mesh"]["status"] == (
        "completed"
    )
    assert completed_alternative["hybrid_stack_mesh"][
        "winning_stack_id"
    ] == "summarize"
    assert completed_alternative["llm_order"]["mode"] == "summarize"
    assert marker not in json.dumps(completed_alternative)


def test_hybrid_pipeline_rejects_cross_mode_outputs() -> None:
    with pytest.raises(ValueError, match="hybrid_outputs require"):
        process("test", hybrid_outputs={})
    with pytest.raises(ValueError, match="vertical_outputs require"):
        process(
            "test",
            processing_mode="hybrid",
            vertical_outputs={},
        )


def test_hybrid_cli_accepts_namespaced_outputs(tmp_path) -> None:
    outputs = tmp_path / "hybrid-outputs.json"
    outputs.write_text(
        json.dumps(
            {
                "build": {
                    "verify": _vertical_output(
                        "verify",
                        verified=False,
                        verified_assumptions=[],
                        risk_flags=["missing evidence"],
                    )
                }
            }
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core",
            "--json",
            "--processing-mode",
            "hybrid",
            "--hybrid-outputs-file",
            str(outputs),
            "設計案を比較して要約してください",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(completed.stdout)

    assert payload["hybrid_stack_mesh"]["next_dispatch"] == {
        "stack_id": "summarize",
        "unit_id": "summarize",
    }
    assert payload["llm_order"]["mode"] == "summarize"


@pytest.mark.parametrize(
    ("profile_name", "minimum", "maximum"),
    [
        ("light_v1", 4, 10),
        ("normal_v1", 8, 18),
        ("design_v1", 14, 28),
        ("deep_verify_v1", 20, 36),
    ],
)
def test_threshold_profiles_bound_active_bit_count(
    profile_name: str,
    minimum: int,
    maximum: int,
) -> None:
    encoded = encode(
        "設計を実装してリスクを検証するための入力",
        threshold_profile=profile_name,
    )

    assert minimum <= encoded.thought_code.active_bit_count <= maximum
    assert encoded.threshold_profile == THRESHOLD_PROFILES[profile_name]


def test_design_and_verification_selects_deep_profile() -> None:
    encoded = encode("この設計を実装してテストしてください")

    assert encoded.threshold_profile.name == "deep_verify_v1"


def test_japanese_review_selects_verification_unit() -> None:
    result = process("この設計をレビューしてください")

    assert "verify" in {
        activation.unit_id for activation in result.selected_units
    }
    assert result.llm_order["mode"] == "verify"


def test_inhibition_matrix_suppresses_target_unit() -> None:
    source = UnitActivation("verify", "Verification", 0.8, 0.8, PATTERN_SHAPE)
    target = UnitActivation("build", "Implementation", 0.9, 0.9, PATTERN_SHAPE)

    result = integrate(
        [source, target],
        {"verify": {"build": 0.5}},
    )
    by_id = {activation.unit_id: activation for activation in result}

    assert by_id["verify"].integrated_score == pytest.approx(0.8)
    assert by_id["build"].integrated_score == pytest.approx(0.5)
    assert by_id["build"].inhibited_by["verify"] == pytest.approx(0.4)


def test_default_inhibition_matrix_loads_frozen_values_from_config() -> None:
    # Route groups expand to exactly the frozen v1.0a pairwise behavior.
    assert DEFAULT_INHIBITION_MATRIX == {
        "build": {"respond": 0.20},
        "clarify": {"build": 0.45, "respond": 0.25},
        "summarize": {"explore": 0.30},
        "verify": {"build": 0.35, "explore": 0.20},
    }
    assert load_inhibition_matrix() == DEFAULT_INHIBITION_MATRIX
    assert DEFAULT_INHIBITION_POLICY.schema_version == (
        "inhibition-matrix.v2"
    )
    assert DEFAULT_INHIBITION_POLICY.groups["clarification"] == (
        "clarify",
    )


def test_inhibition_group_policy_expands_across_route_categories(
    tmp_path,
) -> None:
    policy_path = tmp_path / "grouped.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": "inhibition-matrix.v2",
                "groups": {
                    "control": ["clarify", "verify"],
                    "construction": ["build", "explore"],
                    "compression": ["summarize"],
                    "direct": ["respond"],
                },
                "group_matrix": {
                    "control": {"construction": 0.5},
                },
                "matrix": {},
            }
        ),
        encoding="utf-8",
    )

    policy = load_inhibition_policy(policy_path)

    assert policy.matrix["clarify"] == {
        "build": 0.5,
        "explore": 0.5,
    }
    assert policy.matrix["verify"] == {
        "build": 0.5,
        "explore": 0.5,
    }


def test_inhibition_matrix_config_rejects_unknown_schema(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps({"schema_version": "nope", "matrix": {}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="schema"):
        load_inhibition_matrix(bad)


def test_unit_selection_policy_preserves_and_exposes_score_components() -> None:
    encoded = encode("この設計を実装してください")
    selected = select_units(encoded)
    build = next(item for item in selected if item.unit_id == "build")
    components = build.score_components
    policy = DEFAULT_UNIT_SELECTION_POLICY
    reconstructed = (
        policy.routing_weight * components["routing_overlap"]
        + policy.channel_affinity_weight * components["channel_affinity"]
        + policy.keyword_weight * components["keyword"]
        + components["bias"]
    )

    assert build.raw_score == pytest.approx(reconstructed)
    assert set(components) == {
        "routing_overlap",
        "channel_affinity",
        "keyword",
        "bias",
    }


def test_unit_selection_policy_rejects_unjustified_weight_total(
    tmp_path,
) -> None:
    payload = DEFAULT_UNIT_SELECTION_POLICY.as_dict()
    payload["weights"]["channel_affinity"] = 0.4
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="sum to 1.0"):
        load_unit_selection_policy(path)


@pytest.mark.parametrize(
    "matrix",
    [
        {"verfiy": {"build": 0.35}},
        {"verify": {"buidl": 0.35}},
        {"verify": {"build": True}},
        {"verify": {"verify": 0.10}},
    ],
)
def test_inhibition_matrix_config_rejects_invalid_contract_entries(
    tmp_path,
    matrix,
) -> None:
    bad = tmp_path / "bad-entry.json"
    bad.write_text(
        json.dumps(
            {
                "schema_version": "inhibition-matrix.v1",
                "matrix": matrix,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_inhibition_matrix(bad)


def test_pipeline_exposes_required_stages_and_metrics() -> None:
    result = process("この設計を実装してテストしてください")
    payload = result.as_dict()

    assert payload["schema_version"] == "vlte-bptm.pipeline.v1"
    assert payload["pipeline_version"] == "1.6"
    assert payload["input"]
    assert len(payload["thought_code"]["value"]) == 18
    assert payload["active_bits"]
    assert payload["selected_units"]
    for unit in payload["selected_units"]:
        assert unit["channel_schema_version"] == CHANNEL_SCHEMA_CONFIG_VERSION
        assert unit["channel_semantics"] == CHANNEL_SEMANTICS
        assert unit["prototype_channels"]
        assert unit["catalog_schema_version"] == UNIT_CATALOG_SCHEMA_VERSION
    assert set(payload["action_vector"]) == {
        "reply",
        "ask",
        "explain",
        "plan",
        "verify",
        "summarize",
        "creative",
        "caution",
    }
    assert (
        payload["action_vector_schema_version"]
        == ACTION_VECTOR_SCHEMA_VERSION
    )
    assert payload["llm_order"]["schema_version"] == LLM_ORDER_SCHEMA_VERSION
    assert payload["llm_order"]["routing_key"] == payload["thought_code"]["value"]
    assert payload["llm_order"]["mode"] in {"build", "verify"}
    assert (
        payload["llm_order"]["metadata"]["threshold_profile"]
        == payload["metrics"]["threshold_profile"]
    )
    assert payload["metrics"]["active_bit_count"] == len(
        payload["active_bits"]
    )
    assert payload["metrics"]["active_bit_density"] == pytest.approx(
        len(payload["active_bits"]) / 64,
        abs=1e-6,
    )
    assert payload["metrics"]["selected_unit_count"] == len(
        payload["selected_units"]
    )
    assert payload["metrics"]["threshold_profile"] == "deep_verify_v1"
    assert payload["diagnostics"]["processing_mode"] == "horizontal"
    assert payload["diagnostics"]["routing"]["density_guard"] == {
        "min_active_bits": 20,
        "max_active_bits": 36,
    }
    assert [stage["stage"] for stage in payload["trace"]] == [
        "input",
        "active_bits",
        "selected_units",
        "inhibition_integration",
        "horizontal_mesh",
        "action_vector",
        "llm_order",
    ]


def test_pipeline_does_not_request_learning_or_output_persistence() -> None:
    constraints = " ".join(process("test").llm_order["constraints"]).lower()

    assert "do not persist" in constraints
    assert "do not perform automatic learning" in constraints
    assert "do not train full-sentence regeneration" in constraints


def test_required_metrics_are_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="thought_core"):
        process("metric log test")

    message = caplog.messages[-1]
    assert "active_bit_count=" in message
    assert "active_bit_density=" in message
    assert "selected_unit_count=" in message
    assert "threshold_profile=" in message


def test_invalid_inhibition_coefficient_is_rejected() -> None:
    activation = UnitActivation("a", "A", 0.5, 0.5, PATTERN_SHAPE)

    with pytest.raises(ValueError):
        integrate([activation], {"a": {"a": 1.1}})


def test_demo_json_is_machine_parseable() -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thought_core",
            "--json",
            "実装",
            "検証",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )

    payload = json.loads(completed.stdout)
    assert payload["input"] == "実装 検証"
    assert payload["metrics"]["selected_unit_count"] >= 1
    assert payload["metrics"]["threshold_profile"] == "deep_verify_v1"
