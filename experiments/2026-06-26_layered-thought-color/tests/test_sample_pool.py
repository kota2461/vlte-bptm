from layered_thought_color.sample_pool import LANES, load_sample_pool


def test_dedicated_sample_pool_is_valid_and_covers_lanes():
    pool = load_sample_pool()
    summary = pool.summary()

    assert summary["case_count"] == 32
    assert set(summary["lane_counts"]) == set(LANES)
    assert summary["language_counts"] == {"en": 23, "ja": 9}
    assert summary["multi_case_group_count"] == summary["group_count"]


def test_dedicated_sample_pool_contains_collision_shapes():
    pool = load_sample_pool()
    by_group = {}
    for case in pool.cases:
        by_group.setdefault(case.group_id, []).append(case)

    verify_variants = by_group["verify_stance_variants"]
    assert {case.expected.base_id for case in verify_variants} == {140}
    assert len({case.expected.stance for case in verify_variants}) >= 3

    code_split = by_group["code_request_split"]
    assert len({case.expected.base_id for case in code_split}) == 3
    assert {case.collision_policy for case in code_split} == {"split_base"}


