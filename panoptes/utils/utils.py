import contextlib
import os
import shutil
import signal

import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz
from astropy.coordinates import ICRS
from astropy.coordinates import SkyCoord

from panoptes.utils.time import current_time


def listify(obj):
    """ Given an object, return a list.

    Always returns a list. If obj is None, returns empty list,
    if obj is list, just returns obj, otherwise returns list with
    obj as single member.

    Returns:
        list:   You guessed it.
    """
    if obj is None:
        return []
    else:
        return obj if isinstance(obj, (list, type(None))) else [obj]


def get_free_space(dir=None):
    """Return the amoung of freespace in gigabytes for given dir.

    >>> from panoptes.utils import get_free_space
    >>> get_free_space()        # doctest: +SKIP
    <Quantity 10.245 Gbyte>

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
    """ Return the numerical value of a Quantity, optionally converting to unit at the same time.

    If passed something other than a Quantity will simply return the original object.

    Args:
        quantity (astropy.units.Quantity): Quantity to extract numerical value from.
        unit (astropy.units.Unit, optional): unit to convert to.

    Returns:
        float: numerical value of the Quantity after conversion to the specified unit.
    """
    if isinstance(quantity, u.Quantity):
        if unit is not None:
            quantity = quantity.to(unit)
        return quantity.value
    else:
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

