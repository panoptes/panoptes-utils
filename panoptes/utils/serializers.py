from contextlib import suppress
from copy import deepcopy
from collections import OrderedDict
import json
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

import numpy as np
from astropy.time import Time
from astropy import units as u

from . import error


class StringYAML(YAML):
    def dump(self, data, stream=None, **kwargs):
        """YAML class that can dump to a string.

        By default the YAML parser doesn't serialize directly to a string. This
        class is a small wrapper to output StreamIO as a string if no stream is
        provided.

        See https://yaml.readthedocs.io/en/latest/example.html#output-of-dump-as-a-string.

        Note:

            This class should not be used directly but instead is instantiated as
            part of the yaml convenience methods below.

        Args:
            data (`object`): An object, usually dict-like.
            stream (`None` | stream, optional): A stream object to write the YAML.
                If default `None`, return value as string.
            **kwargs: Keywords passed to the `dump` function.

        Returns:
            `str`: The serialized object string.
        """
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        yaml = YAML()
        yaml.dump(data, stream, **kwargs)
        if inefficient:
            return stream.getvalue()


def to_json(obj, filename=None, append=True, **kwargs):
    """Convert a Python object to a JSON string.

    Will handle `datetime` objects as well as `astropy.unit.Quantity` objects.
    Astropy quantities will be converted to a dict: `{"value": val, "unit": unit}`.

    Examples:
        .. doctest::

            >>> from panoptes.utils.serializers import to_json
            >>> from astropy import units as u
            >>> config = { "name": "Mauna Loa", "elevation": 3397 * u.meter }
            >>> to_json(config)
            '{"name": "Mauna Loa", "elevation": "3397.0 m"}'

            >>> to_json({"numpy_array": np.arange(10)})
            '{"numpy_array": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}'

            >>> from panoptes.utils import current_time
            >>> to_json({"current_time": current_time()})       # doctest: +SKIP
            '{"current_time": "2019-04-08 22:19:28.402198"}'

    Args:
        obj (`object`): The object to be converted to JSON, usually a dict.
        filename (str, optional): Path to file for saving.
        append (bool, optional): Append to `filename`, default True. Setting
            False will clobber the file.
        **kwargs: Keyword arguments passed to `json.dumps`.

    Returns:
        `str`: The JSON string representation of the object.
    """
    json_str = json.dumps(obj, default=_serialize_object, **kwargs)

    if filename is not None:
        mode = 'w'
        if append:
            mode = 'a'
        with open(filename, mode) as fn:
            fn.write(json_str + '\n')

    return json_str


def from_json(msg):
    """Convert a JSON string into a Python object.

    Astropy quanitites will be converted from a ``{"value": val, "unit": unit}``
    format. Additionally, the following units will be converted if the value ends
    with the exact string:

        * deg
        * m
        * s

    Time-like values are *not* parsed, however see example below.

    Examples:

        .. doctest::

            >>> from panoptes.utils.serializers import from_json
            >>> config_str = '{"name":"Mauna Loa","elevation":{"value":3397.0,"unit":"m"}}'
            >>> from_json(config_str)
            {'name': 'Mauna Loa', 'elevation': <Quantity 3397. m>}

            # Invalid values will be returned as is.
            >>> from_json('{"horizon":{"value":42.0,"unit":"degr"}}')
            {'horizon': {'value': 42.0, 'unit': 'degr'}}

            # The following will convert if final string:
            >>> from_json('{"horizon": "42.0 deg"}')
            {'horizon': <Quantity 42. deg>}

            >>> from_json('{"elevation": "1000 m"}')
            {'elevation': <Quantity 1000. m>}

            >>> from_json('{"readout_time": "10 s"}')
            {'readout_time': <Quantity 10. s>}

            # Be careful with short unit names in extended format!
            >>> horizon = from_json('{"horizon":{"value":42.0,"unit":"d"}}')
            >>> horizon['horizon']
            <Quantity 42. d>
            >>> horizon['horizon'].decompose()
            <Quantity 3628800. s>

            >>> from panoptes.utils import current_time
            >>> time_str = to_json({"current_time": current_time().datetime})
            >>> from_json(time_str)['current_time']         # doctest: +SKIP
            2019-04-08T06:43:28.232406

            >>> from astropy.time import Time
            >>> Time(from_json(time_str)['current_time'])   # doctest: +SKIP
            <Time object: scale='utc' format='isot' value=2019-04-08T06:43:28.232>

    Args:
        msg (`str`): The JSON string representation of the object.

    Returns:
        `dict`: The loaded object.
    """
    try:
        new_obj = _parse_all_objects(json.loads(msg))
    except json.decoder.JSONDecodeError as e:
        raise error.InvalidDeserialization(f'Error: {e!r} Message: {msg!r}')

    return new_obj


