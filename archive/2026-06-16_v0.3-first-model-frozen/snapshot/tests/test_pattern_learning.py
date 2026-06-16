import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pattern_learning import (
    boundary_curriculum,
    boundary_curriculum_v2,
    language_curriculum,
)
from pattern_learning import deployment
from pattern_learning.database import PatternDatabase
from pattern_learning.deployment import (
    acknowledge_improvement_regression,
    evaluate_gate,
    promote,
    rollback,
    run_deployment_gate,
)
from pattern_learning.extractor import extract_patterns
from pattern_learning.tiers import (
    FOUNDATION_TIER,
    REFINEMENT_TIER,
    curriculum_tier,
)
from pattern_learning.math_curriculum import (
    LEVELS,
    MATH_CURRICULUM,
    curriculum_document,
    curriculum_drafts,
)
from pattern_learning.models import PatternDraft, ReviewDecision, SourceDocument
from pattern_learning.server import PatternLabApplication, STATIC_DIR
from pattern_learning.trainer import RouterModel, train_router
from pattern_learning.wikipedia import WikipediaClient


def _document(title: str = "Test source") -> SourceDocument:
    return SourceDocument(
        source_kind="test",
        title=title,
        url=f"https://example.test/{title}",
        revision_id="42",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        license_name="CC BY-SA 4.0",
        attribution="Test contributors",
        text="",
    )


def _draft(
    text: str,
    route: str,
    operators: list[str],
) -> PatternDraft:
    return PatternDraft(
        input_text=text,
        suggested_route=route,
        suggested_operators=operators,
        thought_form={
            "facts": [text],
            "goals": [],
            "constraints": [],
            "uncertainty": [],
            "operation": operators[0],
            "candidates": [],
        },
        confidence=0.8,
    )


def test_only_approved_candidate_enters_pattern_db(tmp_path: Path) -> None:
    database = PatternDatabase(tmp_path / "patterns.db")
    database.add_document(
        _document(),
        [
            _draft("この機能を実装してください", "build", ["sequence"]),
            _draft("設計の根拠を検証してください", "verify", ["verification"]),
        ],
    )
    candidates = database.list_candidates()

    database.review(
        ReviewDecision(
            candidate_id=candidates[0]["id"],
            verdict="approve",
            rating=5,
            route="build",
            operators=["sequence", "decomposition"],
            notes="useful",
        )
    )
    database.review(
        ReviewDecision(
            candidate_id=candidates[1]["id"],
            verdict="reject",
            rating=1,
            notes="not reusable",
        )
    )

    patterns = database.training_examples()
    assert len(patterns) == 1
    assert patterns[0]["route"] == "build"
    assert patterns[0]["operators"] == ["sequence", "decomposition"]
    assert patterns[0]["source"]["revision_id"] == "42"
    assert database.stats()["candidates"] == {
        "pending": 0,
        "approved": 1,
        "rejected": 1,
        "total": 2,
    }


def test_rejecting_a_previously_approved_candidate_removes_pattern(
    tmp_path: Path,
) -> None:
    database = PatternDatabase(tmp_path / "patterns.db")
    database.add_document(
        _document(),
        [_draft("実装してください", "build", ["sequence"])],
    )
    candidate_id = database.list_candidates()[0]["id"]
    database.review(
        ReviewDecision(candidate_id, "approve", 4)
    )
    database.review(
        ReviewDecision(candidate_id, "reject", 2)
    )

    assert database.training_examples() == []
    assert database.get_candidate(candidate_id)["status"] == "rejected"


def test_extractor_creates_structured_review_candidates() -> None:
    document = SourceDocument(
        source_kind="test",
        title="Logic",
        url="https://example.test/logic",
        revision_id="7",
        fetched_at="2026-06-09T00:00:00+00:00",
        license_name="CC BY-SA 4.0",
        attribution="Example",
        text=(
            "命題とは、真または偽が明確に定まる文である。"
            "条件が成立する場合、次に結論を検証する必要がある。"
        ),
    )

    drafts = extract_patterns(document)

    assert len(drafts) == 2
    assert "definition" in drafts[0].suggested_operators
    assert "condition" in drafts[1].suggested_operators
    assert "verification" in drafts[1].suggested_operators
    assert drafts[0].thought_form["facts"]


def test_wikipedia_client_requires_contactable_user_agent() -> None:
    with pytest.raises(ValueError, match="contact"):
        WikipediaClient("PatternLab")

    client = WikipediaClient("PatternLab/0.1 (owner@example.com)")
    assert client.user_agent == "PatternLab/0.1 (owner@example.com)"


