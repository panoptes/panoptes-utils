"""Client helpers for the telemetry server."""

from __future__ import annotations

import os
from typing import Any

import requests
from loguru import logger


class TelemetryClientError(RuntimeError):
    """Raised when the telemetry server returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Initialize the error.

        Args:
            status_code: HTTP status code returned by the server.
            detail: Error detail returned by the server.
        """

        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Telemetry server error {status_code}: {detail}")


class TelemetryClient:
    """Simple Python client for the telemetry server.

    The client wraps the telemetry HTTP API with small convenience methods for the
    common lifecycle: check readiness, optionally start a run, emit events, inspect
    the current materialized view, and stop the run or the server.

    `start_run` activates a run context. After that, `post_event(...)` calls are
    associated with the active run and stamped with `meta.run_id` until
    `stop_run()` is called.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | str | None = None,
        timeout: float = 5.0,
        session: Any | None = None,
        base_url: str | None = None,
    ) -> None:
        """Create a telemetry client.

        Args:
            host: Telemetry server host. Defaults to `PANOPTES_TELEMETRY_HOST` or `localhost`.
            port: Telemetry server port. Defaults to `PANOPTES_TELEMETRY_PORT` or `6562`.
            timeout: Request timeout in seconds.
            session: Optional requests-compatible client object for dependency injection.
            base_url: Optional explicit base URL. If provided, this takes precedence over
                `host` and `port`.
        """

        resolved_host = host or os.getenv("PANOPTES_TELEMETRY_HOST", "localhost")
        resolved_port = int(port or os.getenv("PANOPTES_TELEMETRY_PORT", 6562))
        self.base_url = (base_url or f"http://{resolved_host}:{resolved_port}").rstrip("/")
        self.timeout = timeout
        self._session = session or requests

    def health(self) -> dict[str, Any]:
        """Return the telemetry health response."""

        return self._request("GET", "/health")

    def ready(self) -> dict[str, Any]:
        """Return the telemetry readiness response."""

        return self._request("GET", "/ready")

    def get_run(self) -> dict[str, Any]:
        """Return the current run metadata."""

        return self._request("GET", "/run")

    def start_run(
        self,
        run_dir: str | None = None,
        run_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Start a telemetry run.

        Relative `run_dir` values are resolved by the server under its configured
        `site_dir`. If `run_dir` is omitted, the server uses `site_dir/run_id`.
        If `run_id` is also omitted, the server derives the next numeric run ID
        from existing run directories under `site_dir`.
        """

        payload_meta = dict(meta or {})
        if run_id is not None:
            payload_meta["run_id"] = run_id
        return self._request(
            "POST",
            "/run/start",
            json={"run_dir": run_dir, "run_id": run_id, "meta": payload_meta},
        )

    def stop_run(self) -> dict[str, Any]:
        """Stop the current telemetry run."""

        return self._request("POST", "/run/stop")

    def post_event(
        self,
        event_type: str,
        data: Any,
        make_current: bool = True,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Post a telemetry event to the current telemetry context."""

        payload = {
            "type": event_type,
            "data": data,
            "make_current": make_current,
            "meta": meta or {},
        }
        return self._request("POST", "/event", json=payload)

    def current(self) -> dict[str, Any]:
        """Return the current snapshot for the public telemetry feed."""

        return self._request("GET", "/current")

    def current_event(self, event_type: str) -> dict[str, Any]:
        """Return the current envelope for a single event type."""

        return self._request("GET", f"/current/{event_type}")

    def shutdown(self) -> dict[str, Any]:
        """Request telemetry server shutdown."""

        return self._request("POST", "/shutdown")

    # ------------------------------------------------------------------
    # PanDB-compatible interface
    #
    # These methods mirror the AbstractPanDB API so that code written
    # against panoptes.utils.database can switch to the telemetry server
    # by replacing the PanDB instantiation with a TelemetryClient — no
    # other call-site changes required.
    # ------------------------------------------------------------------

    def insert_current(
        self,
        collection: str,
        obj: Any,
        store_permanently: bool = True,
    ) -> str:
        """PanDB-compatible alias: record an event and mark it current.

        The ``store_permanently`` flag is accepted for API compatibility but
        has no effect — the telemetry server always appends events to the
        NDJSON stream and always keeps the in-memory current snapshot.

        Args:
            collection: Event type / collection name (e.g. ``"weather"``).
            obj: Data payload to record.
            store_permanently: Accepted but ignored; included for PanDB
                compatibility only.

        Returns:
            The sequence number of the recorded event as a string.
        """
        response = self.post_event(collection, obj, make_current=True)
        return str(response.get("seq", ""))

    def insert(self, collection: str, obj: Any) -> str:
        """PanDB-compatible alias: record an event without updating the current snapshot.

        Args:
            collection: Event type / collection name.
            obj: Data payload to record.

        Returns:
            The sequence number of the recorded event as a string.
        """
        response = self.post_event(collection, obj, make_current=False)
        return str(response.get("seq", ""))

    def get_current(self, collection: str) -> dict[str, Any] | None:
        """PanDB-compatible alias: return the most recent snapshot for a collection.

        The returned dict uses the same keys as a PanDB record (``_id``,
        ``type``, ``date``, ``data``) so call-sites do not need to change.

        Args:
            collection: Event type / collection name.

        Returns:
            A dict with keys ``_id``, ``type``, ``date``, and ``data``,
            or ``None`` if no current event exists for the collection.
        """
        try:
            response = self.current_event(collection)
        except TelemetryClientError as exc:
            if exc.status_code == 404:
                return None
            raise
        return {
            "_id": str(response.get("seq", "")),
            "type": response.get("type", collection),
            "date": response.get("ts", ""),
            "data": response.get("data"),
        }

    def find(self, collection: str, obj_id: str) -> dict[str, Any] | None:
        """PanDB-compatible stub: look up a record by ID.

        The telemetry server does not expose historical lookup by ID.
        This method always returns ``None`` and logs a warning. To query
        historical records, parse the NDJSON files directly with ``jq`` or
        a DataFrame library.

        Args:
            collection: Event type / collection name.
            obj_id: Record identifier (ignored).

        Returns:
            Always ``None``.
        """
        logger.warning(
            "TelemetryClient.find() is not supported — "
            "parse the NDJSON files directly for historical queries."
        )
        return None

    def clear_current(self, record_type: str) -> None:
        """PanDB-compatible no-op: clear the current snapshot for a type.

        The telemetry server manages its current snapshot in memory and
        does not support explicit clearing via the API. This method is a
        no-op included for PanDB drop-in compatibility.

        Args:
            record_type: Event type to clear (accepted but ignored).
        """
        logger.debug(
            "TelemetryClient.clear_current({!r}) called — no-op on telemetry server.",
            record_type,
        )

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._session.request(
            method,
            f"{self.base_url}{path}",
            json=json,
            params=params,
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            detail = response.text
            try:
                payload = response.json()
                detail = payload.get("detail", detail)
            except ValueError:
                pass
            raise TelemetryClientError(response.status_code, str(detail))

        return response.json()
