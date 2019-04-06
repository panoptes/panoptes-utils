import orjson

from astropy import units as u


def _serializer(obj):
    if isinstance(obj, u.Quantity):
        return {'value': obj.value, 'unit': obj.unit.name}


def to_string(*args, **kwargs):
    return dumps(*args, **kwargs)


def dumps(obj, use_yaml=False):
    """Dump an object to JSON.

    Args:
        obj (dict): An object to serialize.

    Returns:
        str: Serialized representation of object.
    """
    return orjson.dumps(obj, default=_serializer).decode('utf8')


def to_object(*args, **kwargs):
    return loads(*args, **kwargs)


def loads(msg):
    """Load an object from JSON or YAML.

    Args:
        msg (str): A serialized string representation of object.

    Returns:
        dict: The loaded object.
    """
    return orjson.loads(msg)


def dumps_file(fn, obj, clobber=False):
    """Convenience warpper to dump an object to a a file.

    Args:
        fn (str): Path of filename where object representation will be saved.
        obj (dict): An object to serialize.
        clobber (bool, optional): If object should be overwritten or appended to.
            Defaults to False, which will append to file.

    Returns:
        str: Filename of the file that was written to.
    """
    if clobber is True:
        mode = 'w'
    else:
        mode = 'a'

    with open(fn, mode) as f:
        f.write(orjson.dumps(obj, default=_serializer) + "\n")

    return fn


def loads_file(file_path):
    """Convenience wrapper to load an object from a file.

    Args:
        file_path (str): Path of filename that contains a serialization of the
            the object.

    Returns:
        dict: The loaded object from the given file.
    """
    obj = None
    with open(file_path, 'r') as f:
        obj = orjson.loads(f.read())

    return obj