def test_router_training_uses_approved_patterns_and_saves_model(
    tmp_path: Path,
) -> None:
    database = PatternDatabase(tmp_path / "patterns.db")
    drafts = [
        _draft("Pythonで機能を実装してください", "build", ["sequence"]),
        _draft("画面を設計してコードを書いてください", "build", ["decomposition"]),
        _draft("設計のリスクを検証してください", "verify", ["verification"]),
        _draft("根拠を確認してレビューしてください", "verify", ["verification"]),
    ]
    database.add_document(_document(), drafts)
    for candidate in database.list_candidates():
        database.review(
            ReviewDecision(
                candidate_id=candidate["id"],
                verdict="approve",
                rating=5,
            )
        )

    model_path = tmp_path / "router.json"
    result = train_router(database, model_path, epochs=30, dimension=512)
    model = RouterModel.load(model_path)

    assert result["sample_count"] == 4
    assert result["metrics"]["training_accuracy"] == 1.0
    assert model.predict("コードを実装してください").route == "build"
    assert model.predict("リスクをレビューして検証").route == "verify"
    assert json.loads(model_path.read_text(encoding="utf-8"))[
        "schema_version"
    ] == "pattern-router.model.v1"
    # Too few samples to calibrate honestly -> abstention is disabled and
    # predictions pass through unchanged (no surprise clarify fallback).
    assert model.metadata["confidence_calibrated"] is False
    passthrough = model.predict("コードを実装してください")
    assert passthrough.effective_route == passthrough.route
    assert passthrough.low_confidence is False


def test_isotonic_bins_enforce_monotonic_calibration() -> None:
    from pattern_learning.trainer import _isotonic_bins

    # A noisy low tail bin sitting above high bins must be pooled, never
    # leaving calibrated accuracy decreasing as raw confidence rises.
    fitted = _isotonic_bins([0.4, 0.9, 0.9, 0.5], [100, 100, 100, 2])
    assert fitted == sorted(fitted)
    assert fitted[-1] < 0.9  # the trailing 0.5 bin got pooled down


def test_calibration_abstains_only_below_threshold() -> None:
    from pattern_learning.trainer import RouterModel

    model = RouterModel(
        labels=["respond", "clarify", "verify"],
        dimension=32,
        weights={"respond": {}, "clarify": {}, "verify": {}},
        bias={"respond": 0.0, "clarify": 0.0, "verify": 0.0},
        operator_priors={},
        metadata={
            "confidence_calibrated": True,
            "calibration": {
                "decision_threshold": 0.2,
                "fallback_route": "clarify",
                "reliability": [
                    {"min_confidence": 0.10, "max_confidence": 0.20,
                     "accuracy": 0.45, "count": 100},
                    {"min_confidence": 0.20, "max_confidence": 0.40,
                     "accuracy": 0.90, "count": 100},
                ],
            },
        },
    )

    # Below threshold and not already clarify -> abstain to clarify.
    route, low, calibrated = model._apply_calibration("verify", 0.18)
    assert (route, low, calibrated) == ("clarify", True, 0.45)
    # Above threshold -> trust the raw route, calibrated to the high bin.
    route, low, calibrated = model._apply_calibration("respond", 0.30)
    assert (route, low, calibrated) == ("respond", False, 0.90)
    # Raw route already clarify -> never flagged as a fallback.
    route, low, _ = model._apply_calibration("clarify", 0.18)
    assert (route, low) == ("clarify", False)


def test_calibration_covers_numeric_gaps_between_observed_bins() -> None:
    model = RouterModel(
        labels=["clarify", "verify"],
        dimension=32,
        weights={"clarify": {}, "verify": {}},
        bias={"clarify": 0.0, "verify": 0.0},
        operator_priors={},
        metadata={
            "calibration": {
                "decision_threshold": 0.0,
                "fallback_route": "clarify",
                "reliability": [
                    {
                        "min_confidence": 0.10,
                        "max_confidence": 0.20,
                        "accuracy": 0.40,
                    },
                    {
                        "min_confidence": 0.21,
                        "max_confidence": 0.30,
                        "accuracy": 0.80,
                    },
                ],
            }
        },
    )

    # 0.205 lies between observed ranges and must map to the next upper-bound
    # bin rather than leaking the uncalibrated raw confidence.
    _, _, calibrated = model._apply_calibration("verify", 0.205)
    assert calibrated == 0.80


