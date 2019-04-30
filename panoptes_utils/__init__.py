from .version import __version__

try:
    __PANOPTES_SETUP__
except NameError:
    __PANOPTES_SETUP__ = False

if not __PANOPTES_SETUP__:
    from .time import *
    from .library import *
    from .utils import *
