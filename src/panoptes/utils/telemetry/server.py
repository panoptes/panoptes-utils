"""Telemetry server implementation."""

from __future__ import annotations

import copy
import json
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from multiprocessing import Process
from pathlib import Path
from platform import system
from threading import Lock
from typing import Any, Literal

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

from panoptes.utils import __version__

if system() == "Darwin":
    import multiprocessing

    try:
        if "fork" in multiprocessing.get_all_start_methods():
            multiprocessing.set_start_method("fork")
    except (RuntimeError, ValueError):
        # Ignore if the start method is already set or unsupported.
        pass

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

StorageTarget = Literal["site", "run"]


def utc_iso_z(now: datetime | None = None) -> str:
    """Return a UTC ISO-8601 timestamp with a trailing ``Z``."""

    current = now or datetime.now(UTC)
    return current.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def get_site_day_key(local_dt: datetime) -> str:
    """Return the site stream day key using the local-time noon boundary.

    Args:
        local_dt: A timezone-aware datetime in the machine's local timezone.

    Returns:
        The ``YYYYMMDD`` day key for the site stream file.

    Raises:
        ValueError: If ``local_dt`` is naive.
    """

    if local_dt.tzinfo is None:
        raise ValueError("local_dt must be timezone-aware")

    if local_dt.timetz().replace(tzinfo=None) < time(hour=12):
        local_dt = local_dt - timedelta(days=1)

    return local_dt.strftime("%Y%m%d")


class TelemetryConflictError(RuntimeError):
    """Raised when a requested telemetry action conflicts with server state."""


class TelemetryNotFoundError(RuntimeError):
    """Raised when a requested telemetry resource does not exist."""