def test_calibration_reports_selective_metrics_without_calling_abstention_correct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pattern_learning import trainer

    points = (
        [(False, 0.10)] * 8
        + [(True, 0.11)] * 2
        + [(True, 0.50)] * 20
    )
    monkeypatch.setattr(trainer, "_kfold_points", lambda *args: points)
    examples = [
        {"input_text": str(index), "route": "build", "quality_score": 5}
        for index in range(30)
    ]

    calibration = trainer._calibrate(
        examples,
        ["build", "clarify"],
        dimension=32,
        epochs=1,
        learning_rate=0.1,
        seed=1,
    )

    assert calibration is not None
    diagnostics = calibration["abstention_diagnostics"]
    assert diagnostics["abstained_count"] > 0
    assert diagnostics["coverage"] < 1.0
    assert diagnostics["selective_accuracy"] == 1.0
    assert "corrected" not in diagnostics
    assert "abstention_utility" not in calibration


def test_training_requires_two_routes(tmp_path: Path) -> None:
    database = PatternDatabase(tmp_path / "patterns.db")
    candidate_id = database.add_manual_candidate(
        "実装してください",
        "build",
        ["sequence"],
        {"facts": ["実装してください"], "operation": "sequence"},
    )
    database.review(ReviewDecision(candidate_id, "approve", 5))

    with pytest.raises(ValueError, match="at least two approved"):
        train_router(database, tmp_path / "model.json")


def test_application_exposes_review_workflow(tmp_path: Path) -> None:
    application = PatternLabApplication(
        tmp_path / "patterns.db",
        tmp_path / "model.json",
    )
    created = application.post(
        "/api/candidates/manual",
        {
            "input_text": "不足条件を質問してください",
            "route": "clarify",
            "operators": ["condition"],
        },
    )
    candidate_id = created["candidate"]["id"]

    reviewed = application.post(
        "/api/reviews",
        {
            "candidate_id": candidate_id,
            "verdict": "approve",
            "rating": 4,
            "route": "clarify",
            "operators": ["condition"],
            "thought_form": {
                "facts": [],
                "goals": ["clarify missing conditions"],
                "constraints": [],
                "uncertainty": ["missing input"],
                "operation": "condition",
                "candidates": [],
            },
        },
    )

    assert reviewed["candidate"]["status"] == "approved"
    assert application.get("/api/stats", {})["patterns"] == 1
    assert (STATIC_DIR / "index.html").is_file()


def test_api_review_without_operators_keeps_suggested_values(
    tmp_path: Path,
) -> None:
    application = PatternLabApplication(
        tmp_path / "patterns.db",
        tmp_path / "model.json",
    )
    created = application.post(
        "/api/candidates/manual",
        {
            "input_text": "リスクを検証してください",
            "route": "verify",
            "operators": ["verification", "uncertainty"],
        },
    )
    candidate_id = created["candidate"]["id"]

    reviewed = application.post(
        "/api/reviews",
        {"candidate_id": candidate_id, "verdict": "approve", "rating": 5},
    )

    assert reviewed["candidate"]["status"] == "approved"
    pattern = application.database.training_examples()[0]
    assert pattern["operators"] == ["verification", "uncertainty"]
    assert pattern["route"] == "verify"
    assert pattern["thought_form"]["facts"] == ["リスクを検証してください"]


def test_math_curriculum_is_consistent_and_seeds_pending_only(
    tmp_path: Path,
) -> None:
    texts = [pattern.text for pattern in MATH_CURRICULUM]
    assert len(texts) == len(set(texts))
    assert {pattern.level for pattern in MATH_CURRICULUM} == set(LEVELS)
    assert all(1 <= pattern.rating <= 5 for pattern in MATH_CURRICULUM)
    # 同回答バリエーション: 答えが8になる加算が複数表現で含まれる
    same_answer = [
        pattern
        for pattern in MATH_CURRICULUM
        if pattern.level == "addition" and "8" in "".join(
            pattern.answer_candidates
        )
    ]
    assert len(same_answer) >= 5

    drafts = curriculum_drafts()
    assert len(drafts) == len(MATH_CURRICULUM)
    assert len({draft.suggested_route for draft in drafts}) >= 2

    database = PatternDatabase(tmp_path / "patterns.db")
    inserted = database.add_document(curriculum_document(), drafts)
    assert inserted == len(MATH_CURRICULUM)
    stats = database.stats()
    assert stats["candidates"]["pending"] == len(MATH_CURRICULUM)
    assert stats["patterns"] == 0  # 承認なしでは学習資産に入らない


