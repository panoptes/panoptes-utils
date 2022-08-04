from pathlib import Path
from typing import Optional

import typer

from panoptes.utils import error
from panoptes.utils.images import cr2
from panoptes.utils.images import fits as fits_utils

app = typer.Typer()

cr2_app = typer.Typer()
app.add_typer(cr2_app, name='cr2')

fits_app = typer.Typer()
app.add_typer(fits_app, name='fits')


@cr2_app.command('to-jpg')
def cr2_to_jpg(
        cr2_fname: Path,
        jpg_fname: str = None,
        title: str = '',
        overwrite: bool = False,
        remove_cr2: bool = False,
        verbose: bool = False,
) -> Optional[Path]:
    """Extract a JPG image from a CR2, return the new path name.

    Args:
        cr2_fname (Path): Path to the CR2 file.
        jpg_fname (str): Path to the JPG file.
        title (str): Title to use for the JPG file.
        overwrite (bool): Overwrite existing JPG file.
        remove_cr2 (bool): Remove the CR2 file after conversion.
        verbose (bool): Print verbose output.
    """
    jpg_fname = cr2.cr2_to_jpg(
        cr2_fname,
        jpg_fname=jpg_fname,
        title=title,
        overwrite=overwrite,
        remove_cr2=remove_cr2,
    )

    if jpg_fname.exists() and verbose:
        typer.secho(f'Wrote {jpg_fname}', fg='green')

    return jpg_fname


@cr2_app.command('to-fits')
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


@fits_app.command('solve')
def solve_fits(fits_fname: Path) -> Optional[Path]:
    """Plate-solve a FITS file."""
    print(f'Solving {str(fits_fname)}')
    try:
        solve_info = fits_utils.get_solve_field(fits_fname)
    except error.InvalidSystemCommand as e:
        return None

    solve_fn = solve_info['solved_fits_file']

    print(f'Plate-solved file available at {solve_fn}')
    return Path(solve_fn)


if __name__ == "__main__":
    app()
