from pathlib import Path

import typer

from panoptes.utils.images import cr2

app = typer.Typer()


@app.command('convert-cr2')
def cr2_to_fits(file_path: Path, remove_cr2: bool = True) -> Path:
    """Convert a CR2 image to a FITS, return the new path name."""
    print(f'Converting {file_path} to FITS')
    fits_fn = cr2.cr2_to_fits(file_path, remove_cr2=remove_cr2)
    print(f'FITS file available at {fits_fn}')

    return Path(fits_fn)


if __name__ == "__main__":
    app()
