"""Pydantic models for telemetry event envelopes."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TelemetryEvent(BaseModel):
    """A telemetry event envelope returned by the telemetry server.

    Fields mirror the server's NDJSON envelope shape::

        {"seq": 1, "ts": "2026-05-20T10:00:00Z", "type": "weather",
         "data": {...}, "meta": {...}}

    Both attribute-style and dict-style access are supported so that
    existing call-sites written against plain ``dict`` responses continue
    to work without modification::

        event.seq          # attribute
        event["seq"]       # dict-style
        event.get("seq")   # dict-style with default
        "seq" in event     # containment check
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    seq: int
    ts: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("data", mode="plain")
    def _serialize_data(self, v: dict[str, Any]) -> dict[str, Any]:
        """Convert non-JSON-native values (e.g. Quantities) to JSON-safe primitives."""
        return json.loads(json.dumps(v, default=str))

    # ------------------------------------------------------------------
    # Dict-compatible helpers for backward compat with plain-dict callers
    # ------------------------------------------------------------------

    def __getitem__(self, key: str) -> Any:
        return self.model_dump()[key]

    def __contains__(self, key: object) -> bool:
        return key in self.model_dump()

    def get(self, key: str, default: Any = None) -> Any:
        return self.model_dump().get(key, default)

    def keys(self):
        return self.model_dump().keys()

    def items(self):
        return self.model_dump().items()

    def values(self):
        return self.model_dump().values()


class PanDBRecord(BaseModel):
    """PanDB-compatible record returned by :meth:`TelemetryClient.get_current`.

    Uses the same field names as a ``PanFileDB`` record so that call-sites
    do not need to change::

        record["_id"]    # sequence number as string
        record["type"]   # event type / collection name
        record["date"]   # ISO-8601 timestamp string
        record["data"]   # deserialized event data dict
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)

    id: str = Field(alias="_id")
    type: str
    date: str
    data: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("data", mode="plain")
    def _serialize_data(self, v: dict[str, Any]) -> dict[str, Any]:
        return json.loads(json.dumps(v, default=str))

    # ------------------------------------------------------------------
    # Dict-compatible helpers — use by_alias=True so "_id" is exposed
    # ------------------------------------------------------------------

    def __getitem__(self, key: str) -> Any:
        return self.model_dump(by_alias=True)[key]

    def __contains__(self, key: object) -> bool:
        return key in self.model_dump(by_alias=True)

    def get(self, key: str, default: Any = None) -> Any:
        return self.model_dump(by_alias=True).get(key, default)

    def keys(self):
        return self.model_dump(by_alias=True).keys()

    def items(self):
        return self.model_dump(by_alias=True).items()

    def values(self):
        return self.model_dump(by_alias=True).values()
