import os
import time
from contextlib import suppress
from datetime import timezone as tz
from typing import Union

from astropy import units as u
from astropy.time import Time
from loguru import logger

from panoptes.utils import error


def current_time(flatten=False, datetime=False, pretty=False):
    """ Convenience method to return the "current" time according to the system.

    Note:
        If the ``$POCSTIME`` environment variable is set then this will return
        the time given in the variable. This is used for setting specific times
        during testing. After checking the value of POCSTIME the environment
        variable will also be incremented by one second so that subsequent
        calls to this function will generate monotonically increasing times.

        **Operation of POCS from $POCS/bin/pocs_shell will clear the POCSTIME variable.**

        .. doctest::

            >>> os.environ['POCSTIME'] = '1999-12-31 23:59:59'
            >>> party_time = current_time(pretty=True)
            >>> party_time
            '1999-12-31 23:59:59'

            # Next call is one second later when using $POCSTIME.
            >>> y2k = current_time(pretty=True)
            >>> y2k
            '2000-01-01 00:00:00'


    Note:
        The time returned from this function is **not** timezone aware. All times
        are UTC.

    .. doctest::

        >>> from panoptes.utils.time import current_time
        >>> current_time()                # doctest: +SKIP
        <Time object: scale='utc' format='datetime' value=2018-10-07 22:29:03.009873>

        >>> current_time(datetime=True)   # doctest: +SKIP
        datetime.datetime(2018, 10, 7, 22, 29, 26, 594368)

        >>> current_time(pretty=True)     # doctest: +SKIP
        '2018-10-07 22:29:51'


    Returns:
        astropy.time.Time: Object representing now.
    """

    pocs_time = os.getenv('POCSTIME')

    if pocs_time is not None and pocs_time > '':
        _time = Time(pocs_time)
        # Increment POCSTIME
        os.environ['POCSTIME'] = (_time + 1 * u.second).isot
    else:
        _time = Time.now()

    if flatten:
        _time = flatten_time(_time)

    if pretty:
        _time = _time.isot.split('.')[0].replace('T', ' ')

    if datetime:
        # Add UTC timezone
        _time = _time.to_datetime(timezone=tz.utc)

    return _time


def flatten_time(t):
    """Given an astropy time, flatten to have no extra chars besides integers.

    .. doctest::

        >>> from astropy.time import Time
        >>> from panoptes.utils.time import flatten_time
        >>> t0 = Time('1999-12-31 23:59:59')
        >>> t0.isot
        '1999-12-31T23:59:59.000'

        >>> flatten_time(t0)
        '19991231T235959'

    Args:
        t (astropy.time.Time): The time to be flattened.

    Returns:
        str: The flattened string representation of the time.
    """
    return t.isot.replace('-', '').replace(':', '').split('.')[0]


class CountdownTimer(object):

    def __init__(self, duration: Union[int, float], name: str = ''):
        """Simple timer object for tracking whether a time duration has elapsed.

        Examples:

            >>> timer = CountdownTimer(1)
            >>> timer.time_left() > 0
            True
            >>> timer.expired()
            False
            >>> # Sleep less than the duration returns True.
            >>> timer.sleep(max_sleep=0.1)
            True
            >>> # Sleep more than the duration returns False.
            >>> timer.sleep()
            False
            >>> timer.time_left() == 0
            True
            >>> timer.expired()
            True
            >>> print(timer)
            EXPIRED Timer 0.00/1.00

        Args:
            duration (int or float or astropy.units.Quantity): Amount of time to before time expires.
                May be numeric seconds or an Astropy time duration (e.g. 1 * u.minute).
        """
        if isinstance(duration, u.Quantity):
            duration = duration.to(u.second).value
        elif not isinstance(duration, (int, float)):
            raise ValueError(f'duration ({duration}) is not a supported type: {type(duration)}')

        assert duration >= 0, "Duration must be non-negative."

        self.name = f'{name}Timer'
        self.target_time = None
        self.duration = float(duration)
        self.restart()

    def __str__(self):
        is_expired = ''
        if self.expired():
            is_expired = 'EXPIRED'
        return f'{is_expired} {self.name} {self.time_left():.02f}/{self.duration:.02f}'

    def expired(self):
        """Return a boolean, telling if the timeout has expired.

        Returns:
            bool: If timer has expired.
        """
        return self.time_left() <= 0

    def time_left(self):
        """Return how many seconds are left until the timeout expires.

        Returns:
            int: Number of seconds remaining in timer, zero if ``is_non_blocking=True``.
        """
        delta = self.target_time - time.monotonic()
        if delta > self.duration:  # pragma: no cover
            # clock jumped, recalculate
            self.restart()
            return self.duration
        else:
            return max(0.0, delta)

    def restart(self):
        """Restart the timed duration."""
        self.target_time = time.monotonic() + self.duration
        logger.debug(f'Restarting {self.name}')

    def sleep(self, max_sleep: Union[int, float, None] = None, log_level: str = 'DEBUG'):
        """Sleep until the timer expires, or for max_sleep, whichever is sooner.

        Args:
            max_sleep (int or None): Number of seconds to wait for, or None.
            log_level (str): Log level for sleeping message, default DEBUG.
        Returns:
            True if slept for less than time_left(), False otherwise.
        """
        # Sleep for remaining time by default.
        remaining = self.time_left()
        if not remaining:
            return False
        sleep_time = remaining

        # Sleep only for max time if requested.
        if max_sleep and max_sleep < sleep_time:
            sleep_time = max(max_sleep, 0)

        logger.log(log_level.upper(), f'Sleeping {self.name} for {sleep_time:.02f} seconds')
        time.sleep(sleep_time)

        return sleep_time < remaining