def test_language_curriculum_is_consistent_and_covers_greetings(
    tmp_path: Path,
) -> None:
    patterns = language_curriculum.LANGUAGE_CURRICULUM
    texts = [pattern.text for pattern in patterns]
    assert len(texts) == len(set(texts))
    assert {pattern.level for pattern in patterns} == set(
        language_curriculum.LEVELS
    )
    assert all(1 <= pattern.rating <= 5 for pattern in patterns)
    # 挨拶は日本語・英語の両方で respond ルートに揃っている
    greetings = [
        pattern
        for pattern in patterns
        if pattern.level in {"greetings_ja", "greetings_en"}
    ]
    assert len(greetings) >= 12
    assert all(pattern.route == "respond" for pattern in greetings)

    drafts = language_curriculum.curriculum_drafts()
    assert len(drafts) == len(patterns)
    assert len({draft.suggested_route for draft in drafts}) >= 2

    database = PatternDatabase(tmp_path / "patterns.db")
    inserted = database.add_document(
        language_curriculum.curriculum_document(), drafts
    )
    assert inserted == len(patterns)
    assert database.stats()["patterns"] == 0  # 承認前は学習資産に入らない


def test_boundary_curriculum_is_balanced_contrast_data_and_seeds_pending_only(
    tmp_path: Path,
) -> None:
    patterns = boundary_curriculum.BOUNDARY_CURRICULUM
    assert len(patterns) == 24
    assert len({pattern.text for pattern in patterns}) == len(patterns)
    assert {pattern.boundary for pattern in patterns} == {
        "explore_respond",
        "clarify_verify",
        "explore_build",
    }
    routes = {pattern.route for pattern in patterns}
    assert {"explore", "respond", "clarify", "verify", "build"} <= routes

    database = PatternDatabase(tmp_path / "patterns.db")
    inserted = database.add_document(
        boundary_curriculum.curriculum_document(),
        boundary_curriculum.curriculum_drafts(),
    )

    assert inserted == len(patterns)
    assert database.stats()["candidates"]["pending"] == len(patterns)
    assert database.stats()["patterns"] == 0


def test_boundary_curriculum_v2_is_original_grouped_and_pending_only(
    tmp_path: Path,
) -> None:
    patterns = boundary_curriculum_v2.BOUNDARY_CURRICULUM_V2
    assert len(patterns) == 52
    assert len({pattern.text for pattern in patterns}) == len(patterns)
    assert not (
        {pattern.text for pattern in patterns}
        & {pattern.text for pattern in boundary_curriculum.BOUNDARY_CURRICULUM}
    )
    assert {pattern.boundary for pattern in patterns} == {
        "explore_respond",
        "build_respond",
        "clarify_verify",
        "explore_build",
    }
    groups = {}
    for pattern in patterns:
        groups.setdefault(pattern.contrast_group, []).append(pattern)
    assert len(groups) == 26
    assert all(len(group) == 2 for group in groups.values())
    assert all(
        len({pattern.route for pattern in group}) == 2
        for group in groups.values()
    )
    assert all(
        len({pattern.boundary for pattern in group}) == 1
        and len({pattern.language for pattern in group}) == 1
        and len({pattern.difficulty for pattern in group}) == 1
        for group in groups.values()
    )
    assert all(pattern.language in {"ja", "en"} for pattern in patterns)
    assert all(
        pattern.difficulty in {"simple", "compound"}
        for pattern in patterns
    )
    assert all(pattern.template_id for pattern in patterns)

    # 否定マーカーが単一Routeのラベルを表層分離しないこと(外部レビュー指摘の
    # 再発防止)。revision 1ではrespond 12/12が否定メタ指示を含んでいた。
    negation = re.compile(r"ず、|ずに|せず|Do not|do not|without")
    by_route: dict[str, list[bool]] = {}
    for pattern in patterns:
        by_route.setdefault(pattern.route, []).append(
            bool(negation.search(pattern.text))
        )
    for route, flags in by_route.items():
        assert sum(flags) < len(flags), (
            f"route {route} is fully negation-marked (surface confound)"
        )
    routes_with_negation = {
        route for route, flags in by_route.items() if any(flags)
    }
    assert len(routes_with_negation) >= 3

    document = boundary_curriculum_v2.curriculum_document()
    assert document.metadata["ai_assisted_authoring"] is True
    assert document.metadata["teacher_model_outputs_used"] is False
    assert document.metadata["copied_source_text_used"] is False
    assert document.metadata["hidden_reasoning_used"] is False
    assert document.metadata["approval_required"] is True
    assert document.metadata["authoring_models"]["revision2_rewrite"]
    assert document.revision_id == "2"
    drafts = boundary_curriculum_v2.curriculum_drafts()
    assert all(
        draft.thought_form["ai_assisted_authoring"] is True
        and draft.thought_form["teacher_output_used"] is False
        and draft.thought_form["copied_source_text_used"] is False
        and draft.thought_form["contrast_group"]
        and draft.thought_form["template_id"]
        and draft.thought_form["curriculum_revision"] == "2"
        for draft in drafts
    )

    database = PatternDatabase(tmp_path / "patterns.db")
    inserted = database.add_document(document, drafts)

    assert inserted == 52
    assert database.stats()["candidates"]["pending"] == 52
    assert database.stats()["patterns"] == 0


