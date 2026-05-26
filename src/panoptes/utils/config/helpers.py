import warnings
from contextlib import suppress
from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from panoptes.utils import error
from panoptes.utils.serializers import from_yaml, to_yaml
from panoptes.utils.utils import listify

#: Default user config location, overridden by ``$PANOPTES_CONFIG_FILE``.
DEFAULT_CONFIG_PATH = Path.home() / ".panoptes" / "config.yaml"


def load_config[M: BaseModel](
    config_files: str | Path | list | None = None,
    parse: bool = True,
    load_local: bool = True,
    model: type[M] | None = None,
) -> dict | M:
    """Loads configuration information from one or more YAML files.

    This function is used by the config server; normal config usage should
    be via a running config server.

    If ``config_files`` is ``None``, the path is resolved in this order:

    1. The ``$PANOPTES_CONFIG_FILE`` environment variable (if set).
    2. ``~/.panoptes/config.yaml`` (the standard user config location).
    3. An empty dict with a warning if neither exists.

    Multiple files can be specified and are loaded in order, with later files
    overwriting values from earlier ones.

    .. deprecated::
        The automatic loading of ``<name>_local.yaml`` companion files
        (controlled by ``load_local``) is deprecated.  Place all user
        overrides in ``~/.panoptes/config.yaml`` instead.

    Args:
        config_files (str | Path | List | None, optional): A path or list of paths to config files.
            If None, resolves to ``$PANOPTES_CONFIG_FILE`` or ``~/.panoptes/config.yaml``.
        parse (bool, optional): Whether to parse objects such as dates and astropy units.
            Defaults to True.
        load_local (bool, optional): Whether to load legacy ``<name>_local.yaml`` override
            files if present. Deprecated — will be removed in a future release. Defaults to True.
        model (type[BaseModel] | None, optional): If provided, the loaded config dict is passed
            to ``model.model_validate(config)`` and the model instance is returned instead of
            the raw dict. Defaults to None.

    Returns:
        dict | BaseModel: Dictionary of configuration items, or a validated model instance
            if ``model`` is provided.

    Raises:
        ruamel.yaml.parser.ParserError: If a YAML file cannot be parsed.
        IOError: If a config file cannot be read.
        TypeError: If a config file contains invalid data types.
    """
    import os

    config = dict()

    if config_files is None:
        env_path = os.environ.get("PANOPTES_CONFIG_FILE")
        if env_path:
            env_file = Path(env_path).expanduser()
            if env_file.exists():
                config_files = [env_file]
            else:
                logger.warning(
                    f"$PANOPTES_CONFIG_FILE={env_path!r} does not exist. "
                    f"Check the path and re-run `panoptes-utils config init` if needed."
                )
                config_files = []
        elif DEFAULT_CONFIG_PATH.exists():
            config_files = [DEFAULT_CONFIG_PATH]
        else:
            logger.warning(
                f"No config file found. Set $PANOPTES_CONFIG_FILE or create {DEFAULT_CONFIG_PATH}. "
                f"Run `panoptes-utils config init` to create a starter config."
            )
            config_files = []

    config_files = listify(config_files)
    logger.debug(f"Loading config files: config_files={config_files!r}")
    for config_file in config_files:
        config_file = Path(config_file)
        logger.debug(f"Adding config_file={config_file!r} to config dict")
        _add_to_conf(config, config_file, parse=parse)

        # Legacy _local.yaml support — deprecated.
        if load_local:
            local_version = config_file.parent / Path(config_file.stem + "_local.yaml")
            if local_version.exists():
                warnings.warn(
                    f"Loading {local_version} via the _local.yaml convention is deprecated. "
                    f"Merge your overrides into {DEFAULT_CONFIG_PATH} and set $PANOPTES_CONFIG_FILE. "
                    f"Pass load_local=False to suppress this warning.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                _add_to_conf(config, local_version, parse=parse)

    # parse_config_directories currently only corrects directory names.
    if parse:
        logger.trace(f"Parsing config={config!r}")
        with suppress(KeyError):
            config["directories"] = parse_config_directories(config["directories"])
            logger.trace(f"Config directories parsed: config={config!r}")

    if model is not None:
        return model.model_validate(config)

    return config


def save_config(save_path: Path | None = None, config: dict | None = None, overwrite: bool = True) -> bool:
    """Save config to a YAML file.

    Saves the given config dict to ``save_path``. If ``save_path`` is ``None``,
    the file is written to ``~/.panoptes/config.yaml`` (or ``$PANOPTES_CONFIG_FILE``
    if set).

    .. deprecated::
        Passing a path that ends in ``_local.yaml`` is deprecated.  Use a plain
        config path such as ``~/.panoptes/config.yaml`` instead.

    Args:
        save_path (Path | None, optional): Destination file path. Defaults to
            ``$PANOPTES_CONFIG_FILE`` or ``~/.panoptes/config.yaml``.
        config (dict): Config to save.
        overwrite (bool, optional): True if file should be updated, False
            to generate an error for an existing config. Defaults to True.

    Returns:
        bool: If the save was successful.

    Raises:
         FileExistsError: If the path already exists and ``overwrite=False``.
         ValueError: If ``config`` is ``None``.
    """
    import os

    if config is None:
        raise ValueError("config must be a dict; pass {} explicitly if you intend to write an empty file.")

    if save_path is None:
        env_path = os.environ.get("PANOPTES_CONFIG_FILE")
        save_path = Path(env_path).expanduser() if env_path else DEFAULT_CONFIG_PATH

    save_path = Path(save_path)

    if save_path.stem.endswith("_local"):
        warnings.warn(
            f"Saving to a _local.yaml file ({save_path}) is deprecated. Use {DEFAULT_CONFIG_PATH} instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    if save_path.exists() and overwrite is False:
        raise FileExistsError(f"Path exists and overwrite=False: {save_path}")

    save_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving config to {save_path}")
    with save_path.open("w") as fn:
        to_yaml(config, stream=fn)
    logger.success(f"Config info saved to {save_path}")

    return True


def parse_config_directories(directories: dict[str, str]) -> dict:
    """Parse the config dictionary for common objects.

    Given a `base` entry that corresponds to the absolute path of a directory,
    prepend the `base` to all other relative directory entries.

    The `base` directory must exist or an exception is rasied.

    If the `base` entry is not given the current working directory is used.

    .. doctest::

        >>> dirs_config = dict(base='/tmp', foo='bar', baz='bam', app='/app')
        >>> parse_config_directories(dirs_config)
        {'base': '/tmp', 'foo': '/tmp/bar', 'baz': '/tmp/bam', 'app': '/app'}

        >>> # If base doesn't exist an exception is raised.
        >>> dirs_config = dict(base='/panoptes', foo='bar', baz='bam', app='/app')
        >>> parse_config_directories(dirs_config)
        Traceback (most recent call last):
        ...
        panoptes.utils.error.NotFound: NotFound: Base directory does not exist: /panoptes

    Args:
        directories (dict): The dictionary of directory information. Usually comes
            from the "directories" entry in the config.

    Returns:
        dict: The same directory but with relative directories resolved.

    Raises:
        panoptes.utils.error.NotFound: if the 'base' entry is given but does not exist.
    """
    resolved_dirs = directories.copy()

    # Try to get the base directory first.
    base_dir = Path(resolved_dirs.get("base", ".")).absolute()

    # Warn if base directory does not exist.
    if base_dir.is_dir() is False:
        raise error.NotFound(f"Base directory does not exist: {base_dir}")

    # Add back absolute path for base directory.
    resolved_dirs["base"] = str(base_dir)
    logger.trace(f"Using base_dir={base_dir!r} for setting config directories")

    # Add the base directory to any relative dir.
    for dir_name, dir_path in resolved_dirs.items():
        if dir_path.startswith("/") is False and dir_name != "base":
            sub_dir = (base_dir / dir_path).absolute()

            if sub_dir.exists() is False:
                logger.warning(f"{sub_dir!r} does not exist.")

            logger.trace(f"Setting {dir_name} to {sub_dir}")
            resolved_dirs[dir_name] = str(sub_dir)

    return resolved_dirs


def deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merge *overrides* into *base*, returning a new dict.

    Nested dicts are merged recursively; all other values in *overrides*
    replace those in *base*.

    .. doctest::

        >>> deep_merge({"a": 1, "b": {"x": 10, "y": 20}}, {"b": {"y": 99}, "c": 3})
        {'a': 1, 'b': {'x': 10, 'y': 99}, 'c': 3}

    Args:
        base: The starting dict (e.g. a template config).
        overrides: Values to apply on top of *base*.

    Returns:
        A new dict with *overrides* merged into *base*.
    """
    result = base.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _add_to_conf(config: dict, conf_fn: Path, parse: bool = False) -> None:
    """Add configuration from file to existing config dictionary.

    Args:
        config (dict): Configuration dictionary to update.
        conf_fn (Path): Path to configuration file.
        parse (bool, optional): Whether to parse YAML values. Defaults to False.
    """
    with suppress(IOError, TypeError):
        with conf_fn.open("r") as fn:
            config.update(from_yaml(fn.read(), parse=parse))