@dataclass(slots=True)
class ActiveRun:
    """Metadata describing the currently active run."""

    run_dir: Path
    run_id: str
    meta: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the run."""

        return {
            "run_dir": str(self.run_dir),
            "run_id": self.run_id,
            "meta": copy.deepcopy(self.meta),
            "started_at": self.started_at,
        }


class RunStartRequest(BaseModel):
    """Request body for ``POST /run/start``."""

    run_dir: str | None = None
    run_id: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class EventRequest(BaseModel):
    """Request body for ``POST /event``."""

    type: str
    data: Any
    make_current: bool = True
    meta: dict[str, Any] = Field(default_factory=dict)


class TelemetryService:
    """Manage telemetry state, file storage, and current snapshots."""

    def __init__(
        self,
        site_dir: str | Path,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        """Create a telemetry service.

        Args:
            site_dir: Base directory for rotated site stream NDJSON files.
            now_provider: Callable returning the current local datetime. Defaults to
                ``datetime.now().astimezone()``.
        """

        self.site_dir = Path(site_dir).expanduser()
        self.site_dir.mkdir(parents=True, exist_ok=True)
        self._now_provider = now_provider or (lambda: datetime.now().astimezone())
        self._lock = Lock()
        self._current: dict[StorageTarget, dict[str, dict[str, Any]]] = {
            "site": {},
            "run": {},
        }
        self._seq: dict[StorageTarget, int] = {
            "site": 0,
            "run": 0,
        }
        self._active_run: ActiveRun | None = None

    @property
    def run_active(self) -> bool:
        """Whether a run is currently active."""

        return self._active_run is not None

    def ready(self) -> dict[str, Any]:
        """Return a readiness payload."""

        return {
            "ready": True,
            "run_active": self.run_active,
            "version": __version__,
        }

    def get_run(self) -> dict[str, Any]:
        """Return the active run metadata.

        Raises:
            TelemetryNotFoundError: If no run is active.
        """

        with self._lock:
            if self._active_run is None:
                raise TelemetryNotFoundError("No run is active")

            return self._active_run.as_dict()

    def start_run(
        self,
        run_dir: str | Path | None = None,
        meta: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a new telemetry run context.

        Args:
            run_dir: Directory that will contain ``telemetry.ndjson``. Relative paths
                are resolved under ``site_dir``. If omitted, ``site_dir/run_id``
                is used.
            meta: Optional run metadata to expose via the API.
            run_id: Optional identifier for the run. If omitted, one is taken from
                ``meta["run_id"]`` or, if that is not provided, the next numeric run
                directory under ``site_dir``.

        Returns:
            The active run metadata.

        Raises:
            TelemetryConflictError: If a run is already active.
        """

        with self._lock:
            if self._active_run is not None:
                raise TelemetryConflictError("A run is already active")

            run_meta = copy.deepcopy(meta or {})
            resolved_run_id = str(run_id or run_meta.get("run_id") or self._derive_next_run_id())
            run_path = self._resolve_run_dir(run_dir, resolved_run_id)
            run_path.mkdir(parents=True, exist_ok=True)
            run_meta["run_id"] = resolved_run_id
            self._current["run"] = {}
            self._active_run = ActiveRun(
                run_dir=run_path,
                run_id=resolved_run_id,
                meta=run_meta,
                started_at=utc_iso_z(self._now_provider()),
            )
            return self._active_run.as_dict()

    def stop_run(self) -> dict[str, Any]:
        """Stop the active telemetry run context.

        Returns:
            The run metadata that was active before stopping.

        Raises:
            TelemetryNotFoundError: If no run is active.
        """

        with self._lock:
            if self._active_run is None:
                raise TelemetryNotFoundError("No run is active")

            stopped_run = self._active_run.as_dict()
            self._active_run = None
            self._current["run"] = {}
            return stopped_run

    def append_event(self, request: EventRequest) -> dict[str, Any]:
        """Append an event to the current telemetry target and update the current view.

        Args:
            request: Event request payload.

        Returns:
            The NDJSON event envelope.
        """

        with self._lock:
            target = self._current_target()
            now = self._now_provider()
            event_meta = copy.deepcopy(request.meta)
            if target == "run" and self._active_run is not None:
                event_meta["run_id"] = self._active_run.run_id
            envelope = {
                "seq": self._seq[target] + 1,
                "ts": utc_iso_z(now),
                "stream": target,
                "type": request.type,
                "data": request.data,
                "meta": event_meta,
            }

            output_path = self._stream_path(target, now)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("a", encoding="utf-8") as output_file:
                output_file.write(json.dumps(envelope, separators=(",", ":")) + "\n")

            self._seq[target] = envelope["seq"]

            if request.make_current:
                self._current[target][request.type] = copy.deepcopy(envelope)

            logger.debug(
                "Telemetry event received: type={event_type} target={target} seq={seq} run_id={run_id!r}",
                event_type=request.type,
                target=target,
                seq=envelope["seq"],
                run_id=event_meta.get("run_id"),
            )

            return self._public_event(envelope)

    def current_snapshot(self) -> dict[str, Any]:
        """Return the materialized current view for the public telemetry feed."""

        with self._lock:
            merged_current = copy.deepcopy(self._current["site"])
            merged_current.update(copy.deepcopy(self._current["run"]))
            return {
                "current": {
                    event_type: self._public_event(envelope)
                    for event_type, envelope in merged_current.items()
                },
            }

    def current_event(self, event_type: str) -> dict[str, Any]:
        """Return the current envelope for a single event type.

        Raises:
            TelemetryNotFoundError: If the event type is not present.
        """

        with self._lock:
            if event_type in self._current["run"]:
                return self._public_event(self._current["run"][event_type])
            if event_type in self._current["site"]:
                return self._public_event(self._current["site"][event_type])
            raise TelemetryNotFoundError(f"No current event for type {event_type!r}")

    def _current_target(self) -> StorageTarget:
        return "run" if self._active_run is not None else "site"

    def _resolve_run_dir(self, run_dir: str | Path | None, run_id: str) -> Path:
        if run_dir is None:
            return self.site_dir / run_id

        run_path = Path(run_dir).expanduser()
        if not run_path.is_absolute():
            run_path = self.site_dir / run_path

        return run_path

    def _derive_next_run_id(self) -> str:
        numeric_run_ids = [
            int(path.name) for path in self.site_dir.iterdir() if path.is_dir() and path.name.isdigit()
        ]
        if not numeric_run_ids:
            return "001"

        width = max(3, max(len(str(run_id)) for run_id in numeric_run_ids))
        return str(max(numeric_run_ids) + 1).zfill(width)

    def _stream_path(self, stream: StorageTarget, now: datetime) -> Path:
        if stream == "site":
            return self.site_dir / f"site_{get_site_day_key(now)}.ndjson"

        if self._active_run is None:
            raise TelemetryConflictError("Run stream is unavailable because no run is active")

        return self._active_run.run_dir / "telemetry.ndjson"

    @staticmethod
    def _public_event(envelope: dict[str, Any]) -> dict[str, Any]:
        public_envelope = copy.deepcopy(envelope)
        public_envelope.pop("stream", None)
        return public_envelope


