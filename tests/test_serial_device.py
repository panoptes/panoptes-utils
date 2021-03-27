import time

from panoptes.utils.serial.device import SerialDevice, SerialDeviceDefaults
from panoptes.utils.serializers import from_json, to_json


def test_device():
    s0 = SerialDevice(port='loop://', name='My loop device')
    assert s0.is_connected
    assert s0.port == 'loop://'

    assert str(s0) == 'My loop device on port=loop:// [9600/8-N-1]'

    s0.serial.close()
    assert s0.is_connected is False
    del s0

    s1 = SerialDevice(port='loop://')
    assert str(s1) == 'loop:// [9600/8-N-1]'
    del s1


def test_settings():
    s0 = SerialDevice(port='loop://', serial_settings=SerialDeviceDefaults(baudrate=115200))
    assert s0.serial.baudrate == 115200
    assert s0.serial.timeout == 1
    s1 = SerialDevice(port='loop://', serial_settings=dict(baudrate=115200, timeout=5))
    assert s1.serial.baudrate == 115200
    assert s1.serial.timeout == 5


def test_write():
    s0 = SerialDevice(port='loop://')
    assert len(s0.readings) == 0
    s0.write('Hello world')
    time.sleep(0.5)
    assert s0.readings[0] == 'Hello world'


def test_write_json():
    s0 = SerialDevice(port='loop://', reader_callback=from_json)
    assert len(s0.readings) == 0
    s0.write(to_json(dict(message='Hello world')))
    time.sleep(0.5)
    assert s0.readings[0]['message'] == 'Hello world'


def test_write_raise_exception(caplog):
    s0 = SerialDevice(port='loop://', reader_callback=from_json)
    assert len(s0.readings) == 0
    s0.write('not a json message')
    time.sleep(0.5)
    assert caplog.records[-1].message.startswith('Callback for serial reader error')
    assert caplog.records[-1].levelname == 'WARNING'
    assert s0.readings[0] == 'not a json message'