def test_boundary_curriculum_v2_cli_is_idempotent_pending_seed(
    tmp_path: Path,
) -> None:
    database = tmp_path / "patterns.db"
    command = [
        sys.executable,
        "-m",
        "pattern_learning",
        "--db",
        str(database),
        "seed-boundaries-v2",
    ]
    first = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    second = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "inserted 52 pending boundary v2 candidates" in first.stdout
    assert "inserted 0 pending boundary v2 candidates" in second.stdout
    stats = PatternDatabase(database).stats()
    assert stats["candidates"]["pending"] == 52
    assert stats["patterns"] == 0


def test_curriculum_tiers_derive_from_source_url() -> None:
    assert curriculum_tier("curriculum://math-v1") == FOUNDATION_TIER
    assert curriculum_tier("curriculum://language-v1") == FOUNDATION_TIER
    assert (
        curriculum_tier("curriculum://route-boundaries-v2-round1")
        == REFINEMENT_TIER
    )
    # 未知の出典はfoundationに昇格しない(安全側)
    assert curriculum_tier("manual://abc123") == REFINEMENT_TIER
    assert curriculum_tier("") == REFINEMENT_TIER


def _gate_model(bias_label: str) -> RouterModel:
    return RouterModel(
        labels=["build", "verify"],
        dimension=32,
        weights={"build": {}, "verify": {}},
        bias={
            "build": 1.0 if bias_label == "build" else 0.0,
            "verify": 1.0 if bias_label == "verify" else 0.0,
        },
        operator_priors={},
        metadata={},
    )


def test_deployment_gate_blocks_and_promote_refuses_failures(
    tmp_path: Path,
) -> None:
    model = _gate_model("build")  # 全入力をbuildへ送るモデル
    regression_cases = [
        {"name": "ok", "route": "build", "input": "実装手順を組んで"},
        {"name": "broken", "route": "verify", "input": "検算してください"},
    ]
    foundation_cases = [
        {"input": "こんにちは", "route": "verify", "source": "test"},
    ]
    report = evaluate_gate(model, regression_cases, foundation_cases)

    assert report["passed"] is False
    assert report["checks"]["frozen_regression"]["passed"] is False
    assert len(report["checks"]["foundation_anchors"]["raw_misses"]) == 1

    candidate = tmp_path / "candidate.json"
    deployed = tmp_path / "deployed.json"
    model.save(candidate)
    with pytest.raises(ValueError, match="gate failed"):
        promote(candidate, deployed, report)
    assert not deployed.exists()  # 不合格候補はデプロイへ到達しない


