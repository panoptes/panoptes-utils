import time

import pytest

from panoptes.utils import error
from panoptes.utils import rs232


def test_port_discovery():
    ports = rs232.get_serial_port_info()
    assert isinstance(ports, list)


def test_missing_port():
    with pytest.raises(ValueError):
        rs232.SerialData()


def test_non_existent_device():
    """Doesn't complain if it can't find the device."""
    port = '/dev/tty12345698765'
    ser = rs232.SerialData(port=port)
    assert not ser.is_connected
    assert port == ser.name
    # Can't connect to that device.
    with pytest.raises(error.BadSerialConnection):
        ser.connect()
    assert not ser.is_connected


def test_usage():
    port = 'loop://'
    ser = rs232.SerialData(port=port)
    assert ser.is_connected
    write_bytes = ser.write('Hello world\n')
    assert write_bytes == 12
    read_line = ser.read(write_bytes)
    assert read_line == 'Hello world\n'
    ser.disconnect()
    assert not ser.is_connected


def test_open_delay():
    ser = rs232.SerialData(port='loop://', open_delay=0.5)
    assert not ser.is_connected
    while not ser.is_connected:
        time.sleep(0.1)
    assert ser.is_connected
    ser.connect()
