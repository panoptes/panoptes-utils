import os
from loguru import logger


def get_root_logger(profile='panoptes',
                    log_file='panoptes_{time:YYYYMMDD!UTC}.log',
                    log_dir=None):
    """Creates a root logger for PANOPTES used by the PanBase object.

    Note: The `log_dir` is determined first from `$PANLOG` if it exists, then
      `$PANDIR/logs` if `$PANDIR` exists, otherwise defaults to `.`.

    Args:
        profile (str, optional): The name of the logger to use, defaults to 'panoptes'.
        log_file (str|None, optional): The filename, defaults to `panoptes_{time:YYYYMMDD!UTC}.log`.
        log_dir (str|None, optional): The directory to place the log file, see note.

    Returns:
        `loguru.logger`: A configured instance of the logger.
    """

    # Create the directory for the per-run files.
    if log_dir is None:
        try:
            log_dir = os.environ['PANLOG']
        except KeyError:
            log_dir = os.path.join(os.getenv('PANDIR', '.'), 'logs')
    log_dir = os.path.normpath(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    # Serialize messages to a file.
    log_path = os.path.normpath(os.path.join(log_dir, log_file))
    logger.add(log_path,
               rotation='11:30',
               enqueue=True,
               serialize=True,
               backtrace=True,
               diagnose=True,
               level="DEBUG")

    # Turn on logging from this repo.
    logger.enable(profile)
    logger.success('{:*^80}'.format(' Starting PanLogger '))

    return logger
