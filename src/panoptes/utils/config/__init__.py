import os
from contextlib import suppress

from ..logging import logger
from ..utils import listify
from ..serializers import from_yaml
from ..serializers import to_yaml


def load_config(config_files=None, parse=True, ignore_local=False):
    """Load configuration information

    This function supports loading of a number of different files. If no options
    are passed to ``config_files`` then the default ``$PANDIR/conf_files/pocs.yaml``
    will be loaded. See Notes for additional information.

    The ``config_files`` parameter supports a number of options:

        * ``config_files`` is a list and loaded in order, so the second entry will overwrite any values specified by similarly named keys in the first entry.
        * Entries can be placed in the ``$PANDIR/conf_files`` folder and should be passed as just the file name, e.g. ``['weather.yaml', 'email']`` for loading ``$PANDIR/conf_files/weather.yaml`` and ``$PANDIR/conf_files/email.yaml``.
        * The ``.yaml`` extension will be added if not present, so list can be written as just ``['weather', 'email']``.
        * ``config_files`` can also be specified by an absolute path, which can exist anywhere on the filesystem.
        * Local versions of files can override built-in versions and are automatically loaded if placed in the ``$PANDIR/conf_files`` folder. The files have a ``<>_local.yaml`` name, where ``<>`` is the built-in file. So a ``$PANDIR/conf_files/pocs_local.yaml`` will override any setting in the default ``pocs.yaml`` file.
        * Local files can be ignored (mostly for testing purposes) with the ``ignore_local`` parameter.

    Args:
        config_files (list, optional): A list of files to load as config,
            see Notes for details of how to specify files.
        parse (bool, optional): If the config file should attempt to create
            objects such as dates, astropy units, etc.
        ignore_local (bool, optional): If local files should be ignored, see
            Notes for details.

    Returns:
        dict: A dictionary of config items
    """

    # Default to the pocs.yaml file
    if config_files is None:
        config_files = ['pocs']
    config_files = listify(config_files)

    config = dict()

    config_dir = os.path.expandvars('{$PANDIR}/conf_files')

    for config_file in config_files:
        if not config_file.endswith('.yaml'):
            config_file = f'{config_file}.yaml'

        if not config_file.startswith('/'):
            path = os.path.join(config_dir, config_file)
        else:
            path = config_file

        try:
            _add_to_conf(config, path, parse=parse)
        except Exception as e:  # pragma: no cover
            logger.warning(f"Problem with config file {path}, skipping. {e!r}")

        # Load local version of config
        if ignore_local is False:
            local_version = os.path.join(config_dir, config_file.replace('.', '_local.'))
            if os.path.exists(local_version):
                try:
                    _add_to_conf(config, local_version, parse=parse)
                except Exception as e:  # pragma: no cover
                    logger.warning(f"Problem with local config file {local_version}, skipping: {e!r}")

    # parse_config currently only corrects directory names.
    if parse:
        config = parse_config(config)

    return config


def save_config(path, config, overwrite=True):
    """Save config to local yaml file.

    This will save any entries into the ``$PANDIR/conf_files/<path>_local.yaml`` file to avoid
    clobbering what comes from the version control.

    Args:
        path (str): Path to save, can be relative or absolute. See Notes in ``load_config``.
        config (dict): Config to save.
        overwrite (bool, optional): True if file should be updated, False
            to generate a warning for existing config. Defaults to True
            for updates.
    """
    # Make sure ends with '_local.yaml'
    base, ext = os.path.splitext(path)

    # Always want .yaml (although not actually used).
    ext = '.yaml'

    # Check for _local name.
    if not base.endswith('_local'):
        base = f'{base}_local'

    # Check full path location
    if not base.startswith('/'):
        base = os.path.join(os.environ['PANDIR'], 'conf_files', base)

    full_path = f'{base}{ext}'

    if os.path.exists(full_path) and overwrite is False:
        logger.warning(f"Path exists and overwrite=False: {full_path}")
    else:
        # Create directory if does not exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        logger.info(f'Saving config to {full_path}')
        with open(full_path, 'w') as f:
            to_yaml(config, stream=f)

    logger.info(f'Config saved.')


def parse_config(config):
    """Parse the config dictionary for common objects.

    Currently only parses the following:
        * `directories` for relative path names.

    Args:
        config (dict): Config items.

    Returns:
        dict: Config items but with objects.
    """
    base_dir = os.getenv('PANDIR')
    with suppress(KeyError):
        for dir_name, rel_dir in config['directories'].items():
            abs_dir = os.path.normpath(os.path.join(base_dir, rel_dir))
            if abs_dir != rel_dir:
                config['directories'][dir_name] = abs_dir

    return config


def _add_to_conf(config, conf_fn, parse=False):
    with suppress(IOError, TypeError):
        with open(conf_fn, 'r') as fn:
            config.update(from_yaml(fn, parse=parse))
