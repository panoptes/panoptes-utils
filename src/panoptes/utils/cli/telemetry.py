"""Typer commands for the telemetry server."""

from __future__ import annotations

import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import requests
import typer
from loguru import logger
from rich import print
from rich.console import Console, Group
from rich.json import JSON
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from panoptes.utils.telemetry import TelemetryClient
from panoptes.utils.telemetry.server import telemetry_server

app = typer.Typer()
console = Console()


def _server_is_ready(host: str, port: int) -> bool:
    """Return whether the telemetry server is responding as ready."""

    try:
        response = requests.get(f"http://{host}:{port}/ready", timeout=1)
        response.raise_for_status()
    except requests.RequestException:
        return False

    payload = response.json()
    return bool(payload.get("ready"))


def _payload_panel(
    payload: dict[str, Any],
    event_type: str | None = None,
    *,
    follow: bool = False,
    interval: float | None = None,
) -> Panel:
    """Build a rich panel for the current telemetry payload."""

    title = "Current telemetry"
    if event_type is not None:
        title = f"Current telemetry: {event_type}"

    subtitle = None
    if follow and interval is not None:
        subtitle = f"live refresh every {interval:g}s"

    body = _render_payload(payload)

    return Panel(
        body,
        title=title,
        subtitle=subtitle,
        border_style="cyan",
    )


def _render_payload(payload: dict[str, Any]):
    """Render telemetry payloads with structured envelope fields plus JSON payloads."""

    current_payload = payload.get("current")
    if isinstance(current_payload, dict):
        event_panels = [
            _event_panel(event_type, event_payload)
            for event_type, event_payload in current_payload.items()
            if isinstance(event_payload, dict)
        ]
        if not event_panels:
            return Markdown("_No current telemetry values_")
        return Group(*event_panels)

    return _event_panel(str(payload.get("type", "event")), payload)


def _event_panel(event_name: str, event_payload: dict[str, Any]) -> Panel:
    """Render one telemetry event envelope."""

    envelope_items: list[tuple[str, str]] = []
    for key in ("type", "seq", "ts"):
        value = event_payload.get(key)
        if value is not None:
            envelope_items.append((key, str(value)))

    meta_payload = event_payload.get("meta")
    if isinstance(meta_payload, dict):
        for key, value in sorted(meta_payload.items()):
            envelope_items.append((f"meta.{key}", str(value)))

    summary = Table.grid(expand=True, padding=(0, 2))
    summary.add_column(style="bold cyan", ratio=1)
    summary.add_column(ratio=2)
    summary.add_column(style="bold cyan", ratio=1)
    summary.add_column(ratio=2)

    for index in range(0, len(envelope_items), 2):
        left_key, left_value = envelope_items[index]
        if index + 1 < len(envelope_items):
            right_key, right_value = envelope_items[index + 1]
        else:
            right_key, right_value = "", ""
        summary.add_row(left_key, left_value, right_key, right_value)

    sections: list[object] = [summary]

    data_payload = event_payload.get("data")
    if data_payload is not None:
        sections.extend(
            [
                Markdown("**data**"),
                JSON.from_data(data_payload),
            ]
        )

    return Panel(
        Group(*sections),
        title=event_name,
        border_style="blue",
    )


def _get_current_payload(client: TelemetryClient, event_type: str | None) -> dict[str, Any]:
    """Fetch the current telemetry payload."""

    if event_type is not None:
        return client.current_event(event_type)
    return client.current()


