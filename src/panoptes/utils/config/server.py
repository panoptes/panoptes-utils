import logging
import os
from multiprocessing import Process
from sys import platform

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger
from ruamel.yaml.parser import ParserError
from scalpl import Cut

from panoptes.utils.config.helpers import load_config, save_config

# Platform-specific multiprocessing setup.
if platform == "darwin" or platform == "win32":
    import multiprocessing

    try:
        multiprocessing.set_start_method("fork")
    except RuntimeError:
        pass

# Suppress noisy uvicorn logging by default.
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

app = FastAPI()

# Module-level mutable state, set in config_server() before the subprocess is forked.
# Each subprocess inherits a copy of this state (via fork) and owns it independently.
# Note: config_server() should not be called concurrently, as concurrent calls could
# race on these module-level variables before the subprocess forks.
_pocs_config: dict = {}
_pocs_cut: Cut | None = None
_server_config: dict = {
    "config_file": None,
    "save_local": False,
    "load_local": True,
}


def config_server(
    config_file,
    host=None,
    port=None,
    load_local=True,
    save_local=False,
    auto_start=True,
    access_logs=None,
    error_logs="logger",
):
    """Start the config server in a separate process.

    A convenience function to start the config server.

    Args:
        config_file (str or None): The absolute path to the config file to load.
        host (str, optional): The config server host. First checks for PANOPTES_CONFIG_HOST
            env var, defaults to 'localhost'.
        port (str or int, optional): The config server port. First checks for
            PANOPTES_CONFIG_PORT env var, defaults to 6563.
        load_local (bool, optional): If local config files should be used when loading,
            default True.
        save_local (bool, optional): If setting new values should auto-save to local file,
            default False.
        auto_start (bool, optional): If server process should be started automatically,
            default True.
        access_logs (bool or None, optional): Controls uvicorn access logs. ``True`` enables
            them; the default ``None``/``False`` turns them off.
        error_logs: Unused; kept for backward compatibility.

    Returns:
        multiprocessing.Process: The process running the config server.
    """
    global _pocs_config, _pocs_cut, _server_config

    logger.info(f"Starting panoptes-config-server with config_file={config_file!r}")
    try:
        config = load_config(config_files=config_file, load_local=load_local, parse=False)
    except ParserError as e:
        logger.error(f"Problem parsing config file {config_file}: {e!r}")
        raise e

    logger.success(f"Config server loaded {len(config)} top-level items")

    # Add an entry to control running of the server.
    config["config_server"] = dict(running=True)

    logger.success(f"{config!r}")

    # Populate module-level state before forking so the child inherits it.
    _pocs_config = config
    _pocs_cut = Cut(config)
    _server_config = {
        "config_file": config_file,
        "save_local": save_local,
        "load_local": load_local,
    }
    logger.info("Config items saved to server state")

    host = host or os.getenv("PANOPTES_CONFIG_HOST", "localhost")
    port = int(port or os.getenv("PANOPTES_CONFIG_PORT", 6563))

    enable_access_log = bool(access_logs)

    def start_server(host: str = "localhost", port: int = 6563) -> None:
        """Start the FastAPI config server with uvicorn.

        This function blocks indefinitely while the server is running.
        It only returns (with ``None``) if the server fails to start due
        to an OS-level error or other exception before uvicorn takes control.

        Args:
            host (str): Host address to bind to. Defaults to "localhost".
            port (int): Port number to bind to. Defaults to 6563.
        """
        try:
            logger.info(f"Starting panoptes config server with {host}:{port}")
            uvicorn.run(
                app,
                host=host,
                port=int(port),
                log_level="warning",
                access_log=enable_access_log,
            )
        except OSError:
            logger.warning("Problem starting config server, is another config server already running?")
            return None
        except Exception as e:
            logger.warning(f"Problem starting config server: {e!r}")
            return None

    cmd_kwargs = dict(host=host, port=port)
    logger.debug(f"Setting up config server process with  cmd_kwargs={cmd_kwargs!r}")
    server_process = Process(target=start_server, daemon=True, kwargs=cmd_kwargs)

    if auto_start:
        server_process.start()

    return server_process


@app.api_route("/heartbeat", methods=["GET", "POST"])
async def heartbeat(request: Request) -> JSONResponse:
    """A simple echo service to be used for a heartbeat.

    Defaults to looking for the 'config_server.running' bool value, although a
    different ``key`` can be specified in the request body.
    """
    params: dict = {}
    if request.method == "POST":
        try:
            params = await request.json()
        except Exception:
            params = {}
    else:
        params = dict(request.query_params)

    key = params.get("key", "config_server.running")
    if key is None:
        key = "config_server.running"

    is_running = _pocs_cut.get(key, False) if _pocs_cut is not None else False
    return JSONResponse(content=is_running)


