import operator
from collections import deque
from contextlib import suppress
from dataclasses import dataclass
from typing import Optional, Union, Callable

import serial
from loguru import logger
from serial.threaded import LineReader, ReaderThread
from serial.tools.list_ports import comports as get_comports

from panoptes.utils import error


@dataclass
class SerialDeviceDefaults:
    """Dataclass for the serial port defaults.

    This can be instantiated with changed values and then passed to the serial
    device via the `apply_settings` method.

    Values are:

        write_timeout, inter_byte_timeout, dsrdtr, baudrate,
        timeout, parity, bytesize, rtscts, stopbits, xonxoff

    See https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial.get_settings

    .. doctest:

        >>> import serial
        >>> from panoptes.utils.serial.device import SerialDeviceDefaults
        >>> serial_settings = SerialDeviceDefaults(baudrate=115200)
        >>> serial_settings
        SerialDeviceDefaults(baudrate=115200, timeout=1.0, write_timeout=1.0, bytesize=8, parity='N', stopbits=1, xonxoff=False, rtscts=False, dsrdtr=False)

        >>> # Create a serial device and apply changed settings.
        >>> ser0 = serial.Serial()
        >>> serial_settings.write_timeout = 2.5
        >>> serial_settings.baudrate = 9600
        >>> ser0.apply_settings(serial_settings.to_dict())
        >>> ser0.write_timeout
        2.5
        >>> ser0.baudrate
        9600

    """
    baudrate: int = 9600
    timeout: float = 1.
    write_timeout: float = 1.
    bytesize: int = serial.EIGHTBITS
    parity: str = serial.PARITY_NONE
    stopbits: int = serial.STOPBITS_ONE
    xonxoff: bool = False
    rtscts: bool = False
    dsrdtr: bool = False

    def to_dict(self):
        """Return fields as dict."""
        return {field: getattr(self, field)
                for field in self.__dataclass_fields__.keys()}


def get_serial_port_info():
    """Returns the serial ports defined on the system sorted by device name.

    .. doctest::

        >>> from panoptes.utils.serial.device import get_serial_port_info
        >>> devices = get_serial_port_info()
        >>> devices             # doctest: +SKIP
        [<serial.tools.list_ports_linux.SysFS object at 0x7f6c9cbd9460>]
        >>> devices[0].hwid     # doctest: +SKIP
        'USB VID:PID=2886:802D SER=3C788B875337433838202020FF122204 LOCATION=3-5:1.0'

    Returns: a list of PySerial's ListPortInfo objects. See:
        https://github.com/pyserial/pyserial/blob/master/serial/tools/list_ports_common.py
    """
    return sorted(get_comports(include_links=True), key=operator.attrgetter('device'))


def find_serial_port(vendor_id, product_id, return_all=False):  # pragma: no cover
    """Finds the serial port that matches the given vendor and product id.

    .. doctest::

        >>> from panoptes.utils.serial.device import find_serial_port
        >>> vendor_id = 0x2a03  # arduino
        >>> product_id = 0x0043 # Uno Rev 3
        >>> find_serial_port(vendor_id, product_id)  # doctest: +SKIP
        '/dev/ttyACM0'

        >>> # Raises error when not found.
        >>> find_serial_port(0x1234, 0x4321)
        Traceback (most recent call last):
          ...
        panoptes.utils.error.NotFound: NotFound: No serial ports...

    Args:
        vendor_id (int): The vendor id, can be hex or int.
        product_id (int): The product id, can be hex or int.
        return_all (bool): If more than one serial port matches, return all devices, default False.

    Returns:
        str or list: Either the path to the detected port or a list of all comports that match.
    """
    # Get all serial ports.
    matched_ports = [p for p in get_serial_port_info() if
                     p.vid == vendor_id and p.pid == product_id]

    if len(matched_ports) == 1:
        return matched_ports[0].device
    elif return_all:
        return matched_ports
    else:
        raise error.NotFound(
            f'No serial ports for vendor_id={vendor_id:x} and product_id={product_id:x}')


