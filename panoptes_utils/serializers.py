import orjson

import numpy as np
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

    >>> to_json({"numpy_array": np.arange(10)})
    '{"numpy_array":[0,1,2,3,4,5,6,7,8,9]}'

    >>> from panoptes_utils import current_time
    >>> to_json({"current_time": current_time()})       # doctest: +SKIP
    '{"current_time":"2019-03-27T16:42:01.001"}'

    Args:
        obj (any): The object to be converted to JSON, usually a dict.

    Returns:
        str: The JSON string representation of the object.
    """
    return orjson.dumps(obj, default=_serializer).decode('utf8')


def from_json(msg):
    """Convert a JSON string into a Python object.

    Astropy quanitites will be converted from a ``{"value": val, "unit": unit}`` format.
    Time-like values are *not* parsed, however see example below.

    .. doctest::

        >>> from panoptes_utils.serializers import from_json
        >>> config_str = '{"location":{"name":"Mauna Loa","elevation":{"value":3397.0,"unit":"m"}}}'
        >>> from_json(config_str)
        {'location': {'name': 'Mauna Loa', 'elevation': <Quantity 3397. m>}}

        # Invalid values will be returned as is.
        >>> from_json('{"horizon":{"value":42.0,"unit":"degr"}}')
        {'horizon': {'value': 42.0, 'unit': 'degr'}}

        # Be careful with short unit names!
        >>> horizon = from_json('{"horizon":{"value":42.0,"unit":"d"}}')
        >>> horizon['horizon']
        <Quantity 42. d>
        >>> horizon['horizon'].decompose()
        <Quantity 3628800. s>

        >>> from panoptes_utils import current_time
        >>> time_str = to_json({"current_time": current_time().datetime})
        >>> from_json(time_str)['current_time']         # doctest: +SKIP
        2019-04-08T06:43:28.232406
        >>> from astropy.time import Time
        >>> Time(from_json(time_str)['current_time'])   # doctest: +SKIP
        <Time object: scale='utc' format='isot' value=2019-04-08T06:43:28.232>

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
    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    return str(obj)
