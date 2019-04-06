import orjson

from astropy import units as u


def to_json(obj):
    """Convert a Python object to a JSON string.

    >>> from panoptes_utils.serializers import to_json
    >>> from astropy import units as u
    >>> config = { "location": { "name": "Mauna Loa", "elevation": 3397 * u.meter } }
    >>> to_json(config)
    '{"location":{"name":"Mauna Loa","elevation":{"value":3397.0,"unit":"m"}}}'

    Args:
        obj (any): The object to be converted to JSON, usually a dict.

    Returns:
        str: The JSON string representation of the object.
    """
    return orjson.dumps(obj, default=_serializer).decode('utf8')


def from_json(msg):
    """Convert a JSON string into a Python object.

    >>> from panoptes_utils.serializers import from_json
    >>> config_str = '{"location":{"name":"Mauna Loa","elevation":{"value":3397.0,"unit":"m"}}}'
    >>> from_json(config_str)
    {'location': {'name': 'Mauna Loa', 'elevation': <Quantity 3397. m>}}

    Args:
        msg (str): The JSON string representation of the object.

    Returns:
        dict: The loaded object.
    """
    return _parse_quantities(orjson.loads(msg))


def _parse_quantities(obj):
    # If there are exactly two keys
    keys = sorted(list(obj.keys()))
    if keys == ['unit', 'value']:
        return obj['value'] * u.Unit(obj['unit'])
    else:
        for k in keys:
            if isinstance(obj[k], dict):
                new_obj = _parse_quantities(obj[k])
                if new_obj is not None:
                    obj[k] = new_obj

        return obj


def _serializer(obj):
    if isinstance(obj, u.Quantity):
        return {'value': obj.value, 'unit': obj.unit.name}
