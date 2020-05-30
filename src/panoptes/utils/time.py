import os
import time
from contextlib import suppress
from datetime import timezone as tz

from astropy import units as u
from astropy.time import Time

from . import error
from .logging import logger


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

        >>> from panoptes.utils import current_time
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
        >>> from panoptes.utils import flatten_time
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


# This is a streamlined variant of PySerial's serialutil.Timeout.
class CountdownTimer(object):
    """Simple timer object for tracking whether a time duration has elapsed.


    Args:
        duration (int or float or astropy.units.Quantity): Amount of time to before time expires.
            May be numeric seconds or an Astropy time duration (e.g. 1 * u.minute).
    """

    def __init__(self, duration):
        if isinstance(duration, u.Quantity):
            duration = duration.to(u.second).value
        elif not isinstance(duration, (int, float)):
            raise ValueError(f'duration ({duration}) is not a supported type: {type(duration)}')

        #: bool: True IFF the duration is zero.
        assert duration >= 0, "Duration must be non-negative."
        self.is_non_blocking = (duration == 0)

        self.target_time = None
        self.duration = float(duration)
        self.restart()

    def __str__(self):
        is_blocking = ''
        if self.is_non_blocking is False:
            is_blocking = '(blocking)'
        is_expired = ''
        if self.expired():
            is_expired = 'EXPIRED '
        return f'{is_expired}Timer {is_blocking} {self.time_left():.02f}/{self.duration:.02f}'

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
        if self.is_non_blocking:
            return 0
        else:
            delta = self.target_time - time.monotonic()
            if delta > self.duration:
                # clock jumped, recalculate
                self.restart()
                return self.duration
            else:
                return max(0.0, delta)

    def restart(self):
        """Restart the timed duration."""
        self.target_time = time.monotonic() + self.duration
        logger.debug(f'Restarting {self}')

    def sleep(self, max_sleep=None):
        """Sleep until the timer expires, or for max_sleep, whichever is sooner.

        Args:
            max_sleep: Number of seconds to wait for, or None.
        Returns:
            True if slept for less than time_left(), False otherwise.
        """
        # Sleep for remaining time by default.
        remaining = self.time_left()
        if not remaining:
            return False
        sleep_time = remaining

        # Sleep only for max time if requested.
        if max_sleep and max_sleep < remaining:
            assert max_sleep > 0
            sleep_time = max_sleep

        logger.debug(f'Sleeping for {sleep_time:.02f} seconds')
        time.sleep(sleep_time)

        return sleep_time < remaining


def wait_for_events(events,
                    timeout=600,
                    sleep_delay=1 * u.second,
                    msg_interval=30 * u.second,
                    interrupt_cb=None,
                    event_type='generic',
                    ):
    """Wait for event(s) to be set.

    This method will wait for a maximum of `timeout` seconds for all of the `events`
    to complete.

    Checks every `sleep_delay` seconds for the events to be set.

    Will log debug messages approximately every `msg_interval` seconds.

    The wait loop can be interrupted via `interrupt_cb`, which must be a `callable`
    that returns `True` to interrupt the wait loop, `False` otherwise. The call will
    happen approximately every `sleep_delay` seconds.

    The `event_type` parameter is merely for logging purposes.

    .. doctest::

        >>> import time
        >>> import threading
        >>> from panoptes.utils.time import wait_for_events
        >>> # Create some events, normally something like taking an image.
        >>> event0 = threading.Event()
        >>> event1 = threading.Event()

        >>> # Wait for 30 seconds but interrupt after 1 second by returning True from interrupt.
        >>> def interrupt(): time.sleep(1); return True
        >>> # The function will return False if events are not set.
        >>> wait_for_events([event0, event1], timeout=30, interrupt_cb=interrupt)
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
        msg_interval (float, optional): Time in seconds between sending of log messages.
        interrupt_cb (callable): A callback for interrupting that can stop the wait if it
            returns True, default None (no callback).
        event_type (str, optional): The type of event, used for outputting in log messages,
            default 'generic'.

    Returns:
        bool: True if events were set, False otherwise.

    Raises:
        error.Timeout: Raised if events have not all been set before `timeout` seconds.
    """
    with suppress(AttributeError):
        sleep_delay = sleep_delay.to_value('second')

    event_timer = CountdownTimer(timeout)
    msg_timer = CountdownTimer(msg_interval)

    if not isinstance(events, list):
        events = [events]

    start_time = current_time()
    while not all([event.is_set() for event in events]):
        elapsed_secs = round((current_time() - start_time).to_value('second'), 2)

        if callable(interrupt_cb) and interrupt_cb():
            logger.info(f"Waiting for events has been interrupted after {elapsed_secs} seconds")
            break

        if msg_timer.expired():
            logger.debug(f'Waiting for {event_type} events: {elapsed_secs} seconds elapsed')
            msg_timer.restart()

        if event_timer.expired():
            raise error.Timeout(f"Timeout waiting for {event_type} event after {elapsed_secs} seconds")

        # Sleep for a little bit.
        event_timer.sleep(max_sleep=sleep_delay)

    return all([event.is_set() for event in events])
