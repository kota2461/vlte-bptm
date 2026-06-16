import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from .database import PatternDatabase
from .deployment import (
    DEFAULT_FOUNDATION_FIXTURE,
    DEFAULT_REGISTRY,
    DEFAULT_REGRESSION_FIXTURE,
    promote,
    run_deployment_gate,
)
from .extractor import extract_patterns
from .models import OPERATORS, ROUTES, ReviewDecision
from .trainer import RouterModel, train_router
from .wikipedia import WikipediaClient
from semantic_routing import AccumulationReviewStore, PLMReviewStore


STATIC_DIR = Path(__file__).parent / "static"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLM_BENCHMARK = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "pattern_language_benchmark_v1.json"
)
DEFAULT_PLM_REVIEWS = (
    PROJECT_ROOT / "data" / "plm_benchmark_reviews_v1.json"
)
DEFAULT_ACCUMULATION_CAMPAIGN = (
    PROJECT_ROOT / "data" / "conversation_accumulation_v1.json"
)
DEFAULT_ACCUMULATION_REVIEWS = (
    PROJECT_ROOT / "data" / "conversation_accumulation_reviews_v1.json"
)


class PatternLabApplication:
    def __init__(
        self,
        database_path: str | Path,
        model_path: str | Path,
        regression_fixture: str | Path = DEFAULT_REGRESSION_FIXTURE,
        foundation_fixture: str | Path = DEFAULT_FOUNDATION_FIXTURE,
        registry_path: str | Path = DEFAULT_REGISTRY,
        plm_benchmark_path: str | Path = DEFAULT_PLM_BENCHMARK,
        plm_review_path: str | Path = DEFAULT_PLM_REVIEWS,
        accumulation_campaign_path: str | Path = (
            DEFAULT_ACCUMULATION_CAMPAIGN
        ),
        accumulation_review_path: str | Path = (
            DEFAULT_ACCUMULATION_REVIEWS
        ),
    ) -> None:
        self.database = PatternDatabase(database_path)
        self.model_path = Path(model_path)
        self.regression_fixture = Path(regression_fixture)
        self.foundation_fixture = Path(foundation_fixture)
        self.registry_path = Path(registry_path)
        self.plm_reviews = PLMReviewStore(
            plm_benchmark_path,
            plm_review_path,
        )
        self.accumulation_campaign_path = Path(accumulation_campaign_path)
        self.accumulation_review_path = Path(accumulation_review_path)
        self._accumulation_reviews: AccumulationReviewStore | None = None

    @property
    def accumulation_reviews(self) -> AccumulationReviewStore:
        # Lazy so the server still starts if the campaign file is absent.
        if self._accumulation_reviews is None:
            self._accumulation_reviews = AccumulationReviewStore(
                self.accumulation_campaign_path,
                self.accumulation_review_path,
            )
        return self._accumulation_reviews

    @property
    def candidate_path(self) -> Path:
        return self.model_path.with_name(
            self.model_path.stem + "_candidate.json"
        )

    def _run_gate(self) -> Dict[str, Any]:
        return run_deployment_gate(
            self.candidate_path,
            regression_fixture=self.regression_fixture,
            foundation_fixture=self.foundation_fixture,
            registry_path=self.registry_path,
            deployed_path=self.model_path,
            database_path=self.database.path,
        )

    def get(self, path: str, query: Dict[str, list[str]]) -> Dict[str, Any]:
        if path == "/api/config":
            return {"routes": list(ROUTES), "operators": list(OPERATORS)}
        if path == "/api/stats":
            return self.database.stats()
        if path == "/api/plm/config":
            return {
                "statuses": ["pending", "approved", "rejected", "all"],
                "splits": [
                    "visible",
                    "train",
                    "validation",
                    "sealed",
                    "all",
                ],
            }
        if path == "/api/plm/stats":
            return self.plm_reviews.stats()
        if path == "/api/plm/cases":
            status = query.get("status", ["pending"])[0]
            split = query.get("split", ["visible"])[0]
            return {
                "items": self.plm_reviews.list_cases(
                    status=status,
                    split=split,
                )
            }
        if path == "/api/accumulation/config":
            return {
                "statuses": ["pending", "approved", "rejected", "all"],
                "categories": [
                    "all",
                    *sorted(self.accumulation_reviews.campaign
                            .required_categories),
                ],
            }
        if path == "/api/accumulation/stats":
            return self.accumulation_reviews.stats()
        if path == "/api/accumulation/cases":
            status = query.get("status", ["pending"])[0]
            category = query.get("category", ["all"])[0]
            return {
                "items": self.accumulation_reviews.list_cases(
                    status=status,
                    category=category,
                )
            }
        if path == "/api/candidates":
            status = query.get("status", ["pending"])[0]
            limit = int(query.get("limit", ["50"])[0])
            offset = int(query.get("offset", ["0"])[0])
            return {
                "items": self.database.list_candidates(
                    status=status,
                    limit=limit,
                    offset=offset,
                )
            }
        if path == "/api/patterns":
            return {"items": self.database.training_examples()}
        if path == "/api/health":
            return {"ok": True}
        raise KeyError(path)

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if path == "/api/reviews":
            # Absent operators / thought_form must stay None so the review
            # keeps the candidate's suggested values instead of erasing them.
            operators = payload.get("operators")
            thought_form = payload.get("thought_form")
            decision = ReviewDecision(
                candidate_id=int(payload["candidate_id"]),
                verdict=str(payload["verdict"]),
                rating=int(payload.get("rating", 3)),
                route=payload.get("route") or None,
                operators=list(operators) if operators is not None else None,
                thought_form=(
                    dict(thought_form) if thought_form is not None else None
                ),
                notes=str(payload.get("notes", "")),
            )
            return {"candidate": self.database.review(decision)}

        if path == "/api/plm/reviews":
            case = self.plm_reviews.review(
                case_id=str(payload["case_id"]),
                verdict=str(payload["verdict"]),
                expected=payload["expected"],
                notes=str(payload.get("notes", "")),
            )
            return {"case": case}

        if path == "/api/accumulation/reviews":
            case = self.accumulation_reviews.review(
                case_id=str(payload["case_id"]),
                verdict=str(payload["verdict"]),
                expected=payload["expected"],
                notes=str(payload.get("notes", "")),
            )
            return {"case": case}

        if path == "/api/candidates/manual":
            text = str(payload["input_text"]).strip()
            if not text:
                raise ValueError("input_text is required")
            route = str(payload.get("route", "respond"))
            operators = list(payload.get("operators", ["definition"]))
            thought_form = dict(
                payload.get(
                    "thought_form",
                    {
                        "facts": [text],
                        "goals": [],
                        "constraints": [],
                        "uncertainty": [],
                        "operation": operators[0],
                        "candidates": [],
                    },
                )
            )
            candidate_id = self.database.add_manual_candidate(
                text=text,
                route=route,
                operators=operators,
                thought_form=thought_form,
            )
            return {"candidate": self.database.get_candidate(candidate_id)}

        if path == "/api/import/wikipedia":
            user_agent = str(payload.get("user_agent", "")).strip()
            titles = [
                title.strip()
                for title in payload.get("titles", [])
                if str(title).strip()
            ]
            category = str(payload.get("category", "")).strip()
            article_limit = max(1, min(int(payload.get("article_limit", 10)), 50))
            patterns_per_article = max(
                1, min(int(payload.get("patterns_per_article", 8)), 30)
            )
            client = WikipediaClient(user_agent=user_agent)
            if category:
                titles.extend(
                    client.category_titles(category, limit=article_limit)
                )
            titles = list(dict.fromkeys(titles))[:article_limit]
            if not titles:
                raise ValueError("at least one title or category is required")

            inserted = 0
            documents = client.fetch_titles(titles)
            for document in documents:
                drafts = extract_patterns(
                    document, limit=patterns_per_article
                )
                inserted += self.database.add_document(document, drafts)
            return {
                "articles": len(documents),
                "candidates_inserted": inserted,
            }

        if path == "/api/train":
            # v0.2.2: training never deploys. The gate runs for visibility;
            # promotion is a separate explicit human action (/api/promote).
            result = train_router(
                self.database,
                self.candidate_path,
                epochs=int(payload.get("epochs", 24)),
                dimension=int(payload.get("dimension", 2048)),
                foundation_weight=float(
                    payload.get("foundation_weight", 1.0)
                ),
            )
            gate = self._run_gate()
            result["gate"] = gate
            result["promoted"] = False
            result["note"] = (
                "candidate trained; promotion requires the explicit "
                "promote action"
            )
            return result

        if path == "/api/promote":
            if not self.candidate_path.exists():
                raise ValueError("train a candidate model first")
            gate = self._run_gate()
            if gate["passed"]:
                promote(self.candidate_path, self.model_path, gate)
                gate["promoted_to"] = str(self.model_path.resolve())
            gate["promoted"] = gate["passed"]
            return gate

        if path == "/api/predict":
            if not self.model_path.exists():
                raise ValueError("train a router model first")
            model = RouterModel.load(self.model_path)
            return model.predict(str(payload.get("input_text", ""))).as_dict()

        raise KeyError(path)


