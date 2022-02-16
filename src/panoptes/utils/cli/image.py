from pathlib import Path
from typing import Union

import typer

from panoptes.utils.images import cr2

app = typer.Typer()


@app.command('convert-cr2')
def cr2_to_fits(
        cr2_fname: Union[str, Path],
        fits_fname: str = None,
        overwrite: bool = False,
        fits_headers: dict = None,
        remove_cr2: bool = False,
) -> Path:
    """Convert a CR2 image to a FITS, return the new path name."""
    print(f'Converting {cr2_fname} to FITS')
    fits_fn = cr2.cr2_to_fits(cr2_fname,
                              fits_fname=fits_fname,
                              overwrite=overwrite,
                              fits_headers=fits_headers,
                              remove_cr2=remove_cr2)
    print(f'FITS file available at {fits_fn}')

    return Path(fits_fn)


if __name__ == "__main__":
    app()
