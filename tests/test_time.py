import os
import pytest

import time
import threading
from datetime import timezone as tz
from datetime import datetime as dt
from astropy import units as u

from panoptes.utils import error
from panoptes.utils import current_time
from panoptes.utils import CountdownTimer
from panoptes.utils.time import wait_for_events


def test_pretty_time():
    t0 = '2016-08-13 10:00:00'
    os.environ['POCSTIME'] = t0

    t1 = current_time(pretty=True)
    assert t1 == t0

    # This will increment one second - see docs
    t2 = current_time(flatten=True)
    assert t2 != t0
    assert t2 == '20160813T100001'

    # This will increment one second - see docs
    t3 = current_time(datetime=True)
    assert t3 == dt(2016, 8, 13, 10, 0, 2, tzinfo=tz.utc)


def test_countdown_timer_bad_input():
    with pytest.raises(ValueError):
        assert CountdownTimer('d')

    with pytest.raises(ValueError):
        assert CountdownTimer(current_time())

    with pytest.raises(AssertionError):
        assert CountdownTimer(-1)


def test_countdown_timer_non_blocking():
    timer = CountdownTimer(0)
    assert timer.is_non_blocking
    assert timer.time_left() == 0

    for arg, expected_duration in [(2, 2.0), (0.5, 0.5), (1 * u.second, 1.0)]:
        timer = CountdownTimer(arg)
        assert timer.duration == expected_duration


def test_countdown_timer():
    count_time = 1
    timer = CountdownTimer(count_time)
    assert timer.time_left() > 0
    assert timer.expired() is False
    assert timer.is_non_blocking is False

    counter = 0.
    while timer.time_left() > 0:
        time.sleep(0.1)
        counter += 0.1

    assert counter == pytest.approx(1)
    assert timer.time_left() == 0
    assert timer.expired() is True


def test_countdown_timer_sleep():
    count_time = 1
    timer = CountdownTimer(count_time)
    assert timer.time_left() > 0
    assert timer.expired() is False
    assert timer.is_non_blocking is False

    counter = 0.
    while timer.time_left() > 0.5:
        assert timer.sleep(max_sleep=0.1)
        counter += 0.1

    # Wait for the remaining half second
    assert timer.sleep() is False

    assert counter == pytest.approx(0.5)
    assert timer.time_left() == 0
    assert timer.expired() is True
    assert timer.sleep() is False


def test_wait_for_events():
    # Create some events, normally something like taking an image.
    event0 = threading.Event()
    event1 = threading.Event()

    # Wait for 30 seconds but interrupt after 1 second by returning True.
    def interrupt():
        time.sleep(1)
        return True

    assert wait_for_events([event0, event1], timeout=30, interrupt_cb=interrupt) is False

    # Timeout if event is never set.
    with pytest.raises(error.Timeout):
        wait_for_events(event0, timeout=1)

    # Setting events causes timer to exit.
    def set_events():
        time.sleep(3)
        event0.set()
        event1.set()

    threading.Thread(target=set_events).start()
    assert wait_for_events([event0, event1], msg_interval=1, timeout=30)

    # If the events are set then the function will return immediately
    assert wait_for_events([event0, event1], timeout=30)
