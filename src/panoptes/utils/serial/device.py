import json
import operator
import traceback
from collections import deque
from contextlib import suppress
from typing import Optional, Callable, Union

import serial
from loguru import logger
from panoptes.utils import error
from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder
from serial.threaded import LineReader, ReaderThread
from serial.tools.list_ports import comports as get_comports


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

        >>> from panoptes.utils.serial.device import SerialDeviceDefaults
        >>> serial_defaults = SerialDeviceDefaults(baudrate=115200)
        >>> serial_defaults
        SerialDeviceDefaults(baudrate=115200, timeout=1.0, write_timeout=1.0, bytesize=8, parity='N', stopbits=1, xonxoff=False, rtscts=False, dsrdtr=False)
        >>> serial_defaults.write_timeout = 2.5
        >>> serial_defaults.to_dict()
        {'baudrate': 115200, 'timeout': 1.0, 'write_timeout': 2.5, 'bytesize': 8, 'parity': 'N', 'stopbits': 1, 'xonxoff': False, 'rtscts': False, 'dsrdtr': False}
        >>> serial_defaults.to_json()
        '{"baudrate": 115200, "timeout": 1.0, "write_timeout": 2.5, "bytesize": 8, "parity": "N", "stopbits": 1, "xonxoff": false, "rtscts": false, "dsrdtr": false}'

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
        return {field: getattr(self, field) for field in self.__dataclass_fields__.keys()}

    def to_json(self):
        """Return fields as serialized json."""
        return json.dumps(self, default=pydantic_encoder)


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


class BaseSerialReader(LineReader):  # pragma: no cover
    def connection_made(self, transport):
        super(BaseSerialReader, self).connection_made(transport)

    def handle_line(self, data):
        logger.debug(f"line received: {data!r}")

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)


class SerialDevice(object):
    def __init__(self,
                 port: str = None,
                 name: str = None,
                 reader_callback: Callable = None,
                 serial_settings: Optional[Union[SerialDeviceDefaults, dict]] = None,
                 retry_limit: int = 1,
                 retry_delay: float = 0.01,
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
            >>> str(dev0)
            'My device on port=loop:// [9600/8-N-1]'
            >>> dev0.write('Hello World!')
            >>> len(dev0.readings)
            1
            >>> dev0.readings[0] == 'Hello World!'

            >>> # We can also pass a callback for the reader.
            >>> from panoptes.utils.serializers import from_json, to_json
            >>> dev1 = SerialDevice(port='loop://', reader_callback=from_json)
            >>> str(dev1)
            'SerialDevice loop:// [9600/8-N-1]"
            >>> dev1.write(to_json(dict(message='Hello JSON World!')))
            >>> len(dev0.readings)
            1
            >>> dev0.readings[0]
            '{"message": "Hello JSON World!"}'


        Args:
            port (str): The port (e.g. /dev/tty123 or socket://host:port) to which to
                open a connection.
            name (str): Name of this object. Defaults to the name of the port.
            reader_callback (Callable): A callback function that should take a single
                string parameter, process it in some manner, and then return a single
                entry, which is stored in the `readings` deque.
            serial_settings (dict): The settings to apply to the serial device. See
                docstring for details.
            retry_limit (int, optional): Number of times to try serial `read`.
            retry_delay (float, optional): Delay between calls to serial `read`.
            reader_queue_size (int, optional): The size of the deque for readings,
                default 50.

        Raises:
            ValueError: If the serial parameters are invalid (e.g. a negative baudrate).

        """
        self.name = name or port
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        self.readings = deque(maxlen=reader_queue_size)
        self.reader_thread = None

        self.serial: serial.Serial = serial.serial_for_url(port)
        logger.info(f'SerialDevice for {self.name} created. Connected={self.is_connected}')

        serial_settings = serial_settings or SerialDeviceDefaults()
        if isinstance(serial_settings, SerialDeviceDefaults):
            serial_settings = serial_settings.to_dict()
        logger.info(f'Applying settings to serial class: {serial_settings!r}')
        self.serial.apply_settings(serial_settings)

        # Set up a custom threaded reader class.
        class CustomReader(BaseSerialReader):
            def handle_line(this, data):
                if callable(reader_callback):
                    try:
                        data = reader_callback(data)
                    except Exception as e:
                        logger.warning(f'Callback for serial reader error: {e!r}')

                self.readings.append(data)

        self.reader_thread = ReaderThread(self.serial, CustomReader)
        self.reader_thread.start()

    @property
    def port(self):
        """Name of the port."""
        return self.serial.port

    @property
    def is_connected(self):
        """True if serial port is open, False otherwise."""
        return self.serial.is_open

    def write(self, line):
        """Write to the serial device.

        Note that this expects unicode and will handle adding a newline at the
        end.
        """
        return self.reader_thread.protocol.write_line(line)

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
