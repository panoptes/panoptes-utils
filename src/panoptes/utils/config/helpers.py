import os
from contextlib import suppress

from ..logging import logger
from ..utils import listify
from ..serializers import from_yaml
from ..serializers import to_yaml


def load_config(config_files=None, parse=True, ignore_local=False):
    """Load configuration information.

    .. note::

        This function is used by the config server and normal config usage should
        be via a running config server.

    This function supports loading of a number of different files. If no options
    are passed to ``config_files`` then the default ``$PANDIR/conf_files/pocs.yaml``
    will be loaded.

    ``config_files`` is a list and loaded in order, so the second entry will overwrite
    any values specified by similarly named keys in the first entry.

    ``config_files`` should be specified by an absolute path, which can exist anywhere
    on the filesystem.

    Local versions of files can override built-in versions and are automatically loaded if
    they exist alongside the specified config path. Local files have a ``<>_local.yaml`` name, where
    ``<>`` is the built-in file.

    Given the following path:

    ::

        /path/to/dir
        |- my_conf.yaml
        |- my_conf_local.yaml

    You can do a ``load_config('/path/to/dir/my_conf.yaml')`` and both versions of the file will
    be loaded, with the values in the local file overriding the non-local. Typically the local
    file would also be ignored by ``git``, etc.

    For example, the ``panoptes.utils.config.server.config_server`` will always save values to
    a local version of the file so the default settings can always be recovered if necessary.

    Local files can be ignored (mostly for testing purposes or for recovering default values)
    with the ``ignore_local`` parameter.

    Args:
        config_files (list, optional): A list of files to load as config,
            see Notes for details of how to specify files.
        parse (bool, optional): If the config file should attempt to create
            objects such as dates, astropy units, etc.
        ignore_local (bool, optional): If local files should be ignored, see
            Notes for details.

    Returns:
        dict: A dictionary of config items.
    """
    config = dict()

    config_files = listify(config_files)
    logger.debug(f'Loading config files: {config_files=}')
    for config_file in config_files:
        try:
            logger.debug(f'Adding {config_file=} to config dict')
            _add_to_conf(config, config_file, parse=parse)
        except Exception as e:  # pragma: no cover
            logger.warning(f"Problem with {config_file=}, skipping. {e!r}")

        # Load local version of config
        if ignore_local is False:
            local_version = config_file.replace('.', '_local.')
            if os.path.exists(local_version):
                try:
                    _add_to_conf(config, local_version, parse=parse)
                except Exception as e:  # pragma: no cover
                    logger.warning(
                        f"Problem with local config file {local_version}, skipping: {e!r}")

    # parse_config_directories currently only corrects directory names.
    if parse:
        logger.trace(f'Parsing {config=}')
        try:
            config['directories'] = parse_config_directories(config['directories'])
        except Exception as e:
            logger.warning(f'Unable to parse config: {e=}')
        else:
            logger.trace(f'Config directories parsed: {config=}')

    return config


def save_config(path, config, overwrite=True):
    """Save config to local yaml file.

    Args:
        path (str): Path to save, can be relative or absolute. See Notes in ``load_config``.
        config (dict): Config to save.
        overwrite (bool, optional): True if file should be updated, False
            to generate a warning for existing config. Defaults to True
            for updates.

    Returns:
        bool: If the save was successful.

    Raises:
         FileExistsError: If the local path already exists and ``overwrite=False``.
    """
    # Make sure ends with '_local.yaml'
    base, ext = os.path.splitext(path)

    # Always want .yaml (although not actually used).
    ext = '.yaml'

    # Check for _local name.
    if not base.endswith('_local'):
        base = f'{base}_local'

    full_path = f'{base}{ext}'

    if os.path.exists(full_path) and overwrite is False:
        raise FileExistsError(f"Path exists and overwrite=False: {full_path}")
    else:
        # Create directory if does not exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        logger.info(f'Saving config to {full_path}')
        with open(full_path, 'w') as f:
            to_yaml(config, stream=f)
        logger.success(f'Config info saved to {full_path}')

    return True


def parse_config_directories(directories, must_exist=False):
    """Parse the config dictionary for common objects.

    Given a `base` entry that corresponds to the absolute path of a directory,
    prepend the `base` to all other relative directory entries.

    If `must_exist=True`, then only update entry if the corresponding
    directory exists on the filesystem.

    .. doctest::

        >>> dirs_config = dict(base='/var/panoptes', foo='bar', baz='bam')
        >>> # If the relative dir doesn't exist but is required, return as is.
        >>> parse_config_directories(dirs_config, must_exist=True)
        {'base': '/var/panoptes', 'foo': 'bar', 'baz': 'bam'}

        >>> # Default is to return anyway.
        >>> parse_config_directories(dirs_config)
        {'base': '/var/panoptes', 'foo': '/var/panoptes/bar', 'baz': '/var/panoptes/bam'}

        >>> # If 'base' is not a valid absolute directory, return all as is.
        >>> dirs_config = dict(base='panoptes', foo='bar', baz='bam')
        >>> parse_config_directories(dirs_config, must_exist=False)
        {'base': 'panoptes', 'foo': 'bar', 'baz': 'bam'}

    Args:
        directories (dict): The dictionary of directory information. Usually comes
            from the "directories" entry in the config.
        must_exist (bool): Only parse directory if it exists on the filesystem,
            default False.

    Returns:
        dict: The same directory but with relative directories resolved.
    """

    # Try to get the base directory first.
    base_dir = directories.get('base', os.environ['PANDIR'])
    if os.path.isdir(base_dir):
        logger.trace(f'Using {base_dir=} for setting config directories')

        # Add the base directory to any relative dir.
        for dir_name, rel_dir in directories.items():
            # Only want relative directories.
            if rel_dir.startswith('/') is False:
                abs_dir = os.path.join(base_dir, rel_dir)
                logger.trace(f'{base_dir=} {rel_dir=} {abs_dir=} {must_exist=}')

                if must_exist and not os.path.exists(abs_dir):
                    logger.warning(f'{must_exist=} but {abs_dir=} does not exist, skipping')
                else:
                    logger.trace(f'Setting {dir_name} to {abs_dir}')
                    directories[dir_name] = abs_dir

    return directories


def _add_to_conf(config, conf_fn, parse=False):
    with suppress(IOError, TypeError):
        with open(conf_fn, 'r') as fn:
            config.update(from_yaml(fn.read(), parse=parse))
