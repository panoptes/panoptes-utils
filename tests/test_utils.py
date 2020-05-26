import os
import pytest
import signal

from panoptes.utils import DelaySigTerm
from panoptes.utils import listify
from panoptes.utils import error
from panoptes.utils.library import load_module
from panoptes.utils.library import load_c_library


def test_bad_load_module():
    with pytest.raises(error.NotFound):
        load_module('FOOBAR')


def test_load_c_library():
    # Called without a `path` this will use find_library to locate libc.
    libc = load_c_library('c')
    assert libc._name[:4] == 'libc'

    libc = load_c_library('c', mode=None)
    assert libc._name[:4] == 'libc'


def test_load_c_library_fail():
    # Called without a `path` this will use find_library to locate libc.
    with pytest.raises(error.NotFound):
        load_c_library('foobar')


def test_listify():
    assert listify(12) == [12]
    assert listify([1, 2, 3]) == [1, 2, 3]


def test_empty_listify():
    assert listify(None) == []


def test_listfy_dicts():
    d = dict(a=42)

    d_vals = d.values()
    d_keys = d.keys()

    assert isinstance(listify(d_vals), list)
    assert listify(d_vals) == list(d_vals)

    assert isinstance(listify(d_keys), list)
    assert listify(d_keys) == list(d_keys)

    assert isinstance(listify(d), list)
    assert listify(d) == list(d_vals)


def test_delay_of_sigterm_with_nosignal():
    orig_sigterm_handler = signal.getsignal(signal.SIGTERM)

    with DelaySigTerm():
        assert signal.getsignal(signal.SIGTERM) != orig_sigterm_handler

    assert signal.getsignal(signal.SIGTERM) == orig_sigterm_handler


def test_delay_of_sigterm_with_handled_signal():
    """Confirm that another type of signal can be handled.

    In this test we'll send SIGCHLD, which should immediately call the
    signal_handler the test installs, demonstrating that only SIGTERM
    is affected by this DelaySigTerm.
    """
    test_signal = signal.SIGCHLD

    # Booleans to keep track of how far we've gotten.
    before_signal = False
    after_signal = False
    signal_handled = False
    after_with = False

    def signal_handler(signum, frame):
        assert before_signal

        nonlocal signal_handled
        assert not signal_handled
        signal_handled = True

        assert not after_signal

    old_test_signal_handler = signal.getsignal(test_signal)
    orig_sigterm_handler = signal.getsignal(signal.SIGTERM)
    try:
        # Install our handler.
        signal.signal(test_signal, signal_handler)

        with DelaySigTerm():
            assert signal.getsignal(signal.SIGTERM) != orig_sigterm_handler
            before_signal = True
            # Send the test signal. It should immediately
            # call our handler.
            os.kill(os.getpid(), test_signal)
            assert signal_handled
            after_signal = True

        after_with = True
        assert signal.getsignal(signal.SIGTERM) == orig_sigterm_handler
    finally:
        assert before_signal
        assert signal_handled
        assert after_signal
        assert after_with
        assert signal.getsignal(signal.SIGTERM) == orig_sigterm_handler
        signal.signal(test_signal, old_test_signal_handler)


def test_delay_of_sigterm_with_raised_exception():
    """Confirm that raising an exception inside the handler is OK."""
    test_signal = signal.SIGCHLD

    # Booleans to keep track of how far we've gotten.
    before_signal = False
    after_signal = False
    signal_handled = False
    exception_caught = False

    def signal_handler(signum, frame):
        assert before_signal

        nonlocal signal_handled
        assert not signal_handled
        signal_handled = True

        assert not after_signal
        raise UserWarning()

    old_test_signal_handler = signal.getsignal(test_signal)
    orig_sigterm_handler = signal.getsignal(signal.SIGTERM)
    try:
        # Install our handler.
        signal.signal(test_signal, signal_handler)

        with DelaySigTerm():
            assert signal.getsignal(signal.SIGTERM) != orig_sigterm_handler
            before_signal = True
            # Send the test signal. It should immediately
            # call our handler.
            os.kill(os.getpid(), test_signal)
            # Should not reach this point because signal_handler() should
            # be called because we called:
            #     signal.signal(other-handler, signal_handler)
            after_signal = True
            assert False, "Should not get here!"
    except UserWarning:
        assert before_signal
        assert signal_handled
        assert not after_signal
        assert not exception_caught
        assert signal.getsignal(signal.SIGTERM) == orig_sigterm_handler
        exception_caught = True
    finally:
        # Restore old handler before asserts.
        signal.signal(test_signal, old_test_signal_handler)

        assert before_signal
        assert signal_handled
        assert not after_signal
        assert exception_caught
        assert signal.getsignal(signal.SIGTERM) == orig_sigterm_handler


def test_delay_of_sigterm_with_sigterm():
    """Confirm that SIGTERM is in fact delayed."""

    # Booleans to keep track of how far we've gotten.
    before_signal = False
    after_signal = False
    signal_handled = False

    def signal_handler(signum, frame):
        assert before_signal
        assert after_signal

        nonlocal signal_handled
        assert not signal_handled
        signal_handled = True

    orig_sigterm_handler = signal.getsignal(signal.SIGTERM)
    try:
        # Install our handler.
        signal.signal(signal.SIGTERM, signal_handler)

        with DelaySigTerm():
            before_signal = True
            # Send SIGTERM. It should not call the handler yet.
            os.kill(os.getpid(), signal.SIGTERM)
            assert not signal_handled
            after_signal = True

        assert signal.getsignal(signal.SIGTERM) == signal_handler
        assert before_signal
        assert after_signal
        assert signal_handled
    finally:
        signal.signal(signal.SIGTERM, orig_sigterm_handler)
