import operator
import time
from contextlib import suppress

import serial
from deprecated import deprecated
from loguru import logger
from serial.tools.list_ports import comports as get_comports

from panoptes.utils import error
from panoptes.utils import serializers


@deprecated(reason='Use panoptes.utils.serial.device')
def get_serial_port_info():
    """Returns the serial ports defined on the system.

    Returns: a list of PySerial's ListPortInfo objects. See:
        https://github.com/pyserial/pyserial/blob/master/serial/tools/list_ports_common.py
    """
    return sorted(get_comports(), key=operator.attrgetter('device'))


@deprecated(reason='Use panoptes.utils.serial.device')
def find_serial_port(vendor_id, product_id, return_all=False):  # pragma: no cover
    """Finds the serial port that matches the given vendor and product id.

    .. doctest::

        >>> from panoptes.utils.rs232 import find_serial_port
        >>> vendor_id = 0x2a03  # arduino
        >>> product_id = 0x0043 # Uno Rev 3
        >>> find_serial_port(vendor_id, product_id)  # doctest: +SKIP
        '/dev/ttyACM0'

        >>> # Raises error when not found.
        >>> find_serial_port(0x1234, 0x4321)
        Traceback (most recent call last):
          ...
        panoptes.utils.error.NotFound: NotFound: No serial ports for vendor_id=4660 and product_id=17185

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


@deprecated(reason='Use panoptes.utils.serial.device')
class SerialData(object):
    """SerialData wraps a PySerial instance for reading from and writing to a serial device.

    Because POCS is intended to be very long running, and hardware may be turned off when unused
    or to force a reset, this wrapper may or may not have an open connection to the underlying
    serial device. Note that for most devices, is_connected will return true if the device is
    turned off/unplugged after a connection is opened; the code will only discover there is a
    problem when we attempt to interact with the device.

    .. doctest::

        >>> from panoptes.utils.rs232 import SerialData
        >>> # Connect to our fake buffered device
        >>> device_listener = SerialData(port='loop://')
        >>> device_listener.is_connected
        True
        >>> device_listener.port
        'loop://'
        >>> # Device sends event
        >>> bytes = device_listener.write('Hello World')
        >>> device_listener.read(bytes)
        'Hello World'
    """

    def __init__(self,
                 port=None,
                 baudrate=115200,
                 name=None,
                 timeout=2.0,
                 open_delay=0.0,
                 retry_limit=5,
                 retry_delay=0.5,
                 **kwargs
                 ):
        """Create a SerialData instance and attempt to open a connection.

        The device need not exist at the time this is called, in which case is_connected will
        be false.

        Args:
            port: The port (e.g. /dev/tty123 or socket://host:port) to which to
                open a connection.
            baudrate: For true serial lines (e.g. RS-232), sets the baud rate of
                the device.
            name: Name of this object. Defaults to the name of the port.
            timeout (float, optional): Timeout in seconds for both read and write.
                Defaults to 2.0.
            open_delay: Seconds to wait after opening the port.
            retry_limit: Number of times to try readline() calls in read().
            retry_delay: Delay between readline() calls in read().

        Raises:
            ValueError: If the serial parameters are invalid (e.g. a negative baudrate).

        """
        self.logger = logger

        if not port:
            raise ValueError('Must specify port for SerialData')

        self.name = name or port
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay

        self.ser = serial.serial_for_url(port, do_not_open=True)

        # Configure the PySerial class.
        self.ser.baudrate = baudrate
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = timeout
        self.ser.write_timeout = timeout
        self.ser.xonxoff = False
        self.ser.rtscts = False
        self.ser.dsrdtr = False

        self.logger.debug(f'SerialData for {self.name} created')

        # Properties have been set to reasonable values, ready to open the port.
        try:
            self.connect()
        except serial.serialutil.SerialException as err:  # pragma: no cover
            self.logger.debug(f'Unable to open {self.name}. Error: {err}')
            return

        open_delay = max(0.0, float(open_delay))
        if open_delay > 0.0:
            self.logger.debug(f'Opened {self.name}, sleeping for {open_delay} seconds')
            time.sleep(open_delay)
        else:
            self.logger.debug(f'Opened {self.name}')

    @property
    def port(self):
        """Name of the port."""
        return self.ser.port

    @property
    def is_connected(self):
        """True if serial port is open, False otherwise."""
        return self.ser.is_open

    def connect(self):
        """If disconnected, then connect to the serial port.

        Raises:
            error.BadSerialConnection if unable to open the connection.
        """
        if self.is_connected:
            self.logger.debug(f'Connection already open to {self.name}')
            return
        self.logger.debug(f'SerialData.connect called for {self.name}')
        try:
            # Note: we must not call open when it is already open, else an exception is thrown of
            # the same type thrown when open fails to actually open the device.
            self.ser.open()
            if not self.is_connected:  # pragma: no cover
                raise error.BadSerialConnection(msg=f'Serial connection {self.name} is not open')
        except serial.serialutil.SerialException as err:
            raise error.BadSerialConnection(msg=err)
        self.logger.debug(f'Serial connection established to {self.name}')

    def disconnect(self):
        """Closes the serial connection.

        Raises:
            error.BadSerialConnection if unable to close the connection.
        """
        # Fortunately, close() doesn't throw an exception if already closed.
        self.logger.debug(f'SerialData.disconnect called for {self.name}')
        try:
            self.ser.close()
        except Exception as e:  # pragma: no cover
            raise error.BadSerialConnection(msg=f'disconnect failed for {self.name}; {e!r}')
        if self.is_connected:  # pragma: no cover
            raise error.BadSerialConnection(msg=f'SerialData.disconnect failed for {self.name}')

    def write_bytes(self, data):
        """Write data of type bytes."""
        return self.ser.write(data)

    def write(self, value):
        """Write value (a string) after encoding as bytes."""
        return self.write_bytes(value.encode())

    def read_bytes(self, size=1):
        """Reads size bytes from the serial port.

        If a read timeout is set on self.ser, this may return less characters than requested.
        With no timeout it will block until the requested number of bytes is read.

        Args:
            size: Number of bytes to read.
        Returns:
            Bytes read from the port.
        """
        return self.ser.read(size=size)

    def read(self, retry_limit=None, retry_delay=None):
        """Reads next line of input using readline.

        If no response is given, delay for retry_delay and then try to read
        again. Fail after retry_limit attempts.
        """
        if retry_limit is None:
            retry_limit = self.retry_limit
        if retry_delay is None:
            retry_delay = self.retry_delay

        data = ''
        for _ in range(retry_limit):
            line = self.ser.readline()
            if line:
                data = line.decode(encoding='ascii')
                break
            time.sleep(retry_delay)

        return data

    def get_reading(self):
        """Reads and returns a line, along with the timestamp of the read.

        Returns:
            A pair (tuple) of (timestamp, line). The timestamp is the time of completion of the
            readline operation.
        """
        # Get the timestamp after the read so that a long delay on reading doesn't make it
        # appear that the read happened much earlier than it did.
        line = self.read()
        ts = time.strftime('%Y-%m-%dT%H:%M:%S %Z', time.gmtime())
        info = (ts, line)
        return info

    def get_and_parse_reading(self, retry_limit=5):
        """Reads a line of JSON text and returns the decoded value, along with the current time.

        Args:
            retry_limit: Number of lines to read in an attempt to get one that parses as JSON.

        Returns:
            A pair (tuple) of (timestamp, decoded JSON line). The timestamp is the time of
            completion of the readline operation.
        """
        reading = None
        for _ in range(max(1, retry_limit)):
            (ts, line) = self.get_reading()

            with suppress(error.InvalidDeserialization, TypeError):
                data = serializers.from_json(line)
                if data:
                    reading = (ts, data)
                    break

        return reading

    def reset_input_buffer(self):
        """Clear buffered data from connected port/device.

        Note that Wilfred reports that the input from an Arduino can seriously lag behind
        realtime (e.g. 10 seconds), and that clear_buffer may exist for that reason (i.e. toss
        out any buffered input from a device, and then read the next full line, which likely
        requires tossing out a fragment of a line).
        """
        self.ser.reset_input_buffer()

    def __del__(self):
        """Close the serial device on delete.

        This is to avoid leaving a file or device open if there are multiple references
        to the serial.Serial object.
        """
        try:
            # If an exception is thrown when running __init__, then self.ser may not have
            # been set, in which case reading that field will generate a AttributeError.
            ser = self.ser
        except AttributeError:
            return
        if ser and ser.is_open:
            ser.close()
