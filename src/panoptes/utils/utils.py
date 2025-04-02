import collections.abc
import os
import shutil

import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, ICRS, SkyCoord

from panoptes.utils.time import current_time


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


def get_free_space(directory=None):
    """Return the amoung of freespace in gigabytes for given directory.

    >>> from panoptes.utils.utils import get_free_space
    >>> get_free_space()
    <Quantity ... Gbyte>

    >>> get_free_space(directory='/')
    <Quantity ... Gbyte>

    Args:
        directory (str, optional): Path to directory. If None defaults to root.

    Returns:
        astropy.units.Quantity: The number of gigabytes avialable in folder.

    """
    directory = directory or os.path.abspath('/')

    _, _, free_space = shutil.disk_usage(directory)
    free_space = (free_space * u.byte).to(u.gigabyte)
    return free_space


def altaz_to_radec(alt=None, az=None, location=None, obstime=None, **kwargs):
    """Convert alt/az degrees to RA/Dec SkyCoord.

    >>> from panoptes.utils.utils import altaz_to_radec
    >>> from astropy.coordinates import EarthLocation
    >>> from astropy import units as u
    >>> keck = EarthLocation.of_site('Keck Observatory')
    ...

    >>> altaz_to_radec(alt=75, az=180, location=keck, obstime='2020-02-02T20:20:02.02')
    <SkyCoord (ICRS): (ra, dec) in deg
        (281.78..., 4.807...)>

    >>> # Can use quantities or not.
    >>> alt = 4500 * u.arcmin
    >>> az = 180 * u.degree
    >>> altaz_to_radec(alt=alt, az=az, location=keck, obstime='2020-02-02T20:20:02.02')
    <SkyCoord (ICRS): (ra, dec) in deg
        (281.78..., 4.807...)>

    >>> # Will use current time if none given.
    >>> altaz_to_radec(alt=35, az=90, location=keck)
    <SkyCoord (ICRS): (ra, dec) in deg
        (..., ...)>

    >>> # Must pass a `location` instance.
    >>> altaz_to_radec()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      ...
        assert location is not None
    AssertionError

    Args:
        alt (astropy.units.Quantity or scalar): Altitude.
        az (astropy.units.Quantity or scalar): Azimuth.
        location (astropy.coordinates.EarthLocation, required): A valid location.
        obstime (None, optional): Time for object, defaults to `current_time`

    Returns:
        astropy.coordinates.SkyCoord: Coordinates corresponding to the AltAz.
    """
    assert location is not None
    if obstime is None:
        obstime = current_time()

    alt = get_quantity_value(alt, 'degree') * u.degree
    az = get_quantity_value(az, 'degree') * u.degree

    altaz = AltAz(obstime=obstime, location=location, alt=alt, az=az)
    return SkyCoord(altaz.transform_to(ICRS()))


def get_quantity_value(quantity, unit=None):
    """ Thin-wrapper around the `astropy.units.Quantity.to_value` method.

    If passed something other than a Quantity will simply return the original object.

    >>> from astropy import units as u
    >>> from panoptes.utils.utils import get_quantity_value

    >>> get_quantity_value(60 * u.second)
    60.0

    >>> # Can convert between units.
    >>> get_quantity_value(60 * u.minute, unit='second')
    3600.0

    >>> get_quantity_value(60 * u.minute, unit=u.second)
    3600.0

    >>> get_quantity_value(60)
    60

    >>> get_quantity_value('J2000.0', unit='jyear_str')
    'J2000.0'

    >>> get_quantity_value('J2000.0')
    'J2000.0'

    Args:
        quantity (astropy.units.Quantity or scalar): Quantity to extract numerical value from.
        unit (astropy.units.Unit, optional): unit to convert to.

    Returns:
        float: numerical value of the Quantity after conversion to the specified unit.
    """
    try:
        quantity = quantity.to_value(unit)
        if type(quantity) == np.float64:
            return quantity.item()
        return quantity
    except AttributeError:
        return quantity
