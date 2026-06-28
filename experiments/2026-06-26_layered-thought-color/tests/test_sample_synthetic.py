from layered_thought_color.sample_synthetic import (
    SYNTHETIC_BATCH_SCHEMA_VERSION,
    build_generation_plan,
    generation_plan_summary,
    validate_batch_payload,
)


def _fake_case(spec):
    payload = spec.as_dict()
    payload.update(
        {
            "input": f"Synthetic request for {spec.base_label} {spec.sample_id}.",
            "judgment_questions": [
                "Does the base match the blueprint?",
                "Does the modifier match the blueprint?",
            ],
            "generation_note": "Fake case for validation.",
            "near_miss": {
                "wrong_base_label": "artifact_generation",
                "wrong_modifier": "neutral",
                "why_wrong": "The blueprint fixes the expected labels.",
            },
        }
    )
    return payload


def test_generation_plan_shape_is_175_samples():
    plan = build_generation_plan()
    summary = generation_plan_summary(plan)

    assert summary["task_count"] == 35
    assert summary["sample_count"] == 175
    assert len({task.task_id for task in plan}) == 35
    assert len({spec.sample_id for task in plan for spec in task.specs}) == 175


def test_synthetic_batch_validation_marks_review_required():
    task = build_generation_plan()[0]
    payload = {
        "schema_version": SYNTHETIC_BATCH_SCHEMA_VERSION,
        "task_id": task.task_id,
        "cases": [_fake_case(spec) for spec in task.specs],
    }

    samples = validate_batch_payload(payload, task)

    assert len(samples) == 5
    assert all(sample["human_review_required"] for sample in samples)
    assert not any(sample["training_allowed"] for sample in samples)
    assert all(
        sample["adoption_status"] == "synthetic_review_required"
        for sample in samples
    )



def test_synthetic_batch_validation_repairs_safe_format_drift():
    task = build_generation_plan()[0]
    cases = []
    for spec in task.specs:
        case = _fake_case(spec)
        case["id"] = case["id"].replace("-", "_")
        del case["generation_note"]
        cases.append(case)
    payload = {
        "schema_version": "thought-color-synthetic-batch.v0",
        "task_id": task.task_id.replace("-", "_"),
        "cases": cases,
    }

    samples = validate_batch_payload(payload, task)

    assert len(samples) == 5
    assert samples[0]["id"] == task.specs[0].sample_id
    warning_kinds = {
        warning["kind"]
        for sample in samples
        for warning in sample.get("validation_warnings", [])
    }
    assert "schema_version_repaired" in warning_kinds
    assert "task_id_format_repaired" in warning_kinds
    assert "id_format_repaired" in warning_kinds
    assert "missing_generation_note_repaired" in warning_kinds