@app.command("run")
def run(
    host: str = typer.Option(
        "localhost",
        envvar="PANOPTES_TELEMETRY_HOST",
        help="Host address to bind the telemetry server to.",
    ),
    port: int = typer.Option(
        6562,
        envvar="PANOPTES_TELEMETRY_PORT",
        help="Port number to bind the telemetry server to.",
    ),
    site_dir: Path = typer.Option(
        Path("telemetry"),
        envvar="PANOPTES_TELEMETRY_SITE_DIR",
        file_okay=False,
        dir_okay=True,
        help="Directory for rotated site telemetry NDJSON files.",
    ),
    heartbeat: float = typer.Option(2.0, help="Heartbeat interval in seconds."),
    startup_timeout: float = typer.Option(
        30.0,
        help="Seconds to wait for the telemetry server to become ready before giving up.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable DEBUG-level telemetry server logging, including one log line per event.",
    ),
) -> None:
    """Run the telemetry server and wait for readiness."""

    bind_host = host
    client_host = "localhost" if bind_host == "0.0.0.0" else bind_host

    server_process = telemetry_server(
        site_dir=site_dir,
        host=bind_host,
        port=port,
        auto_start=False,
        verbose=verbose,
    )

    try:
        print("Starting telemetry server. Ctrl-c to stop")
        server_process.start()
        print(
            f"Telemetry server started on server_process.pid={server_process.pid!r}. "
            f"Waiting for readiness on {client_host}:{port}"
        )

        startup_elapsed = 0.0
        startup_interval = 0.5
        while startup_elapsed < startup_timeout:
            if _server_is_ready(client_host, port):
                break
            if not server_process.is_alive():
                logger.error("Telemetry server process exited before becoming ready")
                raise typer.Exit(code=1)
            time.sleep(startup_interval)
            startup_elapsed += startup_interval
        else:
            logger.error(f"Telemetry server did not become ready within {startup_timeout}s")
            server_process.terminate()
            server_process.join(5)
            raise typer.Exit(code=1)

        logger.info("Telemetry server is ready")

        while server_process.is_alive():
            time.sleep(heartbeat)
    except KeyboardInterrupt:
        logger.info(f"Telemetry server interrupted, shutting down {server_process.pid}")
        if server_process.is_alive():
            server_process.terminate()
            server_process.join(30)


@app.command("stop")
def stop(
    host: str = typer.Option(
        "localhost",
        envvar="PANOPTES_TELEMETRY_HOST",
        help="Host address of the telemetry server.",
    ),
    port: int = typer.Option(
        6562,
        envvar="PANOPTES_TELEMETRY_PORT",
        help="Port number of the telemetry server.",
    ),
) -> None:
    """Stop the telemetry server via the shutdown endpoint."""

    logger.info(f"Shutting down telemetry server on {host}:{port}")
    response = requests.post(f"http://{host}:{port}/shutdown", timeout=5)
    response.raise_for_status()
    print(response.json())


@app.command("current")
def current(
    event_type: str | None = typer.Argument(
        None,
        help="Optional event type to fetch instead of the full current telemetry snapshot.",
    ),
    host: str = typer.Option(
        "localhost",
        envvar="PANOPTES_TELEMETRY_HOST",
        help="Host address of the telemetry server.",
    ),
    port: int = typer.Option(
        6562,
        envvar="PANOPTES_TELEMETRY_PORT",
        help="Port number of the telemetry server.",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Poll repeatedly and print updated readings as they change.",
    ),
    interval: float = typer.Option(
        2.0,
        min=0.1,
        help="Polling interval in seconds when following current telemetry.",
    ),
) -> None:
    """Display the current telemetry reading."""

    client = TelemetryClient(host=host, port=port)
    last_payload: dict[str, Any] | None = None

    if not follow:
        payload = _get_current_payload(client, event_type)
        console.print(_payload_panel(payload, event_type))
        return

    try:
        initial_payload = _get_current_payload(client, event_type)
        last_payload = deepcopy(initial_payload)
        with Live(
            _payload_panel(initial_payload, event_type, follow=True, interval=interval),
            console=console,
            refresh_per_second=max(4, int(1 / interval)),
        ) as live:
            while True:
                time.sleep(interval)
                payload = _get_current_payload(client, event_type)
                if last_payload != payload:
                    live.update(_payload_panel(payload, event_type, follow=True, interval=interval))
                    last_payload = deepcopy(payload)
    except KeyboardInterrupt:
        print("[yellow]Stopped following telemetry.[/yellow]")


if __name__ == "__main__":
    app()
