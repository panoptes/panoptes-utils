import pytest

from panoptes.utils import error
from panoptes.utils import rs232
from panoptes.utils.serializers import to_json


def test_port_discovery():
    ports = rs232.get_serial_port_info()
    assert isinstance(ports, list)


def test_missing_port():
    with pytest.raises(ValueError):
        rs232.SerialData()


def test_non_existent_device():
    """Doesn't complain if it can't find the device."""
    port = '/dev/tty12345698765'
    with pytest.raises(error.BadSerialConnection):
        ser = rs232.SerialData(port=port)


def test_usage():
    port = 'loop://'
    ser = rs232.SerialData(port=port, open_delay=0.1)
    assert ser.is_connected
    ser.connect()

    write_bytes = ser.write('Hello world\n')
    assert write_bytes == 12
    read_line = ser.read(write_bytes)
    assert read_line == 'Hello world\n'

    ser.write('A new line')
    ts, reading = ser.get_reading()
    assert reading == 'A new line'

    ser.write(to_json(dict(message='Hello world')))
    reading = ser.get_and_parse_reading()

    ser.reset_input_buffer()

    bytes = ser.write('a')
    ser.read_bytes(bytes)

    ser.disconnect()
    assert not ser.is_connected
