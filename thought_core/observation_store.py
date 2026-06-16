import json
import os
import sqlite3
import stat
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .bits import THOUGHT_CODE_WIDTH
from .encoder import THRESHOLD_PROFILES
from .observation import OBSERVATION_SCHEMA_VERSION
from .order_builder import MODE_INSTRUCTIONS
from .units import DEFAULT_UNITS


PRIVACY_POLICY_SCHEMA_VERSION = "observation-privacy-policy.v1"
OBSERVATION_STORE_SCHEMA_VERSION = "vlte-bptm.observation-store.v1"
OBSERVATION_STORE_EXPORT_SCHEMA_VERSION = (
    "vlte-bptm.observation-store-export.v1"
)
DEFAULT_PRIVACY_POLICY_PATH = (
    Path(__file__).resolve().parent / "config" / "observation_privacy.json"
)
_REPORT_FIELDS = {
    "schema_version",
    "pipeline_version",
    "sample_count",
    "privacy",
    "aggregates",
}
_ALLOWED_AGGREGATE_CELLS = {
    "active_bit_frequency": {
        str(index) for index in range(THOUGHT_CODE_WIDTH)
    },
    "active_bit_count_distribution": {
        str(count) for count in range(THOUGHT_CODE_WIDTH + 1)
    },
    "selected_unit_frequency": {
        unit.unit_id for unit in DEFAULT_UNITS
    },
    "selected_unit_count_distribution": {
        str(count) for count in range(len(DEFAULT_UNITS) + 1)
    },
    "threshold_profile_frequency": set(THRESHOLD_PROFILES),
    "llm_order_mode_frequency": set(MODE_INSTRUCTIONS),
}
_EXCLUDED_AGGREGATES = {"selected_unit_combination_frequency"}


@dataclass(frozen=True)
class ObservationPrivacyPolicy:
    storage_schema_version: str
    storage: str
    opt_in_only: bool
    local_only: bool
    bucket_hours: int
    minimum_cohort_size: int
    minimum_cell_count: int
    retention_days: int
    immutable_buckets: bool
    automatic_purge: bool
    cohort_size_lower_bounds: Tuple[int, ...]
    persisted_aggregates: Tuple[str, ...]
    excluded_aggregates: Tuple[str, ...]
    forbidden_fields: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PRIVACY_POLICY_SCHEMA_VERSION,
            "storage_schema_version": self.storage_schema_version,
            "storage": self.storage,
            "opt_in_only": self.opt_in_only,
            "local_only": self.local_only,
            "bucket_hours": self.bucket_hours,
            "minimum_cohort_size": self.minimum_cohort_size,
            "minimum_cell_count": self.minimum_cell_count,
            "retention_days": self.retention_days,
            "immutable_buckets": self.immutable_buckets,
            "automatic_purge": self.automatic_purge,
            "cohort_size_lower_bounds": list(
                self.cohort_size_lower_bounds
            ),
            "persisted_aggregates": list(self.persisted_aggregates),
            "excluded_aggregates": list(self.excluded_aggregates),
            "forbidden_fields": list(self.forbidden_fields),
        }