class PatternLabHandler(BaseHTTPRequestHandler):
    application: PatternLabApplication

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json_response(
        self,
        payload: Dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, error: Exception) -> None:
        if isinstance(error, KeyError):
            status = HTTPStatus.NOT_FOUND
        elif isinstance(error, (ValueError, json.JSONDecodeError)):
            status = HTTPStatus.BAD_REQUEST
        else:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
        self._json_response(
            {"error": str(error) or error.__class__.__name__},
            status=status,
        )

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path == "/" else path.lstrip("/")
        target = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        content_type, _encoding = mimetypes.guess_type(target.name)
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type",
            (content_type or "application/octet-stream")
            + ("; charset=utf-8" if target.suffix in {".html", ".css", ".js"} else ""),
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            self._serve_static(parsed.path)
            return
        try:
            self._json_response(
                self.application.get(parsed.path, parse_qs(parsed.query))
            )
        except Exception as error:
            self._error(error)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > 1_000_000:
                raise ValueError("request body is too large")
            raw = self.rfile.read(content_length)
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            self._json_response(self.application.post(parsed.path, payload))
        except Exception as error:
            self._error(error)


def run_server(
    database_path: str | Path,
    model_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    application = PatternLabApplication(database_path, model_path)
    handler = type(
        "BoundPatternLabHandler",
        (PatternLabHandler,),
        {"application": application},
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Pattern Lab: http://{host}:{port}")
    print(f"Database: {Path(database_path).resolve()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
