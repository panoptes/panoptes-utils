"""Standalone CLI for the telemetry server."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click
import requests
from loguru import logger

from panoptes.utils.telemetry.server import telemetry_server


def _server_is_ready(host: str, port: int) -> bool:
    try:
        response = requests.get(f"http://{host}:{port}/ready", timeout=1)
        response.raise_for_status()
    except requests.RequestException:
        return False

    payload = response.json()
    return bool(payload.get("ready"))


@click.group()
@click.option(
    "--verbose/--no-verbose",
    envvar="PANOPTES_DEBUG",
    help="Turn on panoptes logger for telemetry, default False.",
)
@click.option(
    "--host",
    default=None,
    envvar="PANOPTES_TELEMETRY_HOST",
    help="The telemetry server host. Defaults to localhost.",
)
@click.option(
    "--port",
    default=None,
    envvar="PANOPTES_TELEMETRY_PORT",
    type=int,
    help="The telemetry server port. Defaults to 6562.",
)
@click.option(
    "--system-dir",
    default=None,
    envvar="PANOPTES_TELEMETRY_SYSTEM_DIR",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Directory for rotated system telemetry NDJSON files. Defaults to ./telemetry.",
)
@click.pass_context
def telemetry_server_cli(
    context,
    host: str | None = None,
    port: int | None = None,
    system_dir: Path | None = None,
    verbose: bool = False,
) -> None:
    """Command line interface for the telemetry server."""

    context.ensure_object(dict)
    bind_host = host or "localhost"
    client_host = "localhost" if bind_host == "0.0.0.0" else bind_host

    context.obj["bind_host"] = bind_host
    context.obj["host"] = client_host
    context.obj["port"] = port or 6562
    context.obj["system_dir"] = system_dir or Path("telemetry")

    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if verbose else "INFO")


@click.command("run")
@click.option("--heartbeat", default=2.0, help="Heartbeat interval in seconds.")
@click.option(
    "--startup-timeout",
    default=30.0,
    help="Seconds to wait for the telemetry server to become ready before giving up.",
)
@click.pass_context
def run(context, heartbeat: float = 2.0, startup_timeout: float = 30.0) -> None:
    """Run the telemetry server and wait for readiness."""

    bind_host = context.obj["bind_host"]
    host = context.obj["host"]
    port = context.obj["port"]
    system_dir = context.obj["system_dir"]

    server_process = telemetry_server(
        system_dir=system_dir,
        host=bind_host,
        port=port,
        auto_start=False,
    )

    try:
        click.echo("Starting telemetry server. Ctrl-c to stop")
        server_process.start()
        click.echo(
            f"Telemetry server started on server_process.pid={server_process.pid!r}. "
            f"Waiting for readiness on {host}:{port}"
        )

        startup_elapsed = 0.0
        startup_interval = 0.5
        while startup_elapsed < startup_timeout:
            if _server_is_ready(host, port):
                break
            if not server_process.is_alive():
                logger.error("Telemetry server process exited before becoming ready")
                return
            time.sleep(startup_interval)
            startup_elapsed += startup_interval
        else:
            logger.error(f"Telemetry server did not become ready within {startup_timeout}s")
            server_process.terminate()
            server_process.join(5)
            return

        logger.info("Telemetry server is ready")

        while server_process.is_alive():
            time.sleep(heartbeat)
    except KeyboardInterrupt:
        logger.info(f"Telemetry server interrupted, shutting down {server_process.pid}")
        if server_process.is_alive():
            server_process.terminate()
            server_process.join(30)


@click.command("stop")
@click.pass_context
def stop(context) -> None:
    """Stop the telemetry server via the shutdown endpoint."""

    host = context.obj["host"]
    port = context.obj["port"]
    logger.info(f"Shutting down telemetry server on {host}:{port}")
    response = requests.post(f"http://{host}:{port}/shutdown", timeout=5)
    response.raise_for_status()
    click.echo(response.json())


telemetry_server_cli.add_command(run)
telemetry_server_cli.add_command(stop)
