import contextlib
import os
import re
import shutil
import signal
import collections.abc

import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz
from astropy.coordinates import ICRS
from astropy.coordinates import SkyCoord

from panoptes.utils.time import current_time

PATH_MATCHER = re.compile(
    r'.*(?P<unit_id>PAN\d{3})/(?P<camera_id>[a-gA-G1-9]{6})/(?P<sequence_id>.*?)/(?P<image_id>.*?)\..*')


def listify(obj):
    """ Given an object, return a list.

    Always returns a list. If obj is None, returns empty list,
    if obj is list, just returns obj, otherwise returns list with
    obj as single member.

    If a `dict` object is passed then this function will return a list of *only*
    the values.

    .. doctest::

        >>> listify(42)
        [42]
        >>> listify('foo')
        ['foo']
        >>> listify(None)
        []
        >>> listify(['a'])
        ['a']

        >>> my_dict = dict(a=42, b='foo')
        >>> listify(my_dict)
        [42, 'foo']
        >>> listify(my_dict.values())
        [42, 'foo']
        >>> listify(my_dict.keys())
        ['a', 'b']


    Returns:
        list:   You guessed it.
    """
    if obj is None:
        return list()
    elif isinstance(obj, list):
        return obj
    elif isinstance(obj, dict):
        return list(obj.values())
    elif isinstance(obj, (collections.abc.ValuesView, collections.abc.KeysView)):
        return list(obj)
    else:
        return [obj]


def get_free_space(dir=None):
    """Return the amoung of freespace in gigabytes for given dir.

    >>> from panoptes.utils import get_free_space
    >>> get_free_space()
    <Quantity ... Gbyte>

    >>> get_free_space(dir='/')
    <Quantity ... Gbyte>

    Args:
        dir (str, optional): Path to directory. If None defaults to $PANDIR.

    Returns:
        astropy.units.Quantity: The number of gigabytes avialable in folder.

    """
    if dir is None:
        dir = os.getenv('PANDIR')

    _, _, free_space = shutil.disk_usage(dir)
    free_space = (free_space * u.byte).to(u.gigabyte)
    return free_space


def string_to_params(opts):
    """Parses a single string into parameters that can be passed to a function.

    A user of the `peas_shell` can supply positional and keyword arguments to the
    command being called, however the `Cmd` module that is used for the shell does
    not parse these options but instead passes this as a single string. This utility
    method does some simple parsing of that string and returns a list of positional
    parameters and a dictionary of keyword arguments.  A keyword argument is considered
    anything that contains an equal sign (e.g. `exptime=30`). Any leading `--` to
    a keyword argument will be stripped during parsing.

    A list of items can be passed by specifying the keyword argument multiple times.

    Note:

        This function will attempt to parse keyword values as floats if possible.
        If a string is required include a single quote around the value, e.g.
        `param='42'` will keep the value as the string `'42'`.


    >>> from panoptes.utils import string_to_params
    >>> args, kwargs = string_to_params("parg1 parg2 key1=a_str key2=2 key2='2' key3=03")
    >>> args
    ['parg1', 'parg2']
    >>> kwargs
    {'key1': 'a_str', 'key2': [2.0, '2'], 'key3': 3.0}
    >>> isinstance(kwargs['key2'][0], float)
    True
    >>> isinstance(kwargs['key2'][1], str)
    True
    >>> kwargs['key2'][1] == '2'
    True

    >>> args, kwargs = string_to_params('--key1=val1 --key1-2=val1-2')
    >>> kwargs
    {'key1': 'val1', 'key1-2': 'val1-2'}

    Args:
        opts (str): A single string containing everything beyond the actual
            command that is called.

    Returns:
        tuple(list, dict): Returns a list of positional parameters and a dictionary
        of keyword arguments. These correspond to the *args and **kwargs that
        a typical function would receive.
    """
    args = []
    kwargs = {}

    for opt in opts.split(' '):
        if '=' not in opt:
            args.append(opt)
        else:
            name, value = opt.split('=', maxsplit=1)
            if name.startswith('--') and len(name) > 2:
                name = name[2:]

            if "'" in value:
                # Remove the explict single quotes.
                value = value.replace("'", "")
            else:
                # Make it a number if possible.
                with contextlib.suppress(ValueError):
                    value = float(value)

            if name in kwargs:
                kwargs[name] = listify(kwargs[name])
                kwargs[name].append(value)
            else:
                kwargs[name] = value

    return args, kwargs


