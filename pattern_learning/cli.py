import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from . import (
    boundary_curriculum,
    boundary_curriculum_v2,
    boundary_curriculum_v3,
    language_curriculum,
    math_curriculum,
)
from .database import PatternDatabase
from .deployment import (
    DEFAULT_CANDIDATE,
    DEFAULT_FOUNDATION_FIXTURE,
    DEFAULT_HISTORY_DIR,
    DEFAULT_REGISTRY,
    DEFAULT_REGRESSION_FIXTURE,
    acknowledge_improvement_regression,
    promote,
    rollback,
    run_deployment_gate,
)
from .extractor import extract_patterns
from .models import PatternDraft, SourceDocument
from .server import run_server
from .trainer import RouterModel, train_router
from .wikipedia import WikipediaClient


DEFAULT_DATABASE = Path("data/pattern_lab.db")
DEFAULT_MODEL = Path("build/pattern_router_model.json")

DEMO_ITEMS = (
    ("この機能をPythonで実装してください", "build", ["sequence"]),
    ("設計のリスクと根拠を検証してください", "verify", ["verification"]),
    ("この文章を短く要約してください", "summarize", ["decomposition"]),
    ("不足している条件を質問してください", "clarify", ["condition"]),
    ("新しい代替案をいくつか検討してください", "explore", ["comparison"]),
    ("こんにちは、今日はいい天気ですね", "respond", ["definition"]),
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Human-reviewed Pattern DB and router training lab"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DATABASE,
        help="SQLite Pattern DB path",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="initialize the Pattern DB")
    subparsers.add_parser(
        "seed-demo",
        help="add six pending examples for UI evaluation",
    )
    subparsers.add_parser(
        "seed-math",
        help=(
            "add the math thinking-pattern curriculum "
            "(number sense to high school) as pending candidates"
        ),
    )
    subparsers.add_parser(
        "seed-language",
        help=(
            "add the Japanese/English language-basics curriculum "
            "(greetings and sentence understanding) as pending candidates"
        ),
    )
    subparsers.add_parser(
        "seed-boundaries",
        help=(
            "add curated route-boundary contrast pairs "
            "as pending candidates"
        ),
    )
    subparsers.add_parser(
        "seed-boundaries-v2",
        help=(
            "add original specification-derived boundary contrast pairs "
            "as pending candidates"
        ),
    )
    subparsers.add_parser(
        "seed-boundaries-v3",
        help=(
            "add revision-3 boundary contrast pairs targeting the weak "
            "build/verify-vs-respond and clarify-vs-verify boundaries"
        ),
    )

    serve = subparsers.add_parser("serve", help="start the evaluation UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--model", type=Path, default=DEFAULT_MODEL)

    wiki = subparsers.add_parser(
        "import-wikipedia",
        help="fetch Japanese Wikipedia pages into the review queue",
    )
    wiki.add_argument("--title", action="append", default=[])
    wiki.add_argument("--category")
    wiki.add_argument("--article-limit", type=int, default=10)
    wiki.add_argument("--patterns-per-article", type=int, default=8)
    wiki.add_argument(
        "--user-agent",
        required=True,
        help="descriptive User-Agent including an email or project URL",
    )

    train = subparsers.add_parser(
        "train",
        help=(
            "train from approved Pattern DB entries into a CANDIDATE "
            "model; use 'promote' to gate and deploy it"
        ),
    )
    train.add_argument("--output", type=Path, default=DEFAULT_CANDIDATE)
    train.add_argument("--epochs", type=int, default=24)
    train.add_argument("--dimension", type=int, default=2048)
    train.add_argument(
        "--foundation-weight",
        type=float,
        default=1.0,
        help=(
            "update-step multiplier for tier-0 foundation patterns "
            "(default 1.0 = off; see PATTERN_ROUTER_v0_2_design.md)"
        ),
    )

    promote_parser = subparsers.add_parser(
        "promote",
        help=(
            "run the deployment gate on a candidate model and, if it "
            "passes, copy it over the deployed model"
        ),
    )
    promote_parser.add_argument(
        "--candidate", type=Path, default=DEFAULT_CANDIDATE
    )
    promote_parser.add_argument(
        "--deployed", type=Path, default=DEFAULT_MODEL
    )
    promote_parser.add_argument(
        "--regression-fixture",
        type=Path,
        default=DEFAULT_REGRESSION_FIXTURE,
    )
    promote_parser.add_argument(
        "--foundation-fixture",
        type=Path,
        default=DEFAULT_FOUNDATION_FIXTURE,
    )
    promote_parser.add_argument(
        "--registry", type=Path, default=DEFAULT_REGISTRY
    )
    promote_parser.add_argument(
        "--ack-improvement-regression",
        metavar="REASON",
        help=(
            "acknowledge only an improvement-check failure; requires "
            "same-fixture sealed evidence for candidate and deployed models"
        ),
    )
    promote_parser.add_argument(
        "--candidate-sealed-result",
        type=Path,
        help="sealed evaluation JSON for the candidate model",
    )
    promote_parser.add_argument(
        "--deployed-sealed-result",
        type=Path,
        help="sealed evaluation JSON for the deployed model",
    )
    promote_parser.add_argument(
        "--ack-actor",
        default="human-operator",
        help="operator recorded in the improvement acknowledgment",
    )

    rollback_parser = subparsers.add_parser(
        "rollback",
        help=(
            "quarantine the deployed model and restore the previous "
            "approved one from build/model_history"
        ),
    )
    rollback_parser.add_argument(
        "--deployed", type=Path, default=DEFAULT_MODEL
    )
    rollback_parser.add_argument(
        "--history-dir", type=Path, default=DEFAULT_HISTORY_DIR
    )
    rollback_parser.add_argument(
        "--reason",
        required=True,
        help="why the deployed model is being rolled back (recorded)",
    )

    predict = subparsers.add_parser(
        "predict",
        help="run an explicitly trained router model",
    )
    predict.add_argument("text")
    predict.add_argument("--model", type=Path, default=DEFAULT_MODEL)

    export = subparsers.add_parser(
        "export",
        help="export approved patterns as JSONL",
    )
    export.add_argument("--output", type=Path, required=True)
    return parser