def _require_positive_int(payload: Mapping[str, Any], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _require_string_list(
    payload: Mapping[str, Any],
    field: str,
) -> Tuple[str, ...]:
    value = payload.get(field)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{field} must contain unique non-empty strings")
    return tuple(value)


def load_observation_privacy_policy(
    path: Optional[Path] = None,
) -> ObservationPrivacyPolicy:
    config_path = path or DEFAULT_PRIVACY_POLICY_PATH
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("observation privacy policy must be an object")
    if payload.get("schema_version") != PRIVACY_POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported observation privacy policy schema")
    if (
        payload.get("storage_schema_version")
        != OBSERVATION_STORE_SCHEMA_VERSION
    ):
        raise ValueError("unsupported observation store schema")
    if payload.get("storage") != "sqlite":
        raise ValueError("observation storage must be sqlite")
    for field in (
        "opt_in_only",
        "local_only",
        "immutable_buckets",
        "automatic_purge",
    ):
        if payload.get(field) is not True:
            raise ValueError(f"{field} must be true")

    bucket_hours = _require_positive_int(payload, "bucket_hours")
    if bucket_hours != 24:
        raise ValueError("bucket_hours must remain fixed at 24")
    minimum_cohort_size = _require_positive_int(
        payload,
        "minimum_cohort_size",
    )
    minimum_cell_count = _require_positive_int(
        payload,
        "minimum_cell_count",
    )
    if minimum_cell_count > minimum_cohort_size:
        raise ValueError(
            "minimum_cell_count cannot exceed minimum_cohort_size"
        )
    retention_days = _require_positive_int(payload, "retention_days")
    lower_bounds = payload.get("cohort_size_lower_bounds")
    if (
        not isinstance(lower_bounds, list)
        or not lower_bounds
        or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            for value in lower_bounds
        )
        or lower_bounds != sorted(set(lower_bounds))
        or lower_bounds[0] != minimum_cohort_size
    ):
        raise ValueError(
            "cohort_size_lower_bounds must be sorted, unique, and start "
            "at minimum_cohort_size"
        )

    persisted = _require_string_list(payload, "persisted_aggregates")
    excluded = _require_string_list(payload, "excluded_aggregates")
    if set(persisted) & set(excluded):
        raise ValueError("persisted and excluded aggregates must be disjoint")
    if set(persisted) != set(_ALLOWED_AGGREGATE_CELLS):
        raise ValueError("persisted_aggregates do not match the fixed contract")
    if set(excluded) != _EXCLUDED_AGGREGATES:
        raise ValueError("excluded_aggregates do not match the fixed contract")

    return ObservationPrivacyPolicy(
        storage_schema_version=payload["storage_schema_version"],
        storage=payload["storage"],
        opt_in_only=payload["opt_in_only"],
        local_only=payload["local_only"],
        bucket_hours=bucket_hours,
        minimum_cohort_size=minimum_cohort_size,
        minimum_cell_count=minimum_cell_count,
        retention_days=retention_days,
        immutable_buckets=payload["immutable_buckets"],
        automatic_purge=payload["automatic_purge"],
        cohort_size_lower_bounds=tuple(lower_bounds),
        persisted_aggregates=persisted,
        excluded_aggregates=excluded,
        forbidden_fields=_require_string_list(
            payload,
            "forbidden_fields",
        ),
    )


DEFAULT_OBSERVATION_PRIVACY_POLICY = load_observation_privacy_policy()


