from pathlib import Path

import typer

from panoptes.utils.images import cr2

app = typer.Typer()


@app.command('convert-cr2')
def cr2_to_fits(
        cr2_fname: Path,
        fits_fname: str = None,
        overwrite: bool = True,
        remove_cr2: bool = False,
) -> Path:
    """Convert a CR2 image to a FITS, return the new path name."""
    print(f'Converting {cr2_fname} to FITS')
    fits_fn = cr2.cr2_to_fits(cr2_fname,
                              fits_fname=fits_fname,
                              overwrite=overwrite,
                              remove_cr2=remove_cr2)

    if fits_fname is not None:
        print(f'FITS file available at {fits_fn}')
        return Path(fits_fn)


if __name__ == "__main__":
    app()
