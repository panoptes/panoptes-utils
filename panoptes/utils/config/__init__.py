import os
from contextlib import suppress
from warnings import warn

from ..logger import logger
from ..utils import listify
from ..serializers import from_yaml
from ..serializers import to_yaml


def load_config(config_files=None, simulator=None, parse=True, ignore_local=False):
    """Load configuation information

    This function supports loading of a number of different files. If no options
    are passed to `config_files` then the default `$PANDIR/conf_files/pocs.yaml`
    will be loaded. See Notes for additional information.

    .. note::

        The `config_files` parameter supports a number of options:
        * `config_files` is a list and loaded in order, so the first entry
            will have any values overwritten by similarly named keys in
            the second entry.
        * Entries can be placed in the `$PANDIR/conf_files` folder and
            should be passed as just the file name, e.g.
            [`weather.yaml`, `email.yaml`] for loading
            `$PANDIR/conf_files/weather.yaml` and `$PANDIR/conf_files/email.yaml`
        * The `.yaml` extension will be added if not present, so list can
            be written as just ['weather', 'email'].
        * `config_files` can also be specified by an absolute path, which
            can exist anywhere on the filesystem.
        * Local versions of files can override built-in versions and are
            automatically loaded if placed in the `$PANDIR/conf_files` folder.
            The files have a `<>_local.yaml` name, where `<>` is the built-in
            file. So a `$PANDIR/conf_files/pocs_local.yaml` will override any
            setting in the default `pocs.yaml` file.
        * Local files can be ignored (mostly for testing purposes) with the
            `ignore_local` parameter.

    Args:
        config_files (list, optional): A list of files to load as config,
            see Notes for details of how to specify files.
        simulator (list, optional): A list of hardware items that should be
            used as a simulator.
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

    config_dir = '{}/conf_files'.format(os.getenv('PANDIR'))

    for f in config_files:
        if not f.endswith('.yaml'):
            f = '{}.yaml'.format(f)

        if not f.startswith('/'):
            path = os.path.join(config_dir, f)
        else:
            path = f

        try:
            _add_to_conf(config, path, parse=parse)
        except Exception as e:
            warn(f"Problem with config file {path}, skipping. {e}")

        # Load local version of config
        if ignore_local is False:
            local_version = os.path.join(config_dir, f.replace('.', '_local.'))
            if os.path.exists(local_version):
                try:
                    _add_to_conf(config, local_version, parse=parse)
                except Exception:
                    warn(f"Problem with local config file {local_version}, skipping")

    # parse_config currently only corrects directory names.
    if parse:
        config = parse_config(config)

    return config


def save_config(path, config, overwrite=True):
    """Save config to local yaml file.

    This will save any entries into the `$PANDIR/conf_files/<path>_local.yaml` file to avoid
    clobbering what comes from the version control.

    Args:
        path (str): Path to save, can be relative or absolute. See Notes
            in `load_config`.
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
        config_dir = os.path.join(os.environ['PANDIR'], 'conf_files')
        base = os.path.join(config_dir, base)

    full_path = f'{base}{ext}'

    if os.path.exists(full_path) and overwrite is False:
        logger.warning(f"Path exists and overwrite=False: {full_path}")
    else:
        # Create directory if does not exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            print(config)
            to_yaml(config, stream=f)


def parse_config(config):
    """Parse the config dictionary for common objects.

    Currently only parses the following:
        * `directories` for relative path names.

    Args:
        config (dict): Config items.

    Returns:
        dict: Config items but with objects.
    """
    # Prepend the base directory to relative dirs
    if 'directories' in config:
        base_dir = os.getenv('PANDIR')
        for dir_name, rel_dir in config['directories'].items():
            abs_dir = os.path.normpath(os.path.join(base_dir, rel_dir))
            if abs_dir != rel_dir:
                config['directories'][dir_name] = abs_dir

    return config


def _add_to_conf(config, fn, parse=False):
    with suppress(IOError):
        with open(fn, 'r') as f:
            c = from_yaml(f, parse=parse)
            if c is not None and isinstance(c, dict):
                config.update(c)
