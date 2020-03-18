from loguru import logger


class PanLogger:

    """Custom formatter to have dynamic widths for logging.

    Also provides a `handlers` dictionary to track attached handlers by id.

    See https://loguru.readthedocs.io/en/stable/resources/recipes.html#dynamically-formatting-messages-to-properly-align-values-with-padding

    """

    def __init__(self):
        self.padding = 0
        self.fmt = "<lvl>{level:.1s}</lvl> <light-blue>{time:MM-DD HH:mm:ss.ss!UTC}</> <blue>({time:HH:mm:ss.ss})</> | <c>{name} {function}:{line}{extra[padding]}</c> | <lvl>{message}</lvl>\n"
        self.handlers = dict()

    def format(self, record):
        length = len("{name}:{function}:{line}".format(**record))
        self.padding = max(self.padding, length)
        record["extra"]["padding"] = " " * (self.padding - length)
        return self.fmt
