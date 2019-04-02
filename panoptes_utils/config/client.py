import requests
from panoptes_utils.serializers import dumps as dump_json
from panoptes_utils.config import parse_config


def get_config(key=None, host='127.0.0.1', port='6563', parse=True):
    """Get a config item from the config server.

    Return the config entry for the given `key`. If `key=None` (default), return
    the entire config.

    Nested keys can be specified as a string, as per [scalpl](https://pypi.org/project/scalpl/).

    Examples:

        >>> get_config(key='name')
        'PAN000'
        >>> get_config(key='location.horizon')
        30 * u.degree
        >>> get_config(key='location.horizon', parse=False)
        30
        >>> get_config(key='cameras.devices[0].model')
        'canon_gphoto2'

    Args:
        key (str): The key to update, see Examples in `get_config` for details.
        host (str, optional): The config server host, defaults to '127.0.0.1'.
        port (str, optional): The config server port, defaults to 6563.
        parse (bool, optional): If the returned response should be parsed.

    Returns:
        dict: The corresponding config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    url = f'http://{host}:{port}/get-config'
    response = requests.post(url, json={'key': key})

    if not response.ok:
        raise Exception(f'Cannot access config server')

    config_entry = response.json()

    if parse:
        if key is not None:
            parse_config({key: config_entry})
        else:
            parse_config(config_entry)

    return config_entry


def set_config(key, new_value, host='127.0.0.1', port='6563', parse=True):
    """Set config item in config server.

    Given a `key` entry, update the config to match. The `key` is a dot accessible
    string, as given by [scalpl](https://pypi.org/project/scalpl/). See Examples in `get_config`
    for details.

    Args:
        key (str): The key to update, see Examples in `get_config` for details.
        new_value (scalar|object): The new value for the key, can be any serializable object.
        host (str, optional): The config server host, defaults to '127.0.0.1'.
        port (str, optional): The config server port, defaults to 6563.
        parse (bool, optional): If the returned response should be parsed.

    Returns:
        dict: The updated config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    url = f'http://{host}:{port}/set-config'

    post_json = dump_json({'key': key, 'value': new_value})

    response = requests.post(url, data=post_json, headers={'Content-Type': 'application/json'})

    if not response.ok:
        raise Exception(f'Cannot access config server')

    config_entry = response.json()

    if parse:
        if key is not None:
            parse_config({key: config_entry})
        else:
            parse_config(config_entry)

    return config_entry
