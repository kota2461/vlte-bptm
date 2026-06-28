import pytest

from layered_thought_color import (
    BASE_COUNT,
    ThoughtColorCode,
    collision_profile,
    raw_capacity,
    valid_capacity,
)


def test_pack_round_trip_preserves_channels():
    code = ThoughtColorCode.from_labels(
        base_id=2023,
        stance="explore",
        operation="verify",
        intensity="hold",
    )

    assert ThoughtColorCode.unpack(code.pack()) == code
    assert code.factorized_features() == {
        "base_id": 2023,
        "stance": 3,
        "operation": 3,
        "intensity": 3,
    }


def test_base_2024_boundary_is_reserved():
    with pytest.raises(ValueError, match="base_id"):
        ThoughtColorCode(base_id=BASE_COUNT)

    reserved_base_token = BASE_COUNT
    with pytest.raises(ValueError, match="base_id"):
        ThoughtColorCode.unpack(reserved_base_token)


def test_capacity_documents_raw_vs_valid_space():
    assert raw_capacity() == 1 << 19
    assert valid_capacity() == 2024 * 8 * 8 * 4
    assert raw_capacity() - valid_capacity() == 24 * 8 * 8 * 4


def test_sparse_features_do_not_collapse_to_packed_id_only():
    code = ThoughtColorCode.from_labels(
        base_id=7,
        stance="clarify",
        operation="respond",
        intensity="low",
    )

    sparse = code.sparse_features()

    assert f"packed:{code.pack()}" not in sparse
    assert "base:0007" in sparse
    assert "stance:clarify" in sparse
    assert "operation:respond" in sparse


def test_collision_profile_keeps_base_collision_visible():
    codes = (
        ThoughtColorCode.from_labels(
            base_id=42,
            stance="explore",
            operation="verify",
            intensity="medium",
        ),
        ThoughtColorCode.from_labels(
            base_id=42,
            stance="clarify",
            operation="respond",
            intensity="low",
        ),
        ThoughtColorCode.from_labels(
            base_id=42,
            stance="clarify",
            operation="respond",
            intensity="low",
        ),
    )

    profile = collision_profile(codes)

    assert profile["unique_base_count"] == 1
    assert profile["unique_full_count"] == 2
    assert profile["base_collision_bucket_count"] == 1
    assert profile["modifier_separated_base_count"] == 1
    assert profile["exact_duplicate_count"] == 1

