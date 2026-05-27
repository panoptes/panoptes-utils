import sys

import typer
from loguru import logger
from rich import print

from panoptes.utils.cli import image

try:
    from panoptes.utils.cli import config as config_cli
    from panoptes.utils.config import server as _config_server  # noqa: F401  # requires "config" extra
except ImportError:
    config_cli = None

try:
    from panoptes.utils.cli import telemetry
except ImportError:
    telemetry = None

app = typer.Typer()


@app.callback()
def main(verbose: bool = False):
    """PANOPTES Utilities CLI.

    Args:
        verbose: Enable DEBUG-level logging. Defaults to False (INFO level).
    """
    # Setup the logger.
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")


app.add_typer(image.app, name="image", help="Process an image.")

if config_cli is not None:
    app.add_typer(config_cli.app, name="config", help="Manage the config server.")
else:
    _config_app = typer.Typer(help="Config commands require optional dependencies.")

    @_config_app.callback()
    def _config_main() -> None:
        """Placeholder config command when optional dependencies are missing."""
        print(
            "Config support is not available. To enable it, install the 'config' extra:\n"
            "  pip install 'panoptes-utils[config]'"
        )

    app.add_typer(_config_app, name="config", help="Manage the config server.")

if telemetry is not None:
    app.add_typer(telemetry.app, name="telemetry", help="Run the telemetry server.")
else:
    telemetry_app = typer.Typer(help="Telemetry commands require optional dependencies.")

    @telemetry_app.callback()
    def telemetry_main() -> None:
        """Placeholder telemetry command when optional dependencies are missing."""
        print(
            "Telemetry support is not available. To enable it, install the 'telemetry' extra:\n"
            "  pip install 'panoptes-utils[telemetry]'"
        )

    app.add_typer(telemetry_app, name="telemetry", help="Run the telemetry server.")

if __name__ == "__main__":
    app()
