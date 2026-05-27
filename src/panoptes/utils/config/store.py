"""Module-level in-memory config store for PANOPTES.

Provides :func:`get_config` and :func:`set_config` as a lightweight alternative to
the HTTP config server.  Config is loaded from a YAML file once at startup (or on
demand) and held in a process-level dict.

This is the preferred approach for any PANOPTES component that does not need to
share live config updates over the network.  For cross-process config broadcasting
see :mod:`panoptes.utils.config.server` and :mod:`panoptes.utils.config.watcher`.

Typical usage::

    from panoptes.utils.config.store import get_config, set_config, init_config

    init_config("~/.panoptes/config.yaml")

    lat = get_config("location.latitude")
    set_config("location.horizon", "30 deg")
    cameras = get_config("cameras.devices[0].model")

"""

import re
from pathlib import Path
from typing import Any

from loguru import logger

from panoptes.utils.config.helpers import load_config as _load_config_file
from panoptes.utils.config.helpers import save_config as _save_config

_CONFIG: dict[str, Any] = {}
_CONFIG_FILE: Path | None = None


def _get_nested(d: dict[str, Any], key: str, default: Any = None) -> Any:
    """Navigate a nested dict using dotted-key notation.

    Supports list-index syntax, e.g. ``"cameras.devices[0].model"``.

    Args:
        d: The dict to navigate.
        key: Dotted key, optionally with ``[N]`` list-index suffixes.
        default: Value returned when the key path is not found.

    Returns:
        The value at ``key``, or *default* if any step of the path is missing.
    """
    if not key:
        return d

    current: Any = d
    for part in key.split("."):
        if not isinstance(current, dict):
            return default

        if match := re.fullmatch(r"([^\[\]]+)(\[(-?\d+)\])?", part):
            name = match.group(1)
            index = match.group(3)
        else:  # pragma: no cover — every non-empty string matches
            name = part
            index = None

        if name not in current:
            return default

        current = current[name]

        if index is not None:
            if not isinstance(current, list):
                return default
            try:
                current = current[int(index)]
            except (IndexError, ValueError):
                return default

    return current


def _set_nested(d: dict[str, Any], keys: list[str], value: Any) -> None:
    """Set a leaf value in a nested dict, creating intermediate dicts as needed.

    Args:
        d: The top-level dict to update (mutated in-place).
        keys: Key path as a list of strings (result of ``key.split(".")``)
        value: The value to store at the leaf.
    """
    for key in keys[:-1]:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


def init_config(config_file: str | Path | None = None) -> dict[str, Any]:
    """Load config from a YAML file and initialise the module-level store.

    If *config_file* is ``None`` the path is resolved by
    :func:`panoptes.utils.config.helpers.load_config` in the following order:

    1. The ``$PANOPTES_CONFIG_FILE`` environment variable (if set).
    2. ``~/.panoptes/config.yaml``.

    Args:
        config_file: Path to a YAML config file. Passing ``None`` re-uses the
            previously configured path (or falls back to env-var / default).

    Returns:
        The loaded config dict.
    """
    global _CONFIG, _CONFIG_FILE
    if config_file is not None:
        _CONFIG_FILE = Path(config_file).expanduser()
    _CONFIG = _load_config_file(_CONFIG_FILE, load_local=False)
    logger.debug(f"Config initialised from {_CONFIG_FILE!r}")
    return _CONFIG


def reload_config() -> dict[str, Any]:
    """Reload config from the same file used by :func:`init_config`.

    Returns:
        The refreshed config dict.
    """
    return init_config(_CONFIG_FILE)


def get_config(key: str | None = None, default: Any = None, **kwargs) -> Any:
    """Get a config value by dotted-key name.

    If the store has not been initialised yet, :func:`init_config` is called
    automatically using the default file resolution.

    Args:
        key: Dotted key, e.g. ``"location.latitude"`` or
            ``"cameras.devices[0].model"``. Pass ``None`` (the default) to
            return the entire config dict.
        default: Value to return when *key* is not found.
        **kwargs: Accepted but ignored — present for drop-in compatibility with
            the old HTTP config-client signature.

    Returns:
        The config value, or *default* if *key* is not found.
    """
    del kwargs
    if not _CONFIG:
        init_config()
    if key is None:
        return _CONFIG
    value = _get_nested(_CONFIG, key, default)
    logger.trace(f"get_config {key!r} -> {value!r}")
    return value


def set_config(key: str, new_value: Any, persist: bool = True, **kwargs) -> Any:
    """Set a config value by dotted-key name.

    Updates the in-memory store. When *persist* is ``True`` (the default) the
    change is also written back to the config file that was passed to
    :func:`init_config`, preserving backward compatibility with the old HTTP
    client which persisted changes to the server by default.

    Args:
        key: Dotted key, e.g. ``"location.latitude"``.
        new_value: The value to store.
        persist: Write the updated config back to disk. Defaults to ``True``.
        **kwargs: Accepted but ignored — present for drop-in compatibility with
            the old HTTP config-client signature.

    Returns:
        *new_value* as stored (mirrors the old HTTP client behaviour).
    """
    del kwargs
    global _CONFIG
    if not _CONFIG:
        init_config()
    _set_nested(_CONFIG, key.split("."), new_value)
    logger.trace(f"set_config {key!r} = {new_value!r}")
    if persist:
        _save_config(_CONFIG_FILE, _CONFIG)
        logger.trace(f"set_config persisted to {_CONFIG_FILE!r}")
    return new_value
