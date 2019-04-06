import orjson

from astropy import units as u


def to_json(obj):
    """Convert a Python object to a JSON string.

    Will handle `datetime` objects as well as `astropy.unit.Quantity` objects.
    Astropy quantities will be converted to a dict: `{"value": val, "unit": unit}`.

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

    This will automatically handle `datetime` objects as well as `astropy.units.Quantity`
    values when stored as a `{"value": val, "unit": unit}` format.

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
    """Parse the incoming object for astropy quantities.

    If `obj` is a dict with exactly two keys named `unit` and `value, then attempt
    to parse into a valid `astropy.unit.Quantity`. If fail, simply return object
    as is.

    Args:
        obj (dict): Object to check for quantities.

    Returns:
        dict: Same as `obj` but with objects converted to quantities.
    """
    # If there are exactly two keys
    try:
        return obj['value'] * u.Unit(obj['unit'])
    except Exception:
        for k in obj.keys():
            if isinstance(obj[k], dict):
                obj[k] = _parse_quantities(obj[k])

        return obj


def _serializer(obj):
    if isinstance(obj, u.Quantity):
        return {'value': obj.value, 'unit': obj.unit.name}
