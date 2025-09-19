from contextlib import suppress
from pathlib import Path
from typing import Dict, List

from loguru import logger

from panoptes.utils import error
from panoptes.utils.serializers import from_yaml
from panoptes.utils.serializers import to_yaml
from panoptes.utils.utils import listify


def load_config(
    config_files: str | Path | List | None = None, parse: bool = True, load_local: bool = True
) -> dict:
    """Loads configuration information from one or more YAML files.

    This function is used by the config server; normal config usage should
    be via a running config server.

    If no options are passed to `config_files`, the default `$PANOPTES_CONFIG_FILE`
    will be loaded. Multiple files can be specified and are loaded in order,
    with later files overwriting values from earlier ones. Local versions of files
    (named `<name>_local.yaml`) can override built-in versions if present.

    Args:
        config_files (str | Path | List | None, optional): A path or list of paths to config files.
            If None, uses the default config file. Files are loaded in order.
        parse (bool, optional): Whether to parse objects such as dates and astropy units.
            Defaults to True.
        load_local (bool, optional): Whether to load local override files (ending with `_local.yaml`)
            if present. Defaults to True.

    Returns:
        dict: Dictionary of configuration items.

    Raises:
        ruamel.yaml.parser.ParserError: If a YAML file cannot be parsed.
        IOError: If a config file cannot be read.
        TypeError: If a config file contains invalid data types.

    Notes:
        Local files are automatically loaded if they exist alongside the specified config path.
        Local files can be ignored by setting `load_local=False`.
    """
    config = dict()

    config_files = listify(config_files)
    logger.debug(f"Loading config files: config_files={config_files!r}")
    for config_file in config_files:
        config_file = Path(config_file)
        logger.debug(f"Adding config_file={config_file!r} to config dict")
        _add_to_conf(config, config_file, parse=parse)

        # Load local version of config
        if load_local:
            local_version = config_file.parent / Path(config_file.stem + "_local.yaml")
            if local_version.exists():
                _add_to_conf(config, local_version, parse=parse)

    # parse_config_directories currently only corrects directory names.
    if parse:
        logger.trace(f"Parsing config={config!r}")
        with suppress(KeyError):
            config["directories"] = parse_config_directories(config["directories"])
            logger.trace(f"Config directories parsed: config={config!r}")

    return config


def save_config(save_path: Path, config: dict, overwrite: bool = True) -> bool:
    """Save config to local yaml file.

    Args:
        save_path (str): Path to save, can be relative or absolute. See Notes in
            ``load_config``.
        config (dict): Config to save.
        overwrite (bool, optional): True if file should be updated, False
            to generate a warning for existing config. Defaults to True
            for updates.

    Returns:
        bool: If the save was successful.

    Raises:
         FileExistsError: If the local path already exists and ``overwrite=False``.
    """
    # Make sure it's a path.
    save_path = Path(save_path)

    # Make sure ends with '_local.yaml'.
    if save_path.stem.endswith("_local") is False:
        save_path = save_path.with_name(save_path.stem + "_local.yaml")

    if save_path.exists() and overwrite is False:
        raise FileExistsError(f"Path exists and overwrite=False: {save_path}")
    else:
        # Create directory if it does not exist.
        save_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving config to {save_path}")
        with save_path.open("w") as fn:
            to_yaml(config, stream=fn)
        logger.success(f"Config info saved to {save_path}")

    return True


def parse_config_directories(directories: Dict[str, str]) -> dict:
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