def _utc(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("observation time must include timezone information")
    return value.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cohort_size_band(
    sample_count: int,
    lower_bounds: Sequence[int],
) -> str:
    for index, lower in enumerate(lower_bounds):
        if index + 1 == len(lower_bounds):
            return f"{lower}+"
        upper = lower_bounds[index + 1] - 1
        if sample_count <= upper:
            return f"{lower}-{upper}"
    raise ValueError("sample_count is below the configured cohort range")


def _assert_forbidden_fields_absent(
    value: Any,
    forbidden_fields: Sequence[str],
) -> None:
    if isinstance(value, Mapping):
        forbidden = set(forbidden_fields)
        present = forbidden.intersection(value)
        if present:
            names = ", ".join(sorted(present))
            raise ValueError(f"report contains forbidden fields: {names}")
        for child in value.values():
            _assert_forbidden_fields_absent(child, forbidden_fields)
    elif isinstance(value, list):
        for child in value:
            _assert_forbidden_fields_absent(child, forbidden_fields)


def _protected_aggregates(
    aggregates: Mapping[str, Any],
    policy: ObservationPrivacyPolicy,
) -> Dict[str, Dict[str, Dict[str, int]]]:
    protected: Dict[str, Dict[str, Dict[str, int]]] = {}
    for aggregate_name in policy.persisted_aggregates:
        source = aggregates.get(aggregate_name)
        if not isinstance(source, Mapping):
            raise ValueError(
                f"aggregate {aggregate_name} must be an object"
            )
        unexpected_cells = set(source) - _ALLOWED_AGGREGATE_CELLS[
            aggregate_name
        ]
        if unexpected_cells:
            raise ValueError(
                f"aggregate {aggregate_name} contains unsupported cells"
            )
        cells: Dict[str, Dict[str, int]] = {}
        for key, metrics in source.items():
            if not isinstance(key, str) or not isinstance(metrics, Mapping):
                raise ValueError(
                    f"aggregate {aggregate_name} contains an invalid cell"
                )
            count = metrics.get("count")
            if (
                isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
            ):
                raise ValueError(
                    f"aggregate {aggregate_name} count must be an integer"
                )
            if count >= policy.minimum_cell_count:
                cells[key] = {"count": count}
        protected[aggregate_name] = cells
    return protected


def prepare_persistent_observation(
    report: Mapping[str, Any],
    observed_at: Optional[datetime] = None,
    policy: ObservationPrivacyPolicy = DEFAULT_OBSERVATION_PRIVACY_POLICY,
) -> Dict[str, Any]:
    if set(report) != _REPORT_FIELDS:
        raise ValueError("observation report fields do not match the contract")
    if report.get("schema_version") != OBSERVATION_SCHEMA_VERSION:
        raise ValueError("unsupported observation report schema")
    pipeline_version = report.get("pipeline_version")
    if not isinstance(pipeline_version, str) or not pipeline_version:
        raise ValueError("pipeline_version must be a non-empty string")
    sample_count = report.get("sample_count")
    if (
        isinstance(sample_count, bool)
        or not isinstance(sample_count, int)
        or sample_count < policy.minimum_cohort_size
    ):
        raise ValueError(
            "persistent observation requires at least "
            f"{policy.minimum_cohort_size} samples"
        )
    privacy = report.get("privacy")
    if privacy != {
        "raw_input_stored": False,
        "llm_output_stored": False,
        "automatic_learning": False,
    }:
        raise ValueError("observation privacy flags do not match the contract")
    _assert_forbidden_fields_absent(report, policy.forbidden_fields)
    aggregates = report.get("aggregates")
    if not isinstance(aggregates, Mapping):
        raise ValueError("aggregates must be an object")
    required = set(policy.persisted_aggregates)
    excluded = set(policy.excluded_aggregates)
    if not required.issubset(aggregates) or not excluded.issubset(aggregates):
        raise ValueError("observation aggregates do not match privacy policy")

    instant = _utc(observed_at)
    bucket_start = instant.replace(hour=0, minute=0, second=0, microsecond=0)
    bucket_end = bucket_start + timedelta(hours=policy.bucket_hours)
    return {
        "schema_version": policy.storage_schema_version,
        "policy_schema_version": PRIVACY_POLICY_SCHEMA_VERSION,
        "report_schema_version": OBSERVATION_SCHEMA_VERSION,
        "pipeline_version": pipeline_version,
        "bucket_start_utc": _format_utc(bucket_start),
        "bucket_end_utc": _format_utc(bucket_end),
        "cohort_size_band": _cohort_size_band(
            sample_count,
            policy.cohort_size_lower_bounds,
        ),
        "minimum_cell_count": policy.minimum_cell_count,
        "aggregates": _protected_aggregates(aggregates, policy),
    }


def _local_database_path(path: Path) -> Path:
    raw = str(path)
    if raw.startswith(("\\\\", "//")) or "://" in raw:
        raise ValueError("observation store must use a local filesystem path")
    if path.suffix.lower() != ".db":
        raise ValueError("observation store path must use a .db suffix")
    return path.expanduser().resolve()


class ObservationStore:
    def __init__(
        self,
        path: Path,
        policy: ObservationPrivacyPolicy = (
            DEFAULT_OBSERVATION_PRIVACY_POLICY
        ),
    ) -> None:
        self.path = _local_database_path(path)
        self.policy = policy

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path))
        connection.execute("PRAGMA secure_delete = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS store_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS observation_buckets (
                bucket_start_utc TEXT PRIMARY KEY,
                bucket_end_utc TEXT NOT NULL,
                policy_schema_version TEXT NOT NULL,
                report_schema_version TEXT NOT NULL,
                pipeline_version TEXT NOT NULL,
                cohort_size_band TEXT NOT NULL,
                minimum_cell_count INTEGER NOT NULL,
                aggregates_json TEXT NOT NULL
            )
            """
        )
        existing = connection.execute(
            "SELECT value FROM store_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if existing is None:
            connection.execute(
                "INSERT INTO store_metadata(key, value) VALUES (?, ?)",
                ("schema_version", self.policy.storage_schema_version),
            )
        elif existing[0] != self.policy.storage_schema_version:
            connection.close()
            raise ValueError("observation store schema does not match policy")
        policy_json = json.dumps(
            self.policy.as_dict(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        existing_policy = connection.execute(
            "SELECT value FROM store_metadata WHERE key = 'policy'"
        ).fetchone()
        if existing_policy is None:
            connection.execute(
                "INSERT INTO store_metadata(key, value) VALUES (?, ?)",
                ("policy", policy_json),
            )
        elif existing_policy[0] != policy_json:
            connection.close()
            raise ValueError("observation store policy does not match config")
        connection.commit()
        if os.name != "nt":
            os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)
        return connection

    def persist(
        self,
        report: Mapping[str, Any],
        observed_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        record = prepare_persistent_observation(
            report,
            observed_at=observed_at,
            policy=self.policy,
        )
        now = _utc(observed_at)
        with self._connect() as connection:
            if self.policy.automatic_purge:
                self._purge_connection(connection, now)
            try:
                connection.execute(
                    """
                    INSERT INTO observation_buckets (
                        bucket_start_utc,
                        bucket_end_utc,
                        policy_schema_version,
                        report_schema_version,
                        pipeline_version,
                        cohort_size_band,
                        minimum_cell_count,
                        aggregates_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["bucket_start_utc"],
                        record["bucket_end_utc"],
                        record["policy_schema_version"],
                        record["report_schema_version"],
                        record["pipeline_version"],
                        record["cohort_size_band"],
                        record["minimum_cell_count"],
                        json.dumps(
                            record["aggregates"],
                            ensure_ascii=True,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError(
                    "an immutable observation bucket already exists for "
                    f"{record['bucket_start_utc']}"
                ) from error
        return record

    def _purge_connection(
        self,
        connection: sqlite3.Connection,
        now: datetime,
    ) -> int:
        cutoff = _utc(now) - timedelta(days=self.policy.retention_days)
        cursor = connection.execute(
            "DELETE FROM observation_buckets WHERE bucket_end_utc <= ?",
            (_format_utc(cutoff),),
        )
        return cursor.rowcount

    def purge(self, now: Optional[datetime] = None) -> int:
        if not self.path.exists():
            return 0
        with self._connect() as connection:
            deleted = self._purge_connection(connection, _utc(now))
        if deleted:
            with self._connect() as connection:
                connection.execute("VACUUM")
        return deleted

    def export(self) -> Dict[str, Any]:
        if not self.path.exists():
            raise ValueError(f"observation store does not exist: {self.path}")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    bucket_start_utc,
                    bucket_end_utc,
                    policy_schema_version,
                    report_schema_version,
                    pipeline_version,
                    cohort_size_band,
                    minimum_cell_count,
                    aggregates_json
                FROM observation_buckets
                ORDER BY bucket_start_utc
                """
            ).fetchall()
        buckets = [
            {
                "bucket_start_utc": row[0],
                "bucket_end_utc": row[1],
                "policy_schema_version": row[2],
                "report_schema_version": row[3],
                "pipeline_version": row[4],
                "cohort_size_band": row[5],
                "minimum_cell_count": row[6],
                "aggregates": json.loads(row[7]),
            }
            for row in rows
        ]
        return {
            "schema_version": OBSERVATION_STORE_EXPORT_SCHEMA_VERSION,
            "storage_schema_version": self.policy.storage_schema_version,
            "policy_schema_version": PRIVACY_POLICY_SCHEMA_VERSION,
            "retention_days": self.policy.retention_days,
            "bucket_count": len(buckets),
            "buckets": buckets,
        }