def create_app(service: TelemetryService) -> FastAPI:
    """Create a FastAPI telemetry app backed by ``service``."""

    app = FastAPI()
    app.state.telemetry_service = service

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/ready")
    def ready() -> dict[str, Any]:
        return service.ready()

    @app.get("/run")
    def get_run() -> dict[str, Any]:
        try:
            return service.get_run()
        except TelemetryNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/run/start")
    def start_run(request: RunStartRequest | None = None) -> dict[str, Any]:
        try:
            request = request or RunStartRequest()
            return service.start_run(request.run_dir, request.meta, request.run_id)
        except TelemetryConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/run/stop")
    def stop_run() -> dict[str, Any]:
        try:
            return service.stop_run()
        except TelemetryNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/event")
    def post_event(request: EventRequest) -> dict[str, Any]:
        try:
            return service.append_event(request)
        except TelemetryConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/current")
    def get_current() -> dict[str, Any]:
        return service.current_snapshot()

    @app.get("/current/{event_type}")
    def get_current_type(event_type: str) -> dict[str, Any]:
        try:
            return service.current_event(event_type)
        except TelemetryNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/shutdown")
    def shutdown(request: Request) -> dict[str, bool]:
        server = getattr(request.app.state, "uvicorn_server", None)
        if server is None:
            raise HTTPException(status_code=409, detail="Server shutdown not available")

        client = request.client
        client_host = getattr(client, "host", None)
        if client_host not in {"127.0.0.1", "::1", "localhost"}:
            raise HTTPException(status_code=403, detail="Server shutdown is restricted to loopback clients")

        server.should_exit = True
        return {"shutting_down": True}

    return app


def telemetry_server(
    site_dir: str | Path | None = None,
    host: str | None = None,
    port: str | int | None = None,
    auto_start: bool = True,
    access_logs: bool | None = None,
    verbose: bool = False,
) -> Process:
    """Start the telemetry server in a separate process.

    Args:
        site_dir: Base directory for site stream NDJSON files.
        host: Host address to bind to. Defaults to ``localhost`` or the
            ``PANOPTES_TELEMETRY_HOST`` environment variable.
        port: Port number to bind to. Defaults to ``6562`` or the
            ``PANOPTES_TELEMETRY_PORT`` environment variable.
        auto_start: Whether to start the child process immediately.
        access_logs: Whether to enable uvicorn access logs.
        verbose: Whether to enable DEBUG-level server logging.

    Returns:
        The child process that hosts the telemetry API.
    """

    telemetry_dir = Path(site_dir or os.getenv("PANOPTES_TELEMETRY_SITE_DIR", "telemetry"))
    bind_host = host or os.getenv("PANOPTES_TELEMETRY_HOST", "localhost")
    bind_port = int(port or os.getenv("PANOPTES_TELEMETRY_PORT", 6562))
    app = create_app(TelemetryService(telemetry_dir))

    def start_server(host: str = "localhost", port: int = 6562) -> None:
        try:
            logger.remove()
            logger.add(sys.stderr, level="DEBUG" if verbose else "INFO")
            logger.info(f"Starting telemetry server on {host}:{port} with site_dir={telemetry_dir!s}")
            config = uvicorn.Config(
                app,
                host=host,
                port=int(port),
                log_level="warning",
                access_log=bool(access_logs),
            )
            server = uvicorn.Server(config)
            app.state.uvicorn_server = server
            server.run()
        except OSError:
            logger.warning("Problem starting telemetry server, is another telemetry server already running?")
            return None
        except Exception as error:  # pragma: no cover
            logger.warning(f"Problem starting telemetry server: {error!r}")
            return None

    server_process = Process(
        target=start_server,
        daemon=True,
        kwargs={"host": bind_host, "port": bind_port},
    )
    if auto_start:
        server_process.start()
    return server_process