@app.api_route("/get-config", methods=["GET", "POST"])
async def get_config_entry(request: Request) -> JSONResponse:
    """Get config entries from server.

    Endpoint that responds to GET and POST requests and returns
    configuration item corresponding to provided key or entire
    configuration. The key entries should be specified in dot-notation,
    with the names corresponding to the entries stored in the configuration
    file. See the `scalpl <https://pypi.org/project/scalpl/>`_ documentation
    for details on the dot-notation.

    The endpoint should receive a JSON document with a single key named ``"key"``
    and a value that corresponds to the desired key within the configuration.

    For example, take the following configuration:

    .. code:: javascript

        {
            'location': {
                'elevation': 3400.0,
                'latitude': 19.55,
                'longitude': 155.12,
            }
        }

    To get the corresponding value for the elevation, pass a JSON document similar to:

    .. code:: javascript

        '{"key": "location.elevation"}'

    Returns:
        str: The json string for the requested object if object is found in config.
        Otherwise a json string with ``status`` and ``msg`` keys will be returned.
    """
    params: dict = {}
    is_json = False

    if request.method == "POST":
        try:
            params = await request.json()
            is_json = True
        except Exception:
            params = {}
            is_json = False
    else:
        params = dict(request.query_params)
        is_json = bool(params)

    verbose = params.get("verbose", True)
    log_level = "DEBUG" if verbose else "TRACE"

    logger.log(log_level, f"Received  params={params!r}")

    if is_json:
        try:
            key = params["key"]
            logger.log(log_level, f"Request contains  key={key!r}")
        except KeyError:
            return JSONResponse(
                {
                    "success": False,
                    "msg": "No valid key found. Need json request: {'key': <config_entry>}",
                }
            )

        if key is None:
            logger.log(log_level, "No valid key given, returning entire config")
            show_config = _pocs_config
        else:
            try:
                logger.log(log_level, f"Looking for  key={key!r} in config")
                show_config = _pocs_cut.get(key, None) if _pocs_cut is not None else None
            except Exception as e:
                logger.error(f"Error while getting config item: {e!r}")
                show_config = None
    else:
        logger.log(log_level, "No valid key given, returning entire config")
        show_config = _pocs_config

    logger.log(log_level, f"Returning  show_config={show_config!r}")
    return JSONResponse(show_config)


@app.api_route("/set-config", methods=["GET", "POST"])
async def set_config_entry(request: Request) -> JSONResponse:
    """Sets an item in the config.

    Endpoint that responds to GET and POST requests and sets a
    configuration item corresponding to the provided key.

    The key entries should be specified in dot-notation, with the names
    corresponding to the entries stored in the configuration file. See
    the `scalpl <https://pypi.org/project/scalpl/>`_ documentation for details
    on the dot-notation.

    The endpoint should receive a JSON document with a single key named ``"key"``
    and a value that corresponds to the desired key within the configuration.

    For example, take the following configuration:

    .. code:: javascript

        {
            'location': {
                'elevation': 3400.0,
                'latitude': 19.55,
                'longitude': 155.12,
            }
        }

    To set the corresponding value for the elevation, pass a JSON document similar to:

    .. code:: javascript

        '{"location.elevation": "1000 m"}'


    Returns:
        str: If method is successful, returned json string will be a copy of the set values.
        On failure, a json string with ``status`` and ``msg`` keys will be returned.
    """
    params: dict | None = None

    if request.method == "POST":
        try:
            params = await request.json()
        except Exception:
            params = None
    else:
        raw = dict(request.query_params)
        params = raw if raw else None

    if params is None:
        return JSONResponse(
            {
                "success": False,
                "msg": "Invalid. Need json request: {'key': <config_entry>, 'value': <new_values>}",
            }
        )

    if _pocs_cut is not None:
        try:
            _pocs_cut.update(params)
        except KeyError:
            for k, v in params.items():
                _pocs_cut.setdefault(k, v)

    save_local = _server_config.get("save_local", False)
    logger.info(f"Setting config  save_local={save_local!r}")
    if save_local and _server_config.get("config_file") is not None:
        if _pocs_cut is None:
            logger.error("Configuration state is uninitialized; cannot save config entry to disk.")
            return JSONResponse(
                {
                    "success": False,
                    "msg": "Configuration state is not initialized; unable to save configuration.",
                },
                status_code=500,
            )
        save_config(_server_config["config_file"], _pocs_cut.copy())

    return JSONResponse(params)


@app.post("/reset-config")
async def reset_config(request: Request) -> JSONResponse:
    """Reset the configuration.

    An endpoint that accepts a POST method. The json request object
    must contain the key ``reset`` (with any value).

    The method will reset the configuration to the original configuration files that were
    used, skipping the local (and saved file).

    .. note::

        If the server was originally started with a local version of the file, those will
        be skipped upon reload. This is not ideal but hopefully this method is not used too
        much.

    Returns:
        str: A json string object containing the keys ``success`` and ``msg`` that indicate
        success or failure.
    """
    global _pocs_config, _pocs_cut

    try:
        params = await request.json()
    except Exception:
        params = {}

    logger.warning("Resetting config server")

    if params.get("reset"):
        try:
            config = load_config(
                config_files=_server_config["config_file"],
                load_local=_server_config.get("load_local", True),
                parse=params.get("parse", False),
            )
        except ParserError as e:
            logger.error(f"Problem parsing config file {_server_config['config_file']}: {e!r}")
            return JSONResponse({"success": False, "msg": f"Problem parsing config file: {e!r}"})

        # Add an entry to control running of the server.
        config["config_server"] = dict(running=True)
        _pocs_config = config
        _pocs_cut = Cut(config)
    else:
        return JSONResponse({"success": False, "msg": "Invalid. Need json request: {'reset': True}"})

    return JSONResponse({"success": True, "msg": "Configuration reset"})