def test_deployment_gate_passes_and_promotes(tmp_path: Path) -> None:
    model = _gate_model("verify")
    regression_cases = [
        {"name": "ok", "route": "verify", "input": "検算してください"},
    ]
    foundation_cases = [
        {"input": "確認して", "route": "verify", "source": "test"},
    ]
    report = evaluate_gate(model, regression_cases, foundation_cases)
    assert report["passed"] is True

    candidate = tmp_path / "candidate.json"
    deployed = tmp_path / "deployed.json"
    model.save(candidate)
    promoted_path = promote(candidate, deployed, report)

    assert promoted_path == deployed
    assert deployed.exists()
    gate_report_path = deployed.with_name("deployment_gate_report.json")
    saved = json.loads(gate_report_path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == "router-deployment-gate.v3"
    assert saved["passed"] is True
    assert "promoted_at" in saved["promotion"]


def _write_gate_environment(tmp_path: Path) -> dict:
    """Tiny self-consistent fixtures + registry for gate integration tests."""

    regression = [
        {"name": "v", "route": "verify", "input": "検算してください"},
    ]
    foundation = {
        "schema_version": "foundation-anchor-suite.v1",
        "cases": [
            {"input": "確認して", "route": "verify", "source": "test"},
        ],
    }
    regression_path = tmp_path / "regression.json"
    foundation_path = tmp_path / "foundation.json"
    regression_path.write_text(
        json.dumps(regression, ensure_ascii=False), encoding="utf-8"
    )
    foundation_path.write_text(
        json.dumps(foundation, ensure_ascii=False), encoding="utf-8"
    )
    registry = {
        "schema_version": "gate-fixture-registry.v1",
        "fixtures": {
            regression_path.name: {
                "version": "test",
                "sha256": deployment.file_sha256(regression_path),
                "min_case_count": 1,
                "min_route_counts": {"verify": 1},
            },
            foundation_path.name: {
                "version": "test",
                "sha256": deployment.file_sha256(foundation_path),
                "min_case_count": 1,
                "min_route_counts": {"verify": 1},
            },
        },
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False), encoding="utf-8"
    )
    candidate = tmp_path / "candidate.json"
    _gate_model("verify").save(candidate)
    return {
        "regression": regression_path,
        "foundation": foundation_path,
        "registry": registry_path,
        "candidate": candidate,
        "deployed": tmp_path / "deployed.json",
    }


