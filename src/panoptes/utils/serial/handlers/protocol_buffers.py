# This module implements a handler for serial_for_url("buffers://").

import io
import threading
from typing import Optional

from panoptes.utils.serial.handlers.protocol_no_op import NoOpSerial
from serial.serialutil import PortNotOpenError

# r_buffer and w_buffer are binary I/O buffers. read(size=N) on an instance
# of Serial reads the next N bytes from r_buffer, and write(data) appends the
# bytes of data to w_buffer.
# NOTE: The caller (a test) is responsible for resetting buffers before tests. See
# the util functions below.
SERIAL_READ_BUFFER: Optional[io.BytesIO] = None
SERIAL_WRITE_BUFFER: Optional[io.BytesIO] = None

# The above I/O buffers are not thread safe, so we need to lock them during access.
SERIAL_READ_LOCK = threading.Lock()
SERIAL_WRITE_LOCK = threading.Lock()


def reset_serial_buffers(read_data=None):
    set_serial_read_buffer(read_data)
    with SERIAL_WRITE_LOCK:
        global SERIAL_WRITE_BUFFER
        SERIAL_WRITE_BUFFER = io.BytesIO()


def set_serial_read_buffer(data):
    """Sets the r buffer to data (a bytes object)."""
    if data and not isinstance(data, (bytes, bytearray)):
        raise TypeError('data must by a bytes or bytearray object.')
    with SERIAL_READ_LOCK:
        global SERIAL_READ_BUFFER
        SERIAL_READ_BUFFER = io.BytesIO(data)


def get_serial_write_buffer():
    """Returns an immutable bytes object with the value of the w buffer."""
    with SERIAL_WRITE_LOCK:
        if SERIAL_WRITE_BUFFER:
            return SERIAL_WRITE_BUFFER.getvalue()


class BuffersSerial(NoOpSerial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def in_waiting(self):
        if not self.is_open:
            raise PortNotOpenError
        with SERIAL_READ_LOCK:
            return len(SERIAL_READ_BUFFER.getbuffer()) - SERIAL_READ_BUFFER.tell()

    def read(self, size=1):
        """Read size bytes.

        If a timeout is set it may return fewer characters than requested.
        With no timeout it will block until the requested number of bytes
        is read.

        Args:
            size: Number of bytes to read.

        Returns:
            Bytes read from the port, of type 'bytes'.

        Raises:
            SerialTimeoutException: In case a write timeout is configured for
                the port and the time is exceeded.
        """
        if not self.is_open:
            raise PortNotOpenError
        with SERIAL_READ_LOCK:
            # TODO(jamessynge): Figure out whether and how to handle timeout.
            # We might choose to generate a timeout if the caller asks for data
            # beyond the end of the buffer; or simply return what is left,
            # including nothing (i.e. bytes()) if there is nothing left.
            return SERIAL_READ_BUFFER.read(size)

    def write(self, data):
        """
        Args:
            data: The data to write.

        Returns:
            Number of bytes written.

        Raises:
            SerialTimeoutException: In case a write timeout is configured for
                the port and the time is exceeded.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must by a bytes or bytearray object.")
        if not self.is_open:
            raise PortNotOpenError
        with SERIAL_WRITE_LOCK:
            return SERIAL_WRITE_BUFFER.write(data)


Serial = BuffersSerial
