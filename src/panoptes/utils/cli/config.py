"""Typer commands for the config server."""

from __future__ import annotations

import time

import typer
from loguru import logger
from rich import print

from panoptes.utils.config.client import get_config, server_is_running, set_config

app = typer.Typer()


@app.command("run")
def run(
    host: str = typer.Option(
        None,
        envvar="PANOPTES_CONFIG_HOST",
        help="Host address to bind the config server to.",
    ),
    port: int = typer.Option(
        6563,
        envvar="PANOPTES_CONFIG_PORT",
        help="Port number to bind the config server to.",
    ),
    config_file: str = typer.Option(
        None,
        envvar="PANOPTES_CONFIG_FILE",
        help="Path to the YAML config file to load.",
    ),
    load_local: bool = typer.Option(True, help="Load local config files on startup."),
    save_local: bool = typer.Option(True, help="Save config changes to the local file."),
    heartbeat: float = typer.Option(2.0, help="Heartbeat interval in seconds."),
    startup_timeout: float = typer.Option(
        30.0,
        help="Seconds to wait for the config server to become ready before giving up.",
    ),
) -> None:
    """Run the config server and block until it stops."""

    try:
        from panoptes.utils.config import server
    except ImportError as exc:
        logger.error(
            "Config server dependencies are not installed. "
            "Install the 'config' extra, e.g. `pip install 'panoptes-utils[config]'`, "
            "to use `panoptes-utils config run`."
        )
        raise typer.Exit(code=1) from exc

    bind_host = host
    client_host = "localhost" if bind_host in (None, "0.0.0.0") else bind_host

    try:
        server_process = server.config_server(
            config_file,
            host=bind_host,
            port=port,
            load_local=load_local,
            save_local=save_local,
            auto_start=False,
        )
    except Exception as e:
        logger.error(f"Unable to start config server: {e!r}")
        raise typer.Exit(code=1)

    try:
        print("Starting config server. Ctrl-c to stop")
        server_process.start()
        print(
            f"Config server started on server_process.pid={server_process.pid!r}. "
            f"Waiting for readiness on {client_host}:{port}"
        )

        startup_elapsed = 0.0
        startup_interval = 0.5
        while startup_elapsed < startup_timeout:
            if server_is_running(host=client_host, port=port):
                break
            if not server_process.is_alive():
                logger.error("Config server process exited before becoming ready")
                raise typer.Exit(code=1)
            time.sleep(startup_interval)
            startup_elapsed += startup_interval
        else:
            logger.error(f"Config server did not become ready within {startup_timeout}s")
            server_process.terminate()
            server_process.join(5)
            raise typer.Exit(code=1)

        logger.info("Config server is ready")

        while server_process.is_alive():
            time.sleep(heartbeat)
    except KeyboardInterrupt:
        logger.info(f"Config server interrupted, shutting down {server_process.pid}")
        if server_process.is_alive():
            server_process.terminate()
            server_process.join(30)
    finally:
        # Ensure the server process is always reaped to avoid zombies.
        if server_process.is_alive():
            logger.info(f"Config server process {server_process.pid} still running at shutdown, terminating")
            server_process.terminate()
        # A second join after earlier joins is safe and ensures the process handle is cleaned up.
        server_process.join(30)


@app.command("stop")
def stop(
    host: str = typer.Option(
        "localhost",
        envvar="PANOPTES_CONFIG_HOST",
        help="Host address of the config server.",
    ),
    port: int = typer.Option(
        6563,
        envvar="PANOPTES_CONFIG_PORT",
        help="Port number of the config server.",
    ),
) -> None:
    """Stop the config server."""

    logger.info(f"Shutting down config server on {host}:{port}")
    set_config("config_server.running", False, host=host, port=port)


@app.command("get")
def config_getter(
    key: str | None = typer.Argument(
        None,
        help="Dotted key to retrieve (e.g. 'location.elevation'). Returns entire config if omitted.",
    ),
    host: str = typer.Option(
        "localhost",
        envvar="PANOPTES_CONFIG_HOST",
        help="Host address of the config server.",
    ),
    port: int = typer.Option(
        6563,
        envvar="PANOPTES_CONFIG_PORT",
        help="Port number of the config server.",
    ),
    default: str | None = typer.Option(None, help="Default value to return if key is not found."),
    parse: bool = typer.Option(True, help="Parse result into a Python object."),
) -> None:
    """Get a config value by dotted key name (e.g. 'location.elevation').

    Returns the entire config if no key is given.
    """

    logger.debug(f"Getting config key={key!r}")
    try:
        config_entry = get_config(key=key, host=host, port=port, parse=parse, default=default)
    except Exception as e:
        logger.error(f"Error while trying to get config: {e!r}")
        print(f"[red]Error while trying to get config: {e!r}[/red]")
        raise typer.Exit(code=1)

    logger.debug(f"Config server response: config_entry={config_entry!r}")
    print(config_entry)


@app.command("set")
def config_setter(
    key: str = typer.Argument(..., help="Dotted key to update (e.g. 'location.elevation')."),
    new_value: str = typer.Argument(..., help="New value to assign."),
    host: str = typer.Option(
        "localhost",
        envvar="PANOPTES_CONFIG_HOST",
        help="Host address of the config server.",
    ),
    port: int = typer.Option(
        6563,
        envvar="PANOPTES_CONFIG_PORT",
        help="Port number of the config server.",
    ),
    parse: bool = typer.Option(True, help="Parse the new value into a Python object."),
) -> None:
    """Set a config value by dotted key name (e.g. 'location.elevation')."""

    logger.debug(f"Setting config key={key!r} new_value={new_value!r} on {host}:{port}")
    config_entry = set_config(key, new_value, host=host, port=port, parse=parse)
    print(config_entry)


if __name__ == "__main__":
    app()