def test_gate_records_hashes_and_fails_on_fixture_tampering(
    tmp_path: Path,
) -> None:
    env = _write_gate_environment(tmp_path)
    report = run_deployment_gate(
        env["candidate"],
        regression_fixture=env["regression"],
        foundation_fixture=env["foundation"],
        registry_path=env["registry"],
        deployed_path=env["deployed"],
        database_path=tmp_path / "absent.db",
    )
    assert report["passed"] is True
    assert report["hashes"]["candidate_sha256"]
    assert report["hashes"]["fixtures"][env["regression"].name]
    assert report["checks"]["fixture_integrity"]["passed"] is True

    # 改ざん: anchorを書き換えるとSHA不一致で不合格になる
    env["foundation"].write_text(
        json.dumps(
            {
                "schema_version": "foundation-anchor-suite.v1",
                "cases": [
                    {"input": "確認して", "route": "build", "source": "t"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    tampered = run_deployment_gate(
        env["candidate"],
        regression_fixture=env["regression"],
        foundation_fixture=env["foundation"],
        registry_path=env["registry"],
        deployed_path=env["deployed"],
        database_path=tmp_path / "absent.db",
    )
    assert tampered["passed"] is False
    assert tampered["checks"]["fixture_integrity"]["passed"] is False


def test_improvement_check_blocks_metric_degradation() -> None:
    current = {"validation_accuracy": 0.80, "kfold_accuracy": 0.75}
    degraded = deployment._check_improvement(
        current, {"validation_accuracy": 0.75, "kfold_accuracy": 0.75}
    )
    assert degraded["passed"] is False
    within_tolerance = deployment._check_improvement(
        current, {"validation_accuracy": 0.79, "kfold_accuracy": 0.74}
    )
    assert within_tolerance["passed"] is True
    first_deployment = deployment._check_improvement(None, {"x": 1})
    assert first_deployment["passed"] is True


def test_improvement_ack_requires_contract_and_matching_sealed_evidence(
    tmp_path: Path,
) -> None:
    env = _write_gate_environment(tmp_path)
    candidate_model = _gate_model("verify")
    candidate_model.metadata["metrics"] = {
        "validation_accuracy": 0.70,
        "kfold_accuracy": 0.81,
    }
    candidate_model.save(env["candidate"])
    deployed_model = _gate_model("verify")
    deployed_model.metadata["metrics"] = {
        "validation_accuracy": 0.80,
        "kfold_accuracy": 0.75,
    }
    deployed_model.save(env["deployed"])

    sealed_fixture = tmp_path / "sealed_v1.json"
    sealed_fixture.write_text('{"cases":[]}', encoding="utf-8")
    registry = json.loads(env["registry"].read_text(encoding="utf-8"))
    registry["fixtures"][sealed_fixture.name] = {
        "version": "v1.0",
        "sha256": deployment.file_sha256(sealed_fixture),
        "role": "sealed measurement only",
    }
    env["registry"].write_text(
        json.dumps(registry, ensure_ascii=False), encoding="utf-8"
    )

    report = run_deployment_gate(
        env["candidate"],
        regression_fixture=env["regression"],
        foundation_fixture=env["foundation"],
        registry_path=env["registry"],
        deployed_path=env["deployed"],
        database_path=tmp_path / "absent.db",
    )
    assert report["contract_passed"] is True
    assert report["passed"] is False

    sealed_sha = deployment.file_sha256(sealed_fixture)
    candidate_result = tmp_path / "candidate-sealed.json"
    deployed_result = tmp_path / "deployed-sealed.json"
    candidate_result.write_text(
        json.dumps(
            {
                "schema_version": "sealed-slice-eval.v1",
                "sealed_sha256": sealed_sha,
                "model_sha256": deployment.file_sha256(env["candidate"]),
                "total": {"correct": 2, "count": 2},
            }
        ),
        encoding="utf-8",
    )
    deployed_result.write_text(
        json.dumps(
            {
                "schema_version": "sealed-slice-eval.v1",
                "sealed_sha256": sealed_sha,
                "model_sha256": deployment.file_sha256(env["deployed"]),
                "total": {"correct": 1, "count": 2},
            }
        ),
        encoding="utf-8",
    )

    mismatched_result = tmp_path / "mismatched-candidate-sealed.json"
    mismatched_result.write_text(
        json.dumps(
            {
                "schema_version": "sealed-slice-eval.v1",
                "sealed_sha256": sealed_sha,
                "model_sha256": "BAD-HASH",
                "total": {"correct": 2, "count": 2},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="candidate sealed result model hash"):
        acknowledge_improvement_regression(
            report,
            reason="evidence must match the gated candidate",
            candidate_sealed_result=mismatched_result,
            deployed_sealed_result=deployed_result,
            registry_path=env["registry"],
        )

    acknowledged = acknowledge_improvement_regression(
        report,
        reason="holdout composition changed; same sealed slice improved",
        candidate_sealed_result=candidate_result,
        deployed_sealed_result=deployed_result,
        registry_path=env["registry"],
        actor="test-reviewer",
    )
    assert acknowledged["passed"] is True
    assert acknowledged["decision"] == "pass_with_improvement_ack"
    ack = acknowledged["checks"]["improvement_vs_deployed"][
        "acknowledgment"
    ]
    assert ack["scope"] == "improvement_vs_deployed_only"
    assert ack["evidence"]["candidate_score"]["correct"] == 2

    env["foundation"].write_text(
        json.dumps(
            {
                "schema_version": "foundation-anchor-suite.v1",
                "cases": [
                    {"input": "確認して", "route": "build", "source": "test"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    blocked = run_deployment_gate(
        env["candidate"],
        regression_fixture=env["regression"],
        foundation_fixture=env["foundation"],
        registry_path=env["registry"],
        deployed_path=env["deployed"],
        database_path=tmp_path / "absent.db",
    )
    with pytest.raises(ValueError, match="contract checks failed"):
        acknowledge_improvement_regression(
            blocked,
            reason="must not bypass integrity",
            candidate_sealed_result=candidate_result,
            deployed_sealed_result=deployed_result,
            registry_path=env["registry"],
        )


def test_promote_refuses_changed_candidate_hash(tmp_path: Path) -> None:
    env = _write_gate_environment(tmp_path)
    report = run_deployment_gate(
        env["candidate"],
        regression_fixture=env["regression"],
        foundation_fixture=env["foundation"],
        registry_path=env["registry"],
        deployed_path=env["deployed"],
        database_path=tmp_path / "absent.db",
    )
    assert report["passed"] is True
    # ゲート後に候補が差し替わったら昇格を拒否する
    _gate_model("build").save(env["candidate"])
    with pytest.raises(ValueError, match="hash changed"):
        promote(env["candidate"], env["deployed"], report)
    assert not env["deployed"].exists()


def test_promotion_archives_previous_and_rollback_restores(
    tmp_path: Path,
) -> None:
    env = _write_gate_environment(tmp_path)
    history = tmp_path / "history"

    def gate() -> dict:
        return run_deployment_gate(
            env["candidate"],
            regression_fixture=env["regression"],
            foundation_fixture=env["foundation"],
            registry_path=env["registry"],
            deployed_path=env["deployed"],
            database_path=tmp_path / "absent.db",
        )

    promote(env["candidate"], env["deployed"], gate(), history_dir=history)
    first_sha = deployment.file_sha256(env["deployed"])

    # 2回目の昇格で旧モデルが履歴へ保存される
    model = _gate_model("verify")
    model.metadata["marker"] = "second"
    model.save(env["candidate"])
    promote(env["candidate"], env["deployed"], gate(), history_dir=history)
    archived = list(history.glob("deployed_*.json"))
    assert len(archived) == 1
    assert deployment.file_sha256(archived[0]) == first_sha

    # rollback: 現行を隔離し、直前の承認済みモデルを復元する
    with pytest.raises(ValueError, match="reason"):
        rollback(env["deployed"], history, reason="  ")
    report = rollback(env["deployed"], history, reason="anchor violation")
    assert deployment.file_sha256(env["deployed"]) == first_sha
    assert list(history.glob("quarantined_*.json"))
    assert report["reason"] == "anchor violation"

    empty_history = tmp_path / "empty"
    empty_history.mkdir()
    with pytest.raises(ValueError, match="no archived model"):
        rollback(env["deployed"], empty_history, reason="x")


def test_round2_batches_are_consistent_and_pending_only(
    tmp_path: Path,
) -> None:
    from pattern_learning import boundary_round2_user, english_routes_round2b

    user_drafts = boundary_round2_user.curriculum_drafts()
    english_drafts = english_routes_round2b.curriculum_drafts()
    assert len(user_drafts) == 10
    assert len(english_drafts) == 8

    # 対照groupは必ず2件1組でRouteが異なる
    groups: dict[str, list] = {}
    for pattern in boundary_round2_user.BOUNDARY_ROUND2_USER:
        groups.setdefault(pattern.contrast_group, []).append(pattern)
    assert all(len(group) == 2 for group in groups.values())
    assert all(
        len({pattern.route for pattern in group}) == 2
        for group in groups.values()
    )

    # sealedスライスと学習候補の本文は重複しない
    sealed = json.loads(
        (
            Path(__file__).parent
            / "fixtures"
            / "sealed_boundary_slice_v1.json"
        ).read_text(encoding="utf-8")
    )
    sealed_texts = {case["input"] for case in sealed["cases"]}
    training_texts = {draft.input_text for draft in user_drafts}
    training_texts |= {draft.input_text for draft in english_drafts}
    assert not (sealed_texts & training_texts)
    assert len(sealed["cases"]) >= 20

    sealed_v2 = json.loads(
        (
            Path(__file__).parent
            / "fixtures"
            / "sealed_boundary_slice_v2.json"
        ).read_text(encoding="utf-8")
    )
    sealed_v2_texts = {case["input"] for case in sealed_v2["cases"]}
    assert not (sealed_v2_texts & training_texts)
    assert not (sealed_v2_texts & sealed_texts)
    registry = json.loads(
        (
            Path(__file__).parent
            / "fixtures"
            / "gate_fixture_registry.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        registry["fixtures"]["sealed_boundary_slice_v1.json"]["status"]
        == "consumed"
    )
    assert (
        registry["fixtures"]["sealed_boundary_slice_v2.json"]["status"]
        == "active"
    )

    database = PatternDatabase(tmp_path / "patterns.db")
    inserted = database.add_document(
        boundary_round2_user.curriculum_document(), user_drafts
    )
    inserted += database.add_document(
        english_routes_round2b.curriculum_document(), english_drafts
    )
    assert inserted == 18
    assert database.stats()["patterns"] == 0


def test_train_router_records_foundation_weight(tmp_path: Path) -> None:
    database = PatternDatabase(tmp_path / "patterns.db")
    drafts = [
        _draft("Pythonで機能を実装してください", "build", ["sequence"]),
        _draft("設計のリスクを検証してください", "verify", ["verification"]),
    ]
    database.add_document(_document(), drafts)
    for candidate in database.list_candidates():
        database.review(
            ReviewDecision(candidate["id"], "approve", 5)
        )

    model_path = tmp_path / "router.json"
    train_router(
        database, model_path, epochs=4, dimension=128, foundation_weight=2.0
    )
    payload = json.loads(model_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["foundation_weight"] == 2.0


def test_predict_cli_does_not_require_database(
    tmp_path: Path,
) -> None:
    model = RouterModel(
        labels=["build", "verify"],
        dimension=32,
        weights={"build": {}, "verify": {}},
        bias={"build": 1.0, "verify": 0.0},
        operator_priors={"build": {"sequence": 1.0}},
        metadata={},
    )
    model_path = tmp_path / "model.json"
    model.save(model_path)
    unusable_database_path = tmp_path / "missing" / "deeper" / "db.sqlite"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pattern_learning",
            "--db",
            str(unusable_database_path),
            "predict",
            "実装してください",
            "--model",
            str(model_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert json.loads(completed.stdout)["route"] == "build"
    assert not unusable_database_path.exists()
