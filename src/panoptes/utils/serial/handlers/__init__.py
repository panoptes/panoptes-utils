"""The protocol_*.py files in this package are based on PySerial's file
test/handlers/protocol_test.py, modified for different behaviors.
The call serial.serial_for_url("XYZ://") looks for a class Serial in a
file named protocol_XYZ.py in this package (i.e. directory).
"""

import serial

# Import this namespace automatically.
serial.protocol_handler_packages.append('panoptes.utils.serial.handlers')
