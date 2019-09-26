import ctypes
import ctypes.util

from astropy.utils import resolve_name
from panoptes.utils import error


def load_c_library(name, path=None, logger=None):
    """Utility function to load a shared/dynamically linked library (.so/.dylib/.dll).

    The name and location of the shared library can be manually specified with the library_path
    argument, otherwise the ctypes.util.find_library function will be used to try to locate based
    on library_name.

    Args:
        name (str): name of the library (without 'lib' prefix or any suffixes, e.g. 'fli').
        path (str, optional): path to the library e.g. '/usr/local/lib/libfli.so'.

    Returns:
        ctypes.CDLL

    Raises:
        panoptes.utils.error.NotFound: raised if library_path not given & find_libary fails to
            locate the library.
        OSError: raises if the ctypes.CDLL loader cannot load the library.
    """
    # Open library
    if logger:
        logger.debug("Opening {} library".format(name))
    if not path:
        path = ctypes.util.find_library(name)
        if not path:
            raise error.NotFound("Cound not find {} library!".format(name))
    # This CDLL loader will raise OSError if the library could not be loaded
    return ctypes.CDLL(path)


def load_module(module_name):
    """Dynamically load a module.

    >>> from panoptes.utils.library import load_module
    >>> error = load_module('panoptes.utils.error')
    >>> error.__name__
    'panoptes.utils.error'
    >>> error.__package__
    'panoptes.utils'

    Args:
        module_name (str): Name of module to import.

    Returns:
        module: an imported module name

    Raises:
        error.NotFound: If module cannot be imported.
    """
    try:
        module = resolve_name(module_name)
    except ImportError:
        raise error.NotFound(msg=module_name)

    return module