def to_yaml(obj, **kwargs):
    """Serialize a Python object to a YAML string.

    This will properly serialize the following:

        * `datetime.datetime`
        * `astropy.time.Time`
        * `astropy.units.Quantity`

    Examples:
        Also see the examples `from_yaml`.

        .. doctest::

            >>> import os
            >>> os.environ['POCSTIME'] = '1999-12-31 23:49:49'
            >>> from panoptes.utils import current_time
            >>> t0 = current_time()
            >>> t0
            <Time object: scale='utc' format='iso' value=1999-12-31 23:49:49.000>

            >>> to_yaml({'astropy time -> astropy time': t0})
            "astropy time -> astropy time: '1999-12-31T23:49:49.000'\\n"

            >>> to_yaml({'datetime -> astropy time': t0.datetime})
            "datetime -> astropy time: '1999-12-31T23:49:49.000'\\n"

            >>> # Can pass a `stream` parameter to save to file
            >>> with open('temp.yaml', 'w') as f:           # doctest: +SKIP
            ...     to_yaml({'my_object': 42}, stream=f)


    Args:
        obj (`object`): The object to be converted to be serialized.
        **kwargs: Arguments passed to `ruamel.yaml.dump`. See Examples.


    Returns:
        `str`: The YAML string representation of the object.
    """
    yaml = StringYAML()

    obj = _serialize_all_objects(deepcopy(obj))

    return yaml.dump(obj, **kwargs)


def from_yaml(msg, parse=True):
    """Convert a YAML string into a Python object.

    This is a thin-wrapper around `ruamel.YAML.load` that also parses the results
    looking for `astropy.units.Quantity` objects.

    Comments are preserved as long as the object remains YAML (lost on conversion
    to JSON, for example).

    See `from_json` for examples of astropy unit parsing.

    Examples:
        Note how comments in the YAML are preserved.

        .. doctest::

            >>> config_str = '''name: Generic PANOPTES Unit
            ... pan_id: PAN000
            ...
            ... location:
            ...   latitude: 19.54 deg
            ...   longitude: -155.58 deg
            ...   name: Mauna Loa Observatory  # Can be anything
            ... '''

            >>> config = from_yaml(config_str)
            >>> config['location']['latitude']
            <Quantity 19.54 deg>

            >>> yaml_config = to_yaml(config)
            >>> yaml_config                  # doctest: +SKIP
            ''' name: Generic PANOPTES Unit
            ... pan_id: PAN000  # CHANGE NAME
            ...
            ... location:
            ...   latitude: 19.54 deg
            ...   longitude: value: -155.58 deg
            ...   name: Mauna Loa Observatory  # Can be anything
            ... '''
            >>> yaml_config == config_str
            True

    Args:
        msg (`str`): The YAML string representation of the object.

    Returns:
        `collections.OrderedDict`: The ordered dict representing the YAML string, with appropriate
            object deserialization.
    """

    obj = YAML().load(msg)

    if parse:
        obj = _parse_all_objects(obj)

    return obj


def _parse_all_objects(obj):
    """Recursively parse the incoming object for astropy quantities.

    If `obj` is a dict with exactly two keys named `unit` and `value, then attempt
    to parse into a valid `astropy.unit.Quantity`. If fail, simply return object
    as is.

    Args:
        obj (`dict`): Object to check for quantities.

    Returns:
        `dict`: Same as `obj` but with objects converted to quantities.
    """
    if isinstance(obj, (dict, OrderedDict)):
        if 'value' in obj and 'unit' in obj:
            with suppress(ValueError):
                return obj['value'] * u.Unit(obj['unit'])

        for k, v in obj.items():
            obj[k] = _parse_all_objects(v)

    if isinstance(obj, bool):
        return bool(obj)

    # Try to turn into a time
    with suppress(KeyError, ValueError):
        if isinstance(Time(obj), Time):
            return Time(obj).datetime

    # Try to parse as quantity if certain type
    if isinstance(obj, str) and obj > '':
        with suppress(IndexError):
            units_string = obj.rsplit()[-1]  # Get the final word
            if units_string in ['m', 'deg', 's']:
                try:
                    quantity = u.Quantity(obj)
                    # If it ends up dimensionless just return obj.
                    if str(quantity.unit) == '':
                        return obj
                    else:
                        return quantity
                except Exception:
                    return obj

    return obj


def _serialize_all_objects(obj):
    for k, v in obj.items():
        # If it is a dict, send parse all its elements
        if isinstance(v, dict):
            obj[k] = _serialize_all_objects(v)
        else:
            obj[k] = _serialize_object(v, default=None)

    return obj


def _serialize_object(obj, default=None):
    # Astropy Quantity.
    if isinstance(obj, u.Quantity):
        return str(obj)

    # Numpy array.
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    # Astropy Time-like (including datetime).
    with suppress(ValueError):
        if isinstance(Time(obj), Time):
            return Time(obj).isot

    # If we are given a default object type, e.g. str
    if default is not None:
        return default(obj)

    return obj
