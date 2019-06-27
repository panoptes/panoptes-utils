# This module implements a handler for serial_for_url("no_op://").

from panoptes.utils.tests.serial_handlers import NoOpSerial

# Export it as Serial so that it will be picked up by PySerial's serial_for_url.
Serial = NoOpSerial