def wait_for_events(events,
                    timeout=600,
                    sleep_delay=5 * u.second,
                    callback=None,
                    ):
    """Wait for event(s) to be set.

    This method will wait for a maximum of `timeout` seconds for all the `events`
    to complete.

    Checks every `sleep_delay` seconds for the events to be set.

    If provided, the `callback` will be called every `sleep_delay` seconds.
    The callback should return `True` to continue waiting otherwise `False`
    to interrupt the loop and return from the function.

    .. doctest::

        >>> import time
        >>> import threading
        >>> from panoptes.utils.time import wait_for_events
        >>> # Create some events, normally something like taking an image.
        >>> event0 = threading.Event()
        >>> event1 = threading.Event()

        >>> # Wait for 30 seconds but interrupt after 1 second by returning False from callback.
        >>> def interrupt_cb(): time.sleep(1); return False
        >>> # The function will return False if events are not set.
        >>> wait_for_events([event0, event1], timeout=30, callback=interrupt_cb)
        False

        >>> # Timeout will raise an exception.
        >>> wait_for_events([event0, event1], timeout=1)
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
          File ".../panoptes-utils/src/panoptes/utils/time.py", line 254, in wait_for_events
        panoptes.utils.error.Timeout: Timeout: Timeout waiting for generic event

        >>> # Set the events in another thread for normal usage.
        >>> def set_events(): time.sleep(1); event0.set(); event1.set()
        >>> threading.Thread(target=set_events).start()
        >>> wait_for_events([event0, event1], timeout=30)
        True

    Args:
        events (list(`threading.Event`)): An Event or list of Events to wait on.
        timeout (float|`astropy.units.Quantity`): Timeout in seconds to wait for events,
            default 600 seconds.
        sleep_delay (float, optional): Time in seconds between event checks.
        callback (callable): A periodic callback that should return `True` to continue
            waiting or `False` to interrupt the loop. Can also be used for e.g. custom logging.

    Returns:
        bool: True if events were set, False otherwise.

    Raises:
        error.Timeout: Raised if events have not all been set before `timeout` seconds.
    """
    with suppress(AttributeError):
        sleep_delay = sleep_delay.to_value('second')

    event_timer = CountdownTimer(timeout)

    if not isinstance(events, list):
        events = [events]

    start_time = current_time()
    while not all([event.is_set() for event in events]):
        elapsed_secs = round((current_time() - start_time).to_value('second'), 2)

        if event_timer.expired():
            raise error.Timeout(
                f"Timeout waiting for {len(events)} events after {elapsed_secs} seconds")

        if callable(callback) and callback() is False:
            logger.warning(
                f"Waiting for {len(events)} events has been interrupted after {elapsed_secs} "
                f"seconds")
            break

        # Sleep for a little bit.
        event_timer.sleep(max_sleep=sleep_delay)

    return all([event.is_set() for event in events])