def altaz_to_radec(alt=35, az=90, location=None, obstime=None, verbose=False):
    """Convert alt/az degrees to RA/Dec SkyCoord.

    >>> from panoptes.utils import altaz_to_radec
    >>> from astropy.coordinates import EarthLocation
    >>> keck = EarthLocation.of_site('Keck Observatory')
    ...

    >>> altaz_to_radec(alt=75, az=180, location=keck, obstime='2020-02-02T20:20:02.02')
    <SkyCoord (ICRS): (ra, dec) in deg
        (281.78..., 4.807...)>

    >>> # Will use current time if none given
    >>> altaz_to_radec(location=keck)
    <SkyCoord (ICRS): (ra, dec) in deg
        (..., ...)>

    >>> altaz_to_radec(location=keck, obstime='2020-02-02T20:20:02.02', verbose=True)
    Getting coordinates for Alt 35 Az 90, from (-5464487..., -2492806..., 2151240.19451846) m at 2020-02-02T20:20:02.02
    <SkyCoord (ICRS): (ra, dec) in deg
        (338.40968035, 11.11755983)>

    >>> # Must pass a `location` instance.
    >>> altaz_to_radec()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      ...
        assert location is not None
    AssertionError

    Args:
        alt (int, optional): Altitude, defaults to 35
        az (int, optional): Azimute, defaults to 90 (east)
        location (None|astropy.coordinates.EarthLocation, required): A valid location.
        obstime (None, optional): Time for object, defaults to `current_time`
        verbose (bool, optional): Verbose, default False.

    Returns:
        astropy.coordinates.SkyCoord: Coordinates corresponding to the AltAz.
    """
    assert location is not None
    if obstime is None:
        obstime = current_time()

    if verbose:
        print("Getting coordinates for Alt {} Az {}, from {} at {}".format(
            alt, az, location, obstime))

    altaz = AltAz(obstime=obstime, location=location, alt=alt * u.deg, az=az * u.deg)
    return SkyCoord(altaz.transform_to(ICRS))


class DelaySigTerm(contextlib.ContextDecorator):
    """Supports delaying SIGTERM during a critical section.

    This allows one to avoid having SIGTERM interrupt a
    critical block of code, such as saving to a database.

    Example:

        ..
        with DelaySigTerm():
            db.WriteCurrentRecord(record)

    """
    # TODO(jamessynge): Consider generalizing as DelaySignal(signum).

    def __enter__(self, callback=None):
        """
        Args:
            callback: If not None, called when SIGTERM is handled,
                with kwargs previously_caught and frame.
        """
        self.caught = False
        self.old_handler = signal.getsignal(signal.SIGTERM)
        if callback:
            assert callable(callback)
            self.callback = callback
        else:
            self.callback = None

        def handler(signum, frame):
            previously_caught = self.caught
            self.caught = True
            if self.callback:
                self.callback(previously_caught=previously_caught, frame=frame)

        signal.signal(signal.SIGTERM, handler)
        return self

    def __exit__(self, *exc):
        signal.signal(signal.SIGTERM, self.old_handler)
        if self.caught:
            # Send SIGTERM to this process.
            os.kill(os.getpid(), signal.SIGTERM)
            # Suppress any exception caught while the context was running.
            return True
        return False


def get_quantity_value(quantity, unit=None):
    """ Thin-wrapper around the `astropy.units.Quantity.to_value` method.

    If passed something other than a Quantity will simply return the original object.

    >>> from astropy import units as u
    >>> from panoptes.utils import get_quantity_value

    >>> get_quantity_value(60 * u.second)
    60.0

    >>> # Can convert between units.
    >>> get_quantity_value(60 * u.minute, unit='second')
    3600.0

    >>> get_quantity_value(60 * u.minute, unit=u.second)
    3600.0

    >>> get_quantity_value(60)
    60

    Args:
        quantity (astropy.units.Quantity): Quantity to extract numerical value from.
        unit (astropy.units.Unit, optional): unit to convert to.

    Returns:
        float: numerical value of the Quantity after conversion to the specified unit.
    """
    try:
        return quantity.to_value(unit)
    except AttributeError:
        return quantity


def moving_average(data_set, periods=3):
    """Moving average.

    Args:
        data_set (`numpy.array`): An array of values over which to perform the moving average.
        periods (int, optional): Number of periods.

    Returns:
        `numpy.array`: An array of the computed averages.
    """
    weights = np.ones(periods) / periods
    return np.convolve(data_set, weights, mode='same')


def image_id_from_path(path):
    """Return the `image_id` from the given path or uri.

    >>> from panoptes.utils import image_id_from_path
    >>> path = 'gs://panoptes-raw-images/PAN012/95cdbc/20190820T111638/20190820T122447.fits'
    >>> image_id_from_path(path)
    'PAN012_95cdbc_20190820T122447'

    Args:
        path (str): A path or uri for a file.

    Returns:
        str: The image id in the form "<unit_id>_<camera_id>_<image_id>"
    """
    result = PATH_MATCHER.match(path)
    return '{}_{}_{}'.format(
        result.group('unit_id'),
        result.group('camera_id'),
        result.group('image_id')
    )


def sequence_id_from_path(path):
    """Return the `sequence_id` from the given path or uri.

    >>> from panoptes.utils import sequence_id_from_path
    >>> path = 'gs://panoptes-raw-images/PAN012/95cdbc/20190820T111638/20190820T122447.fits'
    >>> sequence_id_from_path(path)
    'PAN012_95cdbc_20190820T111638'

    Args:
        path (str): A path or uri for a file.

    Returns:
        str: The image id in the form "<unit_id>_<camera_id>_<sequence_id>"
    """
    result = PATH_MATCHER.match(path)
    return '{}_{}_{}'.format(
        result.group('unit_id'),
        result.group('camera_id'),
        result.group('sequence_id')
    )