def _demo_document() -> tuple[SourceDocument, List[PatternDraft]]:
    document = SourceDocument(
        source_kind="demo",
        title="Pattern Lab demo candidates",
        url="demo://router-patterns-v1",
        revision_id="1",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        license_name="project-demo",
        attribution="Thought State Register",
        text="",
    )
    drafts = [
        PatternDraft(
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
            confidence=0.9,
        )
        for text, route, operators in DEMO_ITEMS
    ]
    return document, drafts


def main(argv: List[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "predict":
        print(
            json.dumps(
                RouterModel.load(args.model).predict(args.text).as_dict(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "promote":
        report = run_deployment_gate(
            args.candidate,
            regression_fixture=args.regression_fixture,
            foundation_fixture=args.foundation_fixture,
            registry_path=args.registry,
            deployed_path=args.deployed,
            database_path=args.db,
        )
        if args.ack_improvement_regression:
            if (
                args.candidate_sealed_result is None
                or args.deployed_sealed_result is None
            ):
                raise ValueError(
                    "improvement acknowledgment requires "
                    "--candidate-sealed-result and "
                    "--deployed-sealed-result"
                )
            acknowledge_improvement_regression(
                report,
                reason=args.ack_improvement_regression,
                candidate_sealed_result=args.candidate_sealed_result,
                deployed_sealed_result=args.deployed_sealed_result,
                registry_path=args.registry,
                actor=args.ack_actor,
            )
        if report["passed"]:
            deployed = promote(args.candidate, args.deployed, report)
            report["promoted_to"] = str(deployed.resolve())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1

    if args.command == "rollback":
        print(
            json.dumps(
                rollback(
                    deployed_path=args.deployed,
                    history_dir=args.history_dir,
                    reason=args.reason,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    database = PatternDatabase(args.db)

    if args.command == "init":
        print(f"initialized: {args.db.resolve()}")
        return 0

    if args.command == "seed-demo":
        document, drafts = _demo_document()
        inserted = database.add_document(document, drafts)
        print(f"inserted {inserted} pending candidates")
        return 0

    if args.command == "seed-math":
        inserted = database.add_document(
            math_curriculum.curriculum_document(),
            math_curriculum.curriculum_drafts(),
        )
        print(f"inserted {inserted} pending math candidates")
        return 0

    if args.command == "seed-language":
        inserted = database.add_document(
            language_curriculum.curriculum_document(),
            language_curriculum.curriculum_drafts(),
        )
        print(f"inserted {inserted} pending language candidates")
        return 0

    if args.command == "seed-boundaries":
        inserted = database.add_document(
            boundary_curriculum.curriculum_document(),
            boundary_curriculum.curriculum_drafts(),
        )
        print(f"inserted {inserted} pending boundary candidates")
        return 0

    if args.command == "seed-boundaries-v2":
        inserted = database.add_document(
            boundary_curriculum_v2.curriculum_document(),
            boundary_curriculum_v2.curriculum_drafts(),
        )
        print(f"inserted {inserted} pending boundary v2 candidates")
        return 0

    if args.command == "seed-boundaries-v3":
        inserted = database.add_document(
            boundary_curriculum_v3.curriculum_document(),
            boundary_curriculum_v3.curriculum_drafts(),
        )
        print(f"inserted {inserted} pending boundary v3 candidates")
        return 0

    if args.command == "serve":
        run_server(args.db, args.model, args.host, args.port)
        return 0

    if args.command == "import-wikipedia":
        client = WikipediaClient(args.user_agent)
        article_limit = max(1, min(args.article_limit, 50))
        titles = list(args.title)
        if args.category:
            titles.extend(
                client.category_titles(args.category, limit=article_limit)
            )
        titles = list(dict.fromkeys(titles))[:article_limit]
        if not titles:
            raise SystemExit("--title or --category is required")
        inserted = 0
        documents = client.fetch_titles(titles)
        for document in documents:
            inserted += database.add_document(
                document,
                extract_patterns(
                    document,
                    limit=args.patterns_per_article,
                ),
            )
        print(
            json.dumps(
                {
                    "articles": len(documents),
                    "candidates_inserted": inserted,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "train":
        result = train_router(
            database,
            args.output,
            epochs=args.epochs,
            dimension=args.dimension,
            foundation_weight=args.foundation_weight,
        )
        result["note"] = (
            "candidate model only; run 'promote' to gate and deploy"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "export":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            for example in database.training_examples():
                handle.write(json.dumps(example, ensure_ascii=False) + "\n")
        print(f"exported: {args.output.resolve()}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
