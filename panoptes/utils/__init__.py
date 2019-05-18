from .version import __version__

try:
    _PANOPTES_SETUP_
except NameError:
    _PANOPTES_SETUP_ = False

if not _PANOPTES_SETUP_:
    from .time import *
    from .utils import *
