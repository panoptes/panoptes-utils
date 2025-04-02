import ctypes
import ctypes.util
import importlib

from loguru import logger

from panoptes.utils import error


def load_c_library(name, path=None, mode=ctypes.DEFAULT_MODE, **kwargs):
    """Utility function to load a shared/dynamically linked library (.so/.dylib/.dll).

    The name and location of the shared library can be manually specified with the library_path
    argument, otherwise the ctypes.util.find_library function will be used to try to locate based
    on library_name.

    Args:
        name (str): name of the library (without 'lib' prefix or any suffixes, e.g. 'fli').
        path (str, optional): path to the library e.g. '/usr/local/lib/libfli.so'.
        mode (int, optional): mode in which to load the library, see dlopen(3) man page for
            details. Should be one of ctypes.RTLD_GLOBAL, ctypes.RTLD_LOCAL, or
            ctypes.DEFAULT_MODE. Default is ctypes.DEFAULT_MODE.

    Returns:
        ctypes.CDLL

    Raises:
        pocs.utils.error.NotFound: raised if library_path not given & find_library fails to
            locate the library.
        OSError: raises if the ctypes.CDLL loader cannot load the library.
    """
    if mode is None:
        # Interpret a value of None as the default.
        mode = ctypes.DEFAULT_MODE
    # Open library
    logger.debug(f"Opening {name} library")
    if not path:
        path = ctypes.util.find_library(name)
        if not path:
            raise error.NotFound(f"Cound not find {name} library!")
    # This CDLL loader will raise OSError if the library could not be loaded
    return ctypes.CDLL(path, mode=mode)


def load_module(module_name):
    """Dynamically load a module or a class from the module.

    >>> from panoptes.utils.library import load_module
    >>> error = load_module('panoptes.utils.error')
    >>> error.__name__
    'panoptes.utils.error'
    >>> error.__package__
    'panoptes.utils'
    >>> PanError = load_module('panoptes.utils.error.PanError')
    >>> PanError.__name__
    'PanError'

    Args:
        module_name (str): Name of module to import.

    Returns:
        module: an imported module name

    Raises:
        error.NotFound: If module cannot be imported.
    """
    try:
        module = importlib.import_module(module_name)
    except (ModuleNotFoundError, ImportError):
        try:
            base, cls = module_name.rsplit('.', 1)
            module = importlib.import_module(base)
            module = getattr(module, cls)
        except (ModuleNotFoundError, ImportError, AttributeError, ValueError):
            raise error.NotFound(msg=module_name)

    return module
