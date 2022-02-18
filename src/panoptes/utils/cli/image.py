from pathlib import Path

import typer

from panoptes.utils import error
from panoptes.utils.images import cr2
from panoptes.utils.images import fits as fits_utils

app = typer.Typer()
cr2_app = typer.Typer()
fits_app = typer.Typer()
app.add_typer(cr2_app, name='cr2')
app.add_typer(fits_app, name='fits')


@cr2_app.command('convert')
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
def solve_fits(fits_fname: Path) -> Path:
    """Plate-solve a FITS file."""
    print(f'Solving {str(fits_fname)}')
    try:
        solve_info = fits_utils.get_solve_field(fits_fname)
    except error.InvalidSystemCommand as e:
        return

    solve_fn = solve_info['solved_fits_file']

    print(f'Plate-solved file available at {solve_fn}')
    return Path(solve_fn)


if __name__ == "__main__":
    app()
