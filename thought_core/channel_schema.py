import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


CHANNEL_SCHEMA_CONFIG_VERSION = "pattern-channel-schemas.v1"
CHANNEL_SEMANTICS = "unit_local_prototype_affinity_only"
CHANNEL_ALLOCATION_METHOD = "blake2b_unit_prototype.v1"
DEFAULT_CHANNEL_SCHEMA_PATH = (
    Path(__file__).resolve().parent / "config" / "channel_schemas.json"
)


@dataclass(frozen=True)
class ChannelSchemaDefinition:
    schema_id: str
    unit_type: str
    channel_count: int
    spatial_semantics: bool
    channel_semantics: str
    allocation_method: str
    prototype_channels: Tuple[int, ...]
    unassigned_channel_role: str
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": CHANNEL_SCHEMA_CONFIG_VERSION,
            "schema_id": self.schema_id,
            "unit_type": self.unit_type,
            "channel_count": self.channel_count,
            "spatial_semantics": self.spatial_semantics,
            "channel_semantics": self.channel_semantics,
            "allocation_method": self.allocation_method,
            "prototype_channels": list(self.prototype_channels),
            "unassigned_channel_role": self.unassigned_channel_role,
        }


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def load_channel_schemas(
    path: Optional[Path] = None,
) -> Dict[str, ChannelSchemaDefinition]:
    config_path = path or DEFAULT_CHANNEL_SCHEMA_PATH
    payload: Any = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("channel schema config must be an object")
    if payload.get("schema_version") != CHANNEL_SCHEMA_CONFIG_VERSION:
        raise ValueError(
            "unsupported channel schema config: "
            f"{payload.get('schema_version')!r}"
        )

    channel_count = payload.get("channel_count")
    if (
        isinstance(channel_count, bool)
        or not isinstance(channel_count, int)
        or channel_count < 1
    ):
        raise ValueError("channel_count must be a positive integer")
    if payload.get("spatial_semantics") is not False:
        raise ValueError("v1 channel schemas require spatial_semantics=false")
    channel_semantics = _require_string(
        payload.get("channel_semantics"),
        "channel_semantics",
    )
    if channel_semantics != CHANNEL_SEMANTICS:
        raise ValueError("unsupported channel semantics")
    allocation_method = _require_string(
        payload.get("allocation_method"),
        "allocation_method",
    )
    if allocation_method != CHANNEL_ALLOCATION_METHOD:
        raise ValueError("unsupported channel allocation method")

    raw_units = payload.get("units")
    if not isinstance(raw_units, dict) or not raw_units:
        raise ValueError("channel schema config requires unit definitions")

    schemas: Dict[str, ChannelSchemaDefinition] = {}
    schema_ids = set()
    for unit_type, raw_definition in raw_units.items():
        if not isinstance(unit_type, str) or not unit_type:
            raise ValueError("unit type must be a non-empty string")
        if not isinstance(raw_definition, Mapping):
            raise ValueError(f"channel schema for {unit_type} must be an object")
        schema_id = _require_string(
            raw_definition.get("schema_id"),
            f"{unit_type}.schema_id",
        )
        if schema_id in schema_ids:
            raise ValueError(f"duplicate channel schema id: {schema_id}")
        schema_ids.add(schema_id)

        raw_channels = raw_definition.get("prototype_channels")
        if not isinstance(raw_channels, list) or not raw_channels:
            raise ValueError(
                f"{unit_type}.prototype_channels must be a non-empty list"
            )
        if any(
            isinstance(channel, bool) or not isinstance(channel, int)
            for channel in raw_channels
        ):
            raise ValueError("prototype channels must be integer indices")
        prototype_channels = tuple(sorted(raw_channels))
        if len(prototype_channels) != len(set(prototype_channels)):
            raise ValueError("prototype channels must be unique")
        if any(
            channel < 0 or channel >= channel_count
            for channel in prototype_channels
        ):
            raise ValueError("prototype channel is out of range")

        schemas[unit_type] = ChannelSchemaDefinition(
            schema_id=schema_id,
            unit_type=unit_type,
            channel_count=channel_count,
            spatial_semantics=False,
            channel_semantics=channel_semantics,
            allocation_method=allocation_method,
            prototype_channels=prototype_channels,
            unassigned_channel_role=_require_string(
                raw_definition.get("unassigned_channel_role"),
                f"{unit_type}.unassigned_channel_role",
            ),
            rationale=_require_string(
                raw_definition.get("rationale"),
                f"{unit_type}.rationale",
            ),
        )
    return schemas
