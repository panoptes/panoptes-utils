import time

import typer
from loguru import logger
from rich import print
from rich.console import Console

from panoptes.utils.config import server
from panoptes.utils.config.client import get_config, server_is_running, set_config

err_console = Console(stderr=True)

app = typer.Typer(help="Manage the config server.", rich_markup_mode="rich", no_args_is_help=True)


@app.callback()
def config_callback(
    ctx: typer.Context,
    host: str | None = typer.Option(
        None,
        envvar="PANOPTES_CONFIG_HOST",
        help="The config server IP address or host name. "
        "Checks PANOPTES_CONFIG_HOST env var, then defaults to localhost.",
    ),
    port: int | None = typer.Option(
        None,
        envvar="PANOPTES_CONFIG_PORT",
        help="The config server port. Checks PANOPTES_CONFIG_PORT env var, then defaults to 6563.",
    ),
) -> None:
    """Manage the config server."""
    ctx.ensure_object(dict)

    # Distinguish between the address the server binds to and the address clients use
    # to connect. When binding to 0.0.0.0 (all interfaces) or when no host is set,
    # clients should connect via localhost/127.0.0.1 rather than the wildcard address.
    bind_host = host
    client_host = "localhost" if host in (None, "0.0.0.0") else host

    # For backward compatibility, keep the "host" key pointing at the client host so
    # existing commands that read ctx.obj["host"] will use a connectable address.
    ctx.obj["bind_host"] = bind_host
    ctx.obj["client_host"] = client_host
    ctx.obj["host"] = client_host
    ctx.obj["port"] = port


@app.command("run")
def run(
    ctx: typer.Context,
    config_file: str | None = typer.Option(
        None,
        envvar="PANOPTES_CONFIG_FILE",
        help="The yaml config file to load.",
    ),
    load_local: bool = typer.Option(True, help="Use the local config files when loading."),
    save_local: bool = typer.Option(True, help="Save set values to the local file."),
    heartbeat: int = typer.Option(2, help="Heartbeat interval in seconds."),
    startup_timeout: int = typer.Option(
        30, help="Seconds to wait for the server to become ready before giving up."
    ),
) -> None:
    """Run the config server."""
    ctx.ensure_object(dict)

    # Prefer the explicitly stored bind/client hosts, falling back to "host" for
    # compatibility with older contexts.
    bind_host = ctx.obj.get("bind_host", ctx.obj.get("host"))
    client_host = ctx.obj.get("client_host", "localhost" if bind_host in (None, "0.0.0.0") else bind_host)
    port = ctx.obj.get("port")

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
        return

    try:
        print("Starting config server. [bold]Ctrl-c[/bold] to stop")
        server_process.start()
        print(
            f"Config server started on [bold]pid={server_process.pid!r}[/bold]. "
            f'Set [italic]"config_server.running=False"[/italic] or [bold]Ctrl-c[/bold] to stop'
        )

        # Wait for the server to become reachable before entering the monitor loop.
        # uvicorn takes a moment to bind its socket after the process is forked.
        logger.info(f"Waiting for config server to be ready on {client_host}:{port}")
        startup_elapsed = 0.0
        startup_interval = 0.5
        while startup_elapsed < startup_timeout:
            if server_is_running(host=client_host, port=port):
                break
            time.sleep(startup_interval)
            startup_elapsed += startup_interval
        else:
            logger.error(f"Config server did not become ready within {startup_timeout}s")
            server_process.terminate()
            server_process.join(5)
            return

        logger.info("Config server is ready")

        # Loop until the server signals it is no longer running.
        while server_is_running(host=client_host, port=port):
            time.sleep(heartbeat)

        server_process.terminate()
        server_process.join(30)
    except KeyboardInterrupt:
        logger.info(f"Config server interrupted, shutting down {server_process.pid}")
        server_process.terminate()
    except Exception as e:
        logger.error(f"Unable to start config server {e!r}")


@app.command("stop")
def stop(ctx: typer.Context) -> None:
    """Stop the config server."""
    ctx.ensure_object(dict)
    host = ctx.obj.get("host")
    port = ctx.obj.get("port")
    logger.info(f"Shutting down config server on {host}:{port}")
    set_config("config_server.running", False, host=host, port=port)


@app.command("get")
def config_get(
    ctx: typer.Context,
    key: str | None = typer.Argument(
        None, help="Config key in dotted notation (e.g. 'location.elevation'). Returns all config if omitted."
    ),
    default: str | None = typer.Option(None, help="The default to return if no key is found."),
    parse: bool = typer.Option(True, help="Parse the result into an object."),
) -> None:
    """Get an item from the config server by key name.

    Uses dotted notation (e.g. 'location.elevation'). If no key is given, returns the entire config.
    """
    ctx.ensure_object(dict)
    host = ctx.obj.get("host")
    port = ctx.obj.get("port")
    logger.debug(f"Getting config key={key!r}")
    try:
        config_entry = get_config(key=key, host=host, port=port, parse=parse, default=default)
    except Exception as e:
        logger.error(f"Error while trying to get config: {e!r}")
        err_console.print(f"[red]Error while trying to get config: {e!r}[/red]")
    else:
        logger.debug(f"Config server response: config_entry={config_entry!r}")
        print(config_entry)


@app.command("set")
def config_set(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Config key in dotted notation."),
    new_value: str = typer.Argument(..., help="New value to set."),
    parse: bool = typer.Option(True, help="Parse the result into an object."),
) -> None:
    """Set an item in the config server."""
    ctx.ensure_object(dict)
    host = ctx.obj.get("host")
    port = ctx.obj.get("port")
    logger.debug(f"Setting config key={key!r} new_value={new_value!r} on {host}:{port}")
    config_entry = set_config(key, new_value, host=host, port=port, parse=parse)
    print(config_entry)


if __name__ == "__main__":
    app()
