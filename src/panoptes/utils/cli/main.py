import sys

import typer
from loguru import logger

from panoptes.utils.cli import image, telemetry

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
app.add_typer(telemetry.app, name="telemetry", help="Run the telemetry server.")

if __name__ == "__main__":
    app()
