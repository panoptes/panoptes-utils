import os

import requests
from panoptes.utils.error import InvalidConfig
from panoptes.utils.logging import logger
from panoptes.utils.serializers import from_json
from panoptes.utils.serializers import to_json


def server_is_running():
    """Thin-wrapper to check server."""
    try:
        return get_config(endpoint='heartbeat', verbose=False)
    except Exception as e:
        logger.warning(f'server_is_running error (ignore if just starting server): {e!r}')
        return False


def get_config(key=None,
               host=None,
               port=None,
               endpoint='get-config',
               parse=True,
               default=None,
               verbose=True
               ):
    """Get a config item from the config server.

    Return the config entry for the given ``key``. If ``key=None`` (default), return
    the entire config.

    Nested keys can be specified as a string, as per `scalpl <https://pypi.org/project/scalpl/>`_.

    Examples:

    .. doctest::

        >>> get_config(key='name')
        'Testing PANOPTES Unit'

        >>> get_config(key='location.horizon')
        <Quantity 30. deg>

        >>> # With no parsing, the raw string (including quotes) is returned.
        >>> get_config(key='location.horizon', parse=False)
        '"30.0 deg"'
        >>> get_config(key='cameras.devices[1].model')
        'canon_gphoto2'

        >>> # Returns `None` if key is not found.
        >>> foobar = get_config(key='foobar')
        >>> foobar is None
        True

        >>> # But you can supply a default.
        >>> get_config(key='foobar', default='baz')
        'baz'

        >>> # Can use Quantities as well
        >>> from astropy import units as u
        >>> get_config(key='foobar', default=42 * u.meter)
        <Quantity 42. m>

    Notes:
        By default all calls to this function will log at the `trace` level because
        there are some calls (e.g. during POCS operation) that will be quite noisy.

        Setting `verbose=True` changes those to `debug` log levels for an individual
        call.

    Args:
        key (str): The key to update, see Examples in :func:`get_config` for details.
        host (str, optional): The config server host. First checks for PANOPTES_CONFIG_HOST
            env var, defaults to 'localhost'.
        port (str or int, optional): The config server port. First checks for PANOPTES_CONFIG_HOST
            env var, defaults to 6563.
        endpoint (str, optional): The relative url endpoint to use for getting
            the config items, default 'get-config'. See `server_is_running()`
            for example of usage.
        parse (bool, optional): If response should be parsed by
            :func:`panoptes.utils.serializers.from_json`, default True.
        default (str, optional): The config server port, defaults to 6563.
        verbose (bool, optional): Determines the output log level, defaults to
            True (i.e. `debug` log level). See notes for details.
    Returns:
        dict: The corresponding config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    log_level = 'DEBUG' if verbose else 'TRACE'

    host = host or os.getenv('PANOPTES_CONFIG_HOST', 'localhost')
    port = port or os.getenv('PANOPTES_CONFIG_PORT', 6563)

    url = f'http://{host}:{port}/{endpoint}'

    config_entry = default

    try:
        logger.log(log_level, f'Calling get_config on {url=} with {key=}')
        response = requests.post(url, json={'key': key, 'verbose': verbose})
        if not response.ok:  # pragma: no cover
            raise InvalidConfig(f'Config server returned invalid JSON: {response.content=}')
    except Exception as e:
        logger.warning(f'Problem with get_config: {e!r}')
    else:
        response_text = response.text.strip()
        logger.log(log_level, f'Decoded {response_text=}')
        if response_text != 'null':
            logger.log(log_level, f'Received config {key=} {response_text=}')
            if parse:
                logger.log(log_level, f'Parsing config results: {response_text=}')
                config_entry = from_json(response_text)
            else:
                config_entry = response_text

    if config_entry is None:
        logger.log(log_level, f'No config entry found, returning {default=}')
        config_entry = default

    logger.log(log_level, f'Config {key=}: {config_entry=}')
    return config_entry


def set_config(key, new_value, host=None, port=None, parse=True):
    """Set config item in config server.

    Given a `key` entry, update the config to match. The `key` is a dot accessible
    string, as given by `scalpl <https://pypi.org/project/scalpl/>`_. See Examples in
    :func:`get_config` for details.

    Examples:

    .. doctest::

        >>> from astropy import units as u

        >>> # Can use astropy units.
        >>> set_config('location.horizon', 35 * u.degree)
        {'location.horizon': <Quantity 35. deg>}

        >>> get_config(key='location.horizon')
        <Quantity 35. deg>

        >>> # String equivalent works for 'deg', 'm', 's'.
        >>> set_config('location.horizon', '30 deg')
        {'location.horizon': <Quantity 30. deg>}

    Args:
        key (str): The key to update, see Examples in :func:`get_config` for details.
        new_value (scalar|object): The new value for the key, can be any serializable object.
        host (str, optional): The config server host. First checks for PANOPTES_CONFIG_HOST
            env var, defaults to 'localhost'.
        port (str or int, optional): The config server port. First checks for PANOPTES_CONFIG_HOST
            env var, defaults to 6563.
        parse (bool, optional): If response should be parsed by
            :func:`panoptes.utils.serializers.from_json`, default True.

    Returns:
        dict: The updated config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    host = host or os.getenv('PANOPTES_CONFIG_HOST', 'localhost')
    port = port or os.getenv('PANOPTES_CONFIG_PORT', 6563)
    url = f'http://{host}:{port}/set-config'

    json_str = to_json({key: new_value})

    config_entry = None
    try:
        # We use our own serializer so pass as `data` instead of `json`.
        logger.info(f'Calling set_config on {url=}')
        response = requests.post(url,
                                 data=json_str,
                                 headers={'Content-Type': 'application/json'}
                                 )
        if not response.ok:  # pragma: no cover
            raise Exception(f'Cannot access config server: {response.text}')
    except Exception as e:
        logger.warning(f'Problem with set_config: {e!r}')
    else:
        if parse:
            config_entry = from_json(response.content.decode('utf8'))
        else:
            config_entry = response.json()

    return config_entry