class SerialDevice(object):
    def __init__(self,
                 port: str = None,
                 name: str = None,
                 reader_callback: Callable = None,
                 serial_settings: Optional[Union[SerialDeviceDefaults, dict]] = None,
                 reader_queue_size: int = 50,
                 ):
        """A SerialDevice class with helper methods for serial communications.

        The device need not exist at the time this is called, in which case
        is_connected will be false.

        The serial device settings can be passed as a dictionary. See SerialDeviceDefaults
        for possible values.

        .. doctest::

            >>> from panoptes.utils.serial.device import SerialDevice
            >>> dev0 = SerialDevice(port='loop://', name='My device')
            >>> dev0.is_connected
            True
            >>> str(dev0)
            'My device on port=loop:// [9600/8-N-1]'
            >>> dev0.write('Hello World!')  # doctest: +SKIP
            >>> len(dev0.readings) # doctest: +SKIP
            1
            >>> dev0.readings[0] == 'Hello World!' # doctest: +SKIP
            True

            >>> # We can also pass a custom callback.
            >>> from panoptes.utils.serializers import from_json, to_json
            >>> dev1 = SerialDevice(port='loop://', reader_callback=from_json)
            >>> str(dev1)
            'SerialDevice loop:// [9600/8-N-1]'
            >>> dev1.write(to_json(dict(message='Hello JSON World!')))  # doctest: +SKIP
            >>> len(dev0.readings)  # doctest: +SKIP
            1
            >>> dev0.readings[0]  # doctest: +SKIP
            '{"message": "Hello JSON World!"}'

        Args:
            port (str): The port (e.g. /dev/tty123 or socket://host:port) to which to
                open a connection.
            name (str): Name of this object. Defaults to the name of the port.
            reader_callback (Callable): A callback from the reader thread. This should
                accept and return a single parameter. The return item will get appended
                to the `readings` deque.
            serial_settings (dict): The settings to apply to the serial device. See
                docstring for details.
            reader_queue_size (int, optional): The size of the deque for readings,
                default 50.

        Raises:
            ValueError: If the serial parameters are invalid (e.g. a negative baudrate).

        """
        self.name = name or port
        self.readings = deque(maxlen=reader_queue_size)
        self.reader_thread = None
        self._reader_callback = reader_callback

        self.serial: serial.Serial = serial.serial_for_url(port)
        logger.debug(f'SerialDevice for {self.name} created. Connected={self.is_connected}')

        serial_settings = serial_settings or SerialDeviceDefaults()
        if isinstance(serial_settings, SerialDeviceDefaults):
            serial_settings = serial_settings.to_dict()
        logger.debug(f'Applying settings to serial class: {serial_settings!r}')
        self.serial.apply_settings(serial_settings)

        self._add_stream_reader()

    @property
    def port(self):
        """Name of the port."""
        return self.serial.port

    @property
    def is_connected(self):
        """True if serial port is open, False otherwise."""
        return self.serial.is_open

    def connect(self):
        """Connect to device and add default reader."""
        if not self.is_connected:
            self.serial.open()
            self._add_stream_reader()

    def disconnect(self):
        """Disconnect from the device and reset the reader thread."""
        with suppress(AttributeError):
            self.serial.close()
            self.reader_thread = None

    def write(self, line):
        """Write to the serial device.

        Note that this expects unicode and will handle adding a newline at the
        end.
        """
        return self.reader_thread.protocol.write_line(line)

    def _add_stream_reader(self, callback=None):
        """Add a reader to the device."""

        callback = callback or self._reader_callback

        # Set up a custom threaded reader class that calls user callback.
        class CustomReader(LineReader):
            # Use `this` so `self` still refers to device instance.
            def connection_made(this, transport):
                super(LineReader, this).connection_made(transport)

            def connection_lost(this, exc):
                logger.trace(f'Disconnected from {self}')

            def handle_line(this, data):
                try:
                    if callback and callable(callback):
                        data = callback(data)
                    if data is not None:
                        self.readings.append(data)
                except Exception as e:
                    logger.trace(f'Error with callback: {e!r}')

        self.reader_thread = ReaderThread(self.serial, CustomReader)
        self.reader_thread.start()

    def __str__(self):
        if self.name == self.port:
            full_name = f'SerialDevice {self.name}'
        else:
            full_name = f'{self.name} on port={self.port}'

        with self.serial as s:
            serial_summary = f'{s.baudrate}/{s.bytesize}-{s.parity}-{s.stopbits}'
        return f'{full_name} [{serial_summary}]'

    def __del__(self):
        """Close the serial device on delete.

        This is to avoid leaving a file or device open if there are multiple references
        to the serial.Serial object.
        """
        # If an exception is thrown when running __init__, then self.serial may not have
        # been set, in which case reading that field will generate a AttributeError.
        with suppress(AttributeError):  # pragma: no cover
            if self.serial and self.serial.is_open:
                self.serial.close()
