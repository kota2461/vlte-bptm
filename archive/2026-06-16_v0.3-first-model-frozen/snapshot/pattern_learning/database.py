import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .models import OPERATORS, ROUTES, PatternDraft, ReviewDecision, SourceDocument


SCHEMA_VERSION = "pattern-db.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _decode(value: Optional[str], fallback: Any) -> Any:
    return json.loads(value) if value else fallback


class PatternDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    license_name TEXT NOT NULL,
                    attribution TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    UNIQUE(source_kind, url, revision_id)
                );

                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL REFERENCES sources(id),
                    input_text TEXT NOT NULL,
                    suggested_route TEXT NOT NULL,
                    suggested_operators_json TEXT NOT NULL,
                    thought_form_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending', 'approved', 'rejected')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(source_id, input_text)
                );

                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
                    verdict TEXT NOT NULL CHECK(verdict IN ('approve', 'reject')),
                    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                    route TEXT,
                    operators_json TEXT,
                    thought_form_json TEXT,
                    notes TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT NOT NULL UNIQUE,
                    candidate_id INTEGER NOT NULL UNIQUE
                        REFERENCES candidates(id),
                    review_id INTEGER NOT NULL REFERENCES reviews(id),
                    input_text TEXT NOT NULL,
                    route TEXT NOT NULL,
                    operators_json TEXT NOT NULL,
                    thought_form_json TEXT NOT NULL,
                    quality_score INTEGER NOT NULL,
                    source_title TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    source_revision_id TEXT NOT NULL,
                    source_license TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS training_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_path TEXT NOT NULL,
                    sample_count INTEGER NOT NULL,
                    labels_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_candidates_status
                    ON candidates(status, id);
                CREATE INDEX IF NOT EXISTS idx_patterns_route
                    ON patterns(route, id);
                """
            )
            connection.execute(
                """
                INSERT INTO metadata(key, value) VALUES('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (SCHEMA_VERSION,),
            )

    def add_document(
        self,
        document: SourceDocument,
        drafts: List[PatternDraft],
    ) -> int:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO sources(
                    source_kind, title, url, revision_id, fetched_at,
                    license_name, attribution, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.source_kind,
                    document.title,
                    document.url,
                    document.revision_id,
                    document.fetched_at,
                    document.license_name,
                    document.attribution,
                    _json(document.metadata),
                ),
            )
            source = connection.execute(
                """
                SELECT id FROM sources
                WHERE source_kind = ? AND url = ? AND revision_id = ?
                """,
                (
                    document.source_kind,
                    document.url,
                    document.revision_id,
                ),
            ).fetchone()
            if source is None:
                raise RuntimeError("failed to create source")
            source_id = int(source["id"])
            timestamp = _now()
            inserted = 0
            for draft in drafts:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO candidates(
                        source_id, input_text, suggested_route,
                        suggested_operators_json, thought_form_json,
                        confidence, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_id,
                        draft.input_text,
                        draft.suggested_route,
                        _json(draft.suggested_operators),
                        _json(draft.thought_form),
                        draft.confidence,
                        timestamp,
                        timestamp,
                    ),
                )
                inserted += cursor.rowcount
            return inserted

    def add_manual_candidate(
        self,
        text: str,
        route: str,
        operators: List[str],
        thought_form: Dict[str, Any],
        confidence: float = 1.0,
    ) -> int:
        if not text.strip():
            raise ValueError("manual candidate text is required")
        if route not in ROUTES:
            raise ValueError(f"unknown route: {route}")
        unknown = sorted(set(operators) - set(OPERATORS))
        if unknown:
            raise ValueError(f"unknown operators: {', '.join(unknown)}")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        document = SourceDocument(
            source_kind="manual",
            title=f"Manual entry {digest}",
            url=f"manual://{digest}",
            revision_id="1",
            fetched_at=_now(),
            license_name="user-provided",
            attribution="Local user",
            text=text,
        )
        draft = PatternDraft(
            input_text=text,
            suggested_route=route,
            suggested_operators=operators,
            thought_form=thought_form,
            confidence=confidence,
        )
        self.add_document(document, [draft])
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT c.id
                FROM candidates c
                JOIN sources s ON s.id = c.source_id
                WHERE s.url = ? AND c.input_text = ?
                """,
                (document.url, text),
            ).fetchone()
            if row is None:
                raise RuntimeError("failed to create manual candidate")
            return int(row["id"])

    def list_candidates(
        self,
        status: str = "pending",
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if status not in {"pending", "approved", "rejected", "all"}:
            raise ValueError("invalid candidate status")
        where = "" if status == "all" else "WHERE c.status = ?"
        params: list[Any] = [] if status == "all" else [status]
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT c.*, s.source_kind, s.title AS source_title,
                       s.url AS source_url, s.revision_id,
                       s.license_name, s.attribution
                FROM candidates c
                JOIN sources s ON s.id = c.source_id
                {where}
                ORDER BY c.id ASC
                LIMIT ? OFFSET ?
                """,
                params,
            ).fetchall()
        return [self._candidate_dict(row) for row in rows]

    def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT c.*, s.source_kind, s.title AS source_title,
                       s.url AS source_url, s.revision_id,
                       s.license_name, s.attribution
                FROM candidates c
                JOIN sources s ON s.id = c.source_id
                WHERE c.id = ?
                """,
                (candidate_id,),
            ).fetchone()
        return self._candidate_dict(row) if row else None

    @staticmethod
    def _candidate_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "input_text": row["input_text"],
            "suggested_route": row["suggested_route"],
            "suggested_operators": _decode(
                row["suggested_operators_json"], []
            ),
            "thought_form": _decode(row["thought_form_json"], {}),
            "confidence": row["confidence"],
            "status": row["status"],
            "created_at": row["created_at"],
            "source": {
                "kind": row["source_kind"],
                "title": row["source_title"],
                "url": row["source_url"],
                "revision_id": row["revision_id"],
                "license": row["license_name"],
                "attribution": row["attribution"],
            },
        }

    def review(self, decision: ReviewDecision) -> Dict[str, Any]:
        decision.validate()
        with self.connect() as connection:
            candidate = connection.execute(
                """
                SELECT c.*, s.title AS source_title, s.url AS source_url,
                       s.revision_id, s.license_name
                FROM candidates c
                JOIN sources s ON s.id = c.source_id
                WHERE c.id = ?
                """,
                (decision.candidate_id,),
            ).fetchone()
            if candidate is None:
                raise KeyError(f"candidate {decision.candidate_id} not found")

            route = decision.route or candidate["suggested_route"]
            operators = (
                decision.operators
                if decision.operators is not None
                else _decode(candidate["suggested_operators_json"], [])
            )
            thought_form = (
                decision.thought_form
                if decision.thought_form is not None
                else _decode(candidate["thought_form_json"], {})
            )
            timestamp = _now()
            cursor = connection.execute(
                """
                INSERT INTO reviews(
                    candidate_id, verdict, rating, route, operators_json,
                    thought_form_json, notes, reviewed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.candidate_id,
                    decision.verdict,
                    decision.rating,
                    route,
                    _json(operators),
                    _json(thought_form),
                    decision.notes.strip(),
                    timestamp,
                ),
            )
            review_id = int(cursor.lastrowid)
            status = (
                "approved" if decision.verdict == "approve" else "rejected"
            )
            connection.execute(
                """
                UPDATE candidates SET status = ?, updated_at = ? WHERE id = ?
                """,
                (status, timestamp, decision.candidate_id),
            )

            if decision.verdict == "approve":
                pattern_key = "\n".join(
                    [
                        str(decision.candidate_id),
                        candidate["input_text"],
                        route,
                        _json(sorted(operators)),
                    ]
                )
                pattern_id = (
                    "pat_" + hashlib.sha256(
                        pattern_key.encode("utf-8")
                    ).hexdigest()[:20]
                )
                connection.execute(
                    """
                    INSERT INTO patterns(
                        pattern_id, candidate_id, review_id, input_text,
                        route, operators_json, thought_form_json,
                        quality_score, source_title, source_url,
                        source_revision_id, source_license,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(candidate_id) DO UPDATE SET
                        pattern_id = excluded.pattern_id,
                        review_id = excluded.review_id,
                        route = excluded.route,
                        operators_json = excluded.operators_json,
                        thought_form_json = excluded.thought_form_json,
                        quality_score = excluded.quality_score,
                        updated_at = excluded.updated_at
                    """,
                    (
                        pattern_id,
                        decision.candidate_id,
                        review_id,
                        candidate["input_text"],
                        route,
                        _json(operators),
                        _json(thought_form),
                        decision.rating,
                        candidate["source_title"],
                        candidate["source_url"],
                        candidate["revision_id"],
                        candidate["license_name"],
                        timestamp,
                        timestamp,
                    ),
                )
            else:
                connection.execute(
                    "DELETE FROM patterns WHERE candidate_id = ?",
                    (decision.candidate_id,),
                )

        result = self.get_candidate(decision.candidate_id)
        if result is None:
            raise RuntimeError("reviewed candidate disappeared")
        return result

    def training_examples(self) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT pattern_id, input_text, route, operators_json,
                       thought_form_json, quality_score, source_title,
                       source_url, source_revision_id, source_license
                FROM patterns
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            {
                "pattern_id": row["pattern_id"],
                "input_text": row["input_text"],
                "route": row["route"],
                "operators": _decode(row["operators_json"], []),
                "thought_form": _decode(row["thought_form_json"], {}),
                "quality_score": row["quality_score"],
                "source": {
                    "title": row["source_title"],
                    "url": row["source_url"],
                    "revision_id": row["source_revision_id"],
                    "license": row["source_license"],
                },
            }
            for row in rows
        ]

    def stats(self) -> Dict[str, Any]:
        with self.connect() as connection:
            statuses = {
                row["status"]: row["count"]
                for row in connection.execute(
                    """
                    SELECT status, COUNT(*) AS count
                    FROM candidates GROUP BY status
                    """
                )
            }
            routes = {
                row["route"]: row["count"]
                for row in connection.execute(
                    """
                    SELECT route, COUNT(*) AS count
                    FROM patterns GROUP BY route ORDER BY route
                    """
                )
            }
            source_count = connection.execute(
                "SELECT COUNT(*) AS count FROM sources"
            ).fetchone()["count"]
            run = connection.execute(
                """
                SELECT * FROM training_runs ORDER BY id DESC LIMIT 1
                """
            ).fetchone()
        return {
            "schema_version": SCHEMA_VERSION,
            "candidates": {
                "pending": statuses.get("pending", 0),
                "approved": statuses.get("approved", 0),
                "rejected": statuses.get("rejected", 0),
                "total": sum(statuses.values()),
            },
            "patterns": sum(routes.values()),
            "routes": routes,
            "sources": source_count,
            "latest_training_run": (
                {
                    "model_path": run["model_path"],
                    "sample_count": run["sample_count"],
                    "metrics": _decode(run["metrics_json"], {}),
                    "created_at": run["created_at"],
                }
                if run
                else None
            ),
        }

    def record_training_run(
        self,
        model_path: str,
        sample_count: int,
        labels: List[str],
        metrics: Dict[str, Any],
        parameters: Dict[str, Any],
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO training_runs(
                    model_path, sample_count, labels_json,
                    metrics_json, parameters_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    model_path,
                    sample_count,
                    _json(labels),
                    _json(metrics),
                    _json(parameters),
                    _now(),
                ),
            )
