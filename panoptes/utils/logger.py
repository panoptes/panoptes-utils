import os
from loguru import logger


def get_logger():
    """Convenience method to return the logger.

    Returns:
        `loguru.logger`: A logging instance. Currently `loguru`.
    """
    return logger


def get_root_logger(profile='panoptes',
                    log_file='panoptes_{time:YYYYMMDD!UTC}.log',
                    log_dir=None,
                    stderr=False):
    """Creates a root logger for PANOPTES used by the PanBase object.

    Note: The `log_dir` is determined first from `$PANLOG` if it exists, then
      `$PANDIR/logs` if `$PANDIR` exists, otherwise defaults to `.`.

    Args:
        profile (str, optional): The name of the logger to use, defaults to 'panoptes'.
        log_file (str|None, optional): The filename, defaults to `panoptes_{time:YYYYMMDD!UTC}.log`.
        log_dir (str|None, optional): The directory to place the log file, see note.
        stderr (bool, optional): If the default `stderr` handler should be included,
          defaults to False.

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
    # Turn on logging from this repo.
    if stderr is False:
        logger.remove()

    handler_id = logger.add(log_path,
                            rotation='11:30',
                            enqueue=True,
                            serialize=True,
                            backtrace=True,
                            diagnose=True,
                            level="DEBUG")

    logger._handlers = {
        handler_id: log_path
    }
    logger.enable(profile)
    logger.success('{:*^80}'.format(' Starting PanLogger '))

    return logger
