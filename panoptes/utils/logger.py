import os
from loguru import logger


def get_root_logger(profile='panoptes', log_dir=None):
    """Creates a root logger for PANOPTES used by the PanBase object.

    Args:
        profile (str, optional): The name of the logger to use, defaults to 'panoptes'.

    Returns:
        `loguru.logger`: A configured instance of the logger
    """

    # Create the directory for the per-run files.
    if log_dir is None:
        log_dir = os.getenv('PANLOG', os.path.expandvars('$PANDIR/logs'))
    os.makedirs(log_dir, exist_ok=True)

    # Serialize messages to a file.
    log_path = os.path.join(log_dir, 'panoptes_{time:YYYYMMDD!UTC}.log')
    logger.add(log_path,
               rotation='11:30',
               enqueue=True,
               serialize=True,
               backtrace=True,
               diagnose=True,
               level="DEBUG")

    # Turn on logging from this repo.
    logger.enable('panoptes')
    logger.success('{:*^80}'.format(' Starting PanLogger '))

    return logger
