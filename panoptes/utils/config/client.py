import requests
from panoptes.utils import serializers
from panoptes.utils.logger import get_root_logger


def get_config(key=None, host='localhost', port='6563', parse=True, default=None):
    """Get a config item from the config server.

    Return the config entry for the given `key`. If `key=None` (default), return
    the entire config.

    Nested keys can be specified as a string, as per [scalpl](https://pypi.org/project/scalpl/).

    Examples:
        >>> get_config(key='name')
        'Generic PANOPTES Unit'
        >>> get_config(key='location.horizon')
        <Quantity 30. deg>
        >>> get_config(key='location.horizon', parse=False)
        '30.0 deg'
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

    Args:
        key (str): The key to update, see Examples in `get_config` for details.
        host (str, optional): The config server host, defaults to '127.0.0.1'.
        port (str, optional): The config server port, defaults to 6563.
        parse (bool, optional): If response should be parsed by
            `~panoptes.utils.serializers.from_json`, default True.
        default (str, optional): The config server port, defaults to 6563.

    Returns:
        dict: The corresponding config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    url = f'http://{host}:{port}/get-config'

    config_entry = default

    try:
        response = requests.post(url, json={'key': key})
    except Exception as e:
        get_root_logger().info(f'Problem with get_config: {e!r}')
    else:
        if not response.ok:
            get_root_logger().info(f'Problem with get_config: {response.content!r}')
        else:
            if response.text != 'null\n':
                if parse:
                    config_entry = serializers.from_json(response.content.decode('utf8'))
                else:
                    config_entry = response.json()

    if config_entry is None:
        config_entry = default

    return config_entry


def set_config(key, new_value, host='localhost', port='6563', parse=True):
    """Set config item in config server.

    Given a `key` entry, update the config to match. The `key` is a dot accessible
    string, as given by [scalpl](https://pypi.org/project/scalpl/). See Examples in `get_config`
    for details.

    Examples:
        >>> from astropy import units as u
        >>> set_config('location.horizon', 35 * u.degree)
        {'location.horizon': <Quantity 35. deg>}
        >>> get_config(key='location.horizon')
        <Quantity 35. deg>
        >>> set_config('location.horizon', 30 * u.degree)
        {'location.horizon': <Quantity 30. deg>}

    Args:
        key (str): The key to update, see Examples in `get_config` for details.
        new_value (scalar|object): The new value for the key, can be any serializable object.
        host (str, optional): The config server host, defaults to '127.0.0.1'.
        port (str, optional): The config server port, defaults to 6563.
        parse (bool, optional): If response should be parsed by
            `~panoptes.utils.serializers.from_json`, default True.

    Returns:
        dict: The updated config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    url = f'http://{host}:{port}/set-config'

    json_str = serializers.to_json({key: new_value})

    config_entry = None
    try:
        # We use our own serializer so pass as `data` instead of `json`.
        response = requests.post(url,
                                 data=json_str,
                                 headers={'Content-Type': 'application/json'}
                                 )
        if not response.ok:
            raise Exception(f'Cannot access config server: {response.text}')
    except Exception as e:
        get_root_logger().info(f'Problem with set_config: {e!r}')
    else:
        if parse:
            config_entry = serializers.from_json(response.content.decode('utf8'))
        else:
            config_entry = response.json()

    return config_entry
