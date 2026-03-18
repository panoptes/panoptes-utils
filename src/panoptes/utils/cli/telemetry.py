"""Typer commands for the telemetry server."""

from __future__ import annotations

import time
from pathlib import Path

import requests
import typer
from loguru import logger
from rich import print

from panoptes.utils.telemetry.server import telemetry_server

app = typer.Typer()


def _server_is_ready(host: str, port: int) -> bool:
    """Return whether the telemetry server is responding as ready."""

    try:
        response = requests.get(f"http://{host}:{port}/ready", timeout=1)
        response.raise_for_status()
    except requests.RequestException:
        return False

    payload = response.json()
    return bool(payload.get("ready"))


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
) -> None:
    """Run the telemetry server and wait for readiness."""

    bind_host = host
    client_host = "localhost" if bind_host == "0.0.0.0" else bind_host

    server_process = telemetry_server(
        site_dir=site_dir,
        host=bind_host,
        port=port,
        auto_start=False,
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


if __name__ == "__main__":
    app()
