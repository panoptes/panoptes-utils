"""Client helpers for the telemetry server."""

from __future__ import annotations

import os
from typing import Any

import requests


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

    `start_run` is important because it switches the server's default event target
    from the always-available `system` stream to the run-specific `run` stream.
    After `start_run`, calls to `post_event(...)` without an explicit `stream=...`
    are written to `<run_dir>/telemetry.ndjson` and stamped with `meta.run_id`
    until `stop_run()` is called.

    Examples:
        >>> class FakeResponse:
        ...     def __init__(self, status_code, payload):
        ...         self.status_code = status_code
        ...         self._payload = payload
        ...         self.text = str(payload)
        ...     def json(self):
        ...         return self._payload
        >>> class FakeSession:
        ...     def __init__(self):
        ...         self.run_active = False
        ...         self.run_id = None
        ...     def request(self, method, url, json=None, params=None, timeout=5.0):
        ...         path = url.removeprefix("http://example.test")
        ...         if path == "/ready":
        ...             return FakeResponse(200, {"ready": True, "run_active": self.run_active})
        ...         if path == "/run/start":
        ...             self.run_active = True
        ...             self.run_id = json["run_id"]
        ...             payload = {"run_dir": json["run_dir"], "run_id": self.run_id, "meta": json["meta"]}
        ...             return FakeResponse(200, payload)
        ...         if path == "/event":
        ...             stream = json["stream"] or ("run" if self.run_active else "system")
        ...             meta = dict(json["meta"])
        ...             if stream == "run":
        ...                 meta["run_id"] = self.run_id
        ...             payload = {"stream": stream, "type": json["type"], "data": json["data"], "meta": meta}
        ...             return FakeResponse(200, payload)
        ...         if path == "/run/stop":
        ...             self.run_active = False
        ...             return FakeResponse(200, {"stopped": True})
        ...         if path == "/current":
        ...             payload = {"current": {"status": {"data": {"state": "running"}}}}
        ...             return FakeResponse(200, payload)
        ...         return FakeResponse(200, {"ok": True})
        >>> client = TelemetryClient(base_url="http://example.test", session=FakeSession())
        >>> client.ready()
        {'ready': True, 'run_active': False}
        >>> client.post_event("weather", {"sky": "clear"})["stream"]
        'system'
        >>> client.start_run("/tmp/panoptes-run-001", run_id="001", meta={"observer": "demo"})
        {'run_dir': '/tmp/panoptes-run-001', 'run_id': '001', 'meta': {'observer': 'demo', 'run_id': '001'}}
        >>> client.post_event("status", {"state": "running"})["meta"]["run_id"]
        '001'
        >>> sorted(client.current()["current"])
        ['status']
        >>> client.stop_run()
        {'stopped': True}
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
        run_dir: str,
        run_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Start a telemetry run.

        If `run_id` is omitted, the server will use `meta["run_id"]` or the
        run directory name.
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
        stream: str | None = None,
        make_current: bool = True,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Post a telemetry event."""

        payload = {
            "type": event_type,
            "data": data,
            "stream": stream,
            "make_current": make_current,
            "meta": meta or {},
        }
        return self._request("POST", "/event", json=payload)

    def current(self, stream: str | None = None) -> dict[str, Any]:
        """Return the current snapshot for a telemetry stream."""

        params = {"stream": stream} if stream is not None else None
        return self._request("GET", "/current", params=params)

    def current_event(self, event_type: str, stream: str | None = None) -> dict[str, Any]:
        """Return the current envelope for a single event type."""

        params = {"stream": stream} if stream is not None else None
        return self._request("GET", f"/current/{event_type}", params=params)

    def shutdown(self) -> dict[str, Any]:
        """Request telemetry server shutdown."""

        return self._request("POST", "/shutdown")

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
