import requests
from panoptes_utils import serializers


def get_config(key=None, host='localhost', port='6563', parse=True):
    """Get a config item from the config server.

    Return the config entry for the given `key`. If `key=None` (default), return
    the entire config.

    Nested keys can be specified as a string, as per [scalpl](https://pypi.org/project/scalpl/).

    Examples:
        >>> get_config(key='name')
        'PAN000'
        >>> get_config(key='location.horizon')
        <Quantity 30 * u.deg>
        >>> get_config(key='location.horizon', parse=False)
        '30 deg'
        >>> get_config(key='cameras.devices[1].model')
        'canon_gphoto2'

    Args:
        key (str): The key to update, see Examples in `get_config` for details.
        host (str, optional): The config server host, defaults to '127.0.0.1'.
        port (str, optional): The config server port, defaults to 6563.
        parse (bool, optional): If response should be parsed by
            `~panoptes_utils.serializers.from_json`, default True.

    Returns:
        dict: The corresponding config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    url = f'http://{host}:{port}/get-config'
    response = requests.post(url, json={'key': key})

    if not response.ok:
        raise Exception(f'Cannot access config server: {response.content}')

    if parse:
        config_entry = serializers.from_json(response.content.decode('utf8'))
    else:
        config_entry = response.json()

    return config_entry


def set_config(key, new_value, host='localhost', port='6563', parse=True):
    """Set config item in config server.

    Given a `key` entry, update the config to match. The `key` is a dot accessible
    string, as given by [scalpl](https://pypi.org/project/scalpl/). See Examples in `get_config`
    for details.

    Args:
        key (str): The key to update, see Examples in `get_config` for details.
        new_value (scalar|object): The new value for the key, can be any serializable object.
        host (str, optional): The config server host, defaults to '127.0.0.1'.
        port (str, optional): The config server port, defaults to 6563.
        parse (bool, optional): If response should be parsed by
            `~panoptes_utils.serializers.from_json`, default True.

    Returns:
        dict: The updated config entry.

    Raises:
        Exception: Raised if the config server is not available.
    """
    url = f'http://{host}:{port}/set-config'

    json_str = serializers.to_json({key: new_value})

    response = requests.post(url,
                             data=json_str,
                             headers={'Content-Type': 'application/json'}
                             )

    if not response.ok:
        raise Exception(f'Cannot access config server: {response.text}')

    if parse:
        config_entry = serializers.from_json(response.content.decode('utf8'))
    else:
        config_entry = response.json()

    return config_entry
