"""Pydantic models for telemetry event envelopes."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

# PanDB-compatible aliases: dict-style access via these keys is supported
# in addition to the native field names, so that call-sites previously
# written against ``PanFileDB`` records work without modification.
#
#   event["_id"]   → str(event.seq)   (PanDB used a UUID string; we use seq)
#   event["date"]  → event.ts         (PanDB used "date"; we use "ts")
_PANDB_ALIASES: dict[str, str] = {
    "_id": "seq",  # resolved via _resolve_alias()
    "date": "ts",
}


class TelemetryEvent(BaseModel):
    """A telemetry event envelope returned by the telemetry server.

    Fields mirror the server's NDJSON envelope shape::

        {"seq": 1, "ts": "2026-05-20T10:00:00Z", "type": "weather",
         "data": {...}, "meta": {...}}

    Both attribute-style and dict-style access are supported so that
    existing call-sites continue to work without modification::

        event.seq          # attribute (native)
        event["seq"]       # dict-style (native)
        event.get("seq")   # dict-style with default
        "seq" in event     # containment check

    PanDB-compatible aliases are also supported for call-sites previously
    written against ``PanFileDB`` records::

        event["_id"]   # → str(event.seq)
        event["date"]  # → event.ts
        "_id" in event # True
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    seq: int
    ts: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("data", when_used="json")
    def _serialize_data(self, v: dict[str, Any]) -> dict[str, Any]:
        """Convert non-JSON-native values (e.g. Quantities) to JSON-safe primitives.

        Only called during JSON serialization (model_dump_json / model_dump(mode="json")),
        so Python-level access (event.data, event["data"]) always returns the original
        deserialized values including Quantity objects.
        """
        return json.loads(json.dumps(v, default=str))

    def _resolve_alias(self, key: str) -> Any:
        """Resolve a PanDB-compatible alias to its native value."""
        native = _PANDB_ALIASES[key]
        value = getattr(self, native)
        # _id must be a string to match PanDB's UUID-string convention.
        return str(value) if key == "_id" else value

    # ------------------------------------------------------------------
    # Dict-compatible helpers — native fields + PanDB aliases
    # ------------------------------------------------------------------

    def __getitem__(self, key: str) -> Any:
        if key in _PANDB_ALIASES:
            return self._resolve_alias(key)
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        return key in _PANDB_ALIASES or key in self.model_fields

    def get(self, key: str, default: Any = None) -> Any:
        if key in _PANDB_ALIASES:
            return self._resolve_alias(key)
        return getattr(self, key, default)

    def keys(self):
        return self.model_fields.keys()

    def items(self):
        return ((k, getattr(self, k)) for k in self.model_fields)

    def values(self):
        return (getattr(self, k) for k in self.model_fields)
