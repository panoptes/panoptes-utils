"""Typer commands for the config server."""

from __future__ import annotations

import time
from importlib.resources import as_file, files
from pathlib import Path

import typer
from loguru import logger
from rich import print

from panoptes.utils.config import DEFAULT_CONFIG_PATH
from panoptes.utils.config.client import get_config, server_is_running, set_config

app = typer.Typer()


@app.command("init")
def config_init(
    output: Path | None = typer.Option(
        None,
        help="Destination path for the config file. Defaults to ~/.panoptes/config.yaml.",
    ),
    merge_from: Path = typer.Option(
        None,
        "--from",
        help=(
            "Path to an existing config or _local.yaml file whose values are merged "
            "on top of the template. If not given, any *_local.yaml files in the "
            "current directory are detected automatically."
        ),
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite an existing config file."),
) -> None:
    """Create a starter config file at ~/.panoptes/config.yaml.

    Starts from the built-in default template and optionally merges in values
    from an existing config or _local.yaml override file, so your current
    settings are preserved.

    Examples::

        # Plain init — write the template
        panoptes-utils config init

        # Merge an existing override file
        panoptes-utils config init --from pocs_local.yaml

        # Auto-detect *_local.yaml in the current directory and merge
        panoptes-utils config init

        # Write to a custom path
        panoptes-utils config init --output /etc/panoptes/config.yaml
    """
    from panoptes.utils.config import deep_merge
    from panoptes.utils.config.helpers import _add_to_conf

    dest = Path(output) if output else DEFAULT_CONFIG_PATH

    if dest.exists() and not force:
        print(
            f"[yellow]Config file already exists at {dest}.[/yellow]\n"
            f"Use [bold]--force[/bold] to overwrite it."
        )
        raise typer.Exit(code=1)

    # Load template as the base.
    # Use as_file() to materialise a real filesystem path, which is necessary in
    # zipped/wheel installs where Traversable resources are not real file paths.
    template_ref = files("panoptes.utils.config").joinpath("default_config.yaml")
    base_config: dict = {}
    with as_file(template_ref) as template_path:
        _add_to_conf(base_config, template_path, parse=False)

    # Resolve the override source.
    override_path: Path | None = None
    if merge_from:
        override_path = Path(merge_from)
        if not override_path.exists():
            print(f"[red]Override file not found:[/red] {override_path}")
            raise typer.Exit(code=1)
    else:
        # Auto-detect *_local.yaml in the current directory.
        candidates = sorted(Path.cwd().glob("*_local.yaml"))
        if len(candidates) == 1:
            override_path = candidates[0]
            print(f"[dim]Auto-detected override file:[/dim] {override_path}")
        elif len(candidates) > 1:
            names = ", ".join(str(p.name) for p in candidates)
            print(
                f"[yellow]Multiple _local.yaml files found ({names}).[/yellow]\n"
                f"Use [bold]--from <path>[/bold] to specify which one to merge."
            )
            raise typer.Exit(code=1)

    # Merge overrides on top of the template.
    final_config = base_config
    if override_path:
        overrides: dict = {}
        _add_to_conf(overrides, override_path, parse=False)
        final_config = deep_merge(base_config, overrides)
        merged_keys = sorted(overrides.keys())
        print(f"[dim]Merged keys from {override_path.name}:[/dim] {', '.join(merged_keys)}")

    # Write the result.
    dest.parent.mkdir(parents=True, exist_ok=True)
    from panoptes.utils.serializers import to_yaml

    with dest.open("w") as fh:
        to_yaml(final_config, stream=fh)

    print(f"[green]Created config file:[/green] {dest}")
    print("Edit it to match your hardware and location, then set:")
    print(f"  [bold]export PANOPTES_CONFIG_FILE={dest}[/bold]")


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
