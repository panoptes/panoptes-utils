import sys

import typer
from loguru import logger

from panoptes.utils.cli import image

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

if telemetry is not None:
    app.add_typer(telemetry.app, name="telemetry", help="Run the telemetry server.")
else:
    telemetry_app = typer.Typer(help="Telemetry commands require optional dependencies.")

    @telemetry_app.callback()
    def telemetry_main() -> None:
        """Placeholder telemetry command when optional dependencies are missing."""
        typer.echo(
            "Telemetry support is not available. To enable it, install the 'telemetry' extra:\n"
            "  pip install 'panoptes-utils[telemetry]'"
        )

    app.add_typer(telemetry_app, name="telemetry", help="Run the telemetry server.")

if __name__ == "__main__":
    app()
