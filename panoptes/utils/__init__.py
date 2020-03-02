import logging
from logging import NullHandler

from .utils import *
from .time import *

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

logging.getLogger(__name__).addHandler(NullHandler())
