from pathlib import Path

import typer
from rich import print
from watchfiles import Change, watch

from panoptes.utils import error
from panoptes.utils.images import cr2
from panoptes.utils.images import fits as fits_utils

app = typer.Typer(rich_markup_mode="rich", no_args_is_help=True)

cr2_app = typer.Typer(rich_markup_mode="rich", no_args_is_help=True)
app.add_typer(cr2_app, name="cr2")

fits_app = typer.Typer(rich_markup_mode="rich", no_args_is_help=True)
app.add_typer(fits_app, name="fits")


@app.command("watch")
def watch_directory(
    path: Path,
    to_jpg: bool = True,
    to_fits: bool = True,
    solve: bool = True,
    overwrite: bool = False,
    remove_cr2: bool = False,
) -> None:
    """Watch a directory for changes and process any new files.

    The files will be processed according to the boolean flags, with the flag
    names corresponding to other image commands.

    By default, all the flags are enabled, which will:

       * Extract JPG files from a CR2.
       * Convert CR2 files to FITS.
       * Plate-solve FITS files.

    """
    print(f"[green]Watching {path}[/green]")
    for changes in watch(path):
        for change in changes:
            change_type = change[0]
            change_path = Path(change[1])

            if change_type == Change.added:
                if change_path.suffix == ".cr2":
                    if to_jpg:
                        print(f"Converting {change_path} to JPG")
                        try:
                            cr2_to_jpg(
                                change_path,
                                overwrite=overwrite,
                                remove_cr2=remove_cr2 and not to_fits,
                            )
                        except Exception as e:
                            print(f"[red]Error converting {change_path} to JPG: {e}[/red]")
                    if to_fits:
                        print(f"Converting {change_path} to FITS")
                        try:
                            cr2_to_fits(change_path, remove_cr2=remove_cr2, overwrite=overwrite)
                        except Exception as e:
                            print(f"[red]Error converting {change_path} to FITS: {e}[/red]")
                if change_path.suffix == ".fits":
                    if solve:
                        print(f"Solving {change_path}")
                        try:
                            solve_fits(change_path)
                        except Exception as e:
                            print(f"[red]Error solving {change_path}: {e}[/red]")


@cr2_app.command("to-jpg")
def cr2_to_jpg(
    cr2_fname: Path,
    jpg_fname: str = None,
    title: str = "",
    overwrite: bool = False,
    remove_cr2: bool = False,
) -> Path | None:
    """Extract a JPG image from a CR2, return the new path name.

    Args:
        cr2_fname (Path): Path to the CR2 file.
        jpg_fname (str): Path to the JPG file.
        title (str): Title to use for the JPG file.
        overwrite (bool): Overwrite existing JPG file.
        remove_cr2 (bool): Remove the CR2 file after conversion.
    """
    print(f"[green]Converting {cr2_fname} to JPG[/green]")
    jpg_fname = cr2.cr2_to_jpg(
        cr2_fname,
        jpg_fname=jpg_fname,
        title=title,
        overwrite=overwrite,
        remove_cr2=remove_cr2,
    )

    if jpg_fname.exists():
        print(f"[green]Wrote {jpg_fname}[/green]")

    return jpg_fname


@cr2_app.command("to-fits")
def cr2_to_fits(
    cr2_fname: Path,
    fits_fname: str = None,
    overwrite: bool = True,
    remove_cr2: bool = False,
) -> Path:
    """Convert a CR2 image to a FITS, return the new path name."""
    print(f"[green]Converting {cr2_fname} to FITS[/green]")
    fits_fn = cr2.cr2_to_fits(cr2_fname, fits_fname=fits_fname, overwrite=overwrite, remove_cr2=remove_cr2)

    if fits_fname is not None:
        print(f"[green]FITS file available at {fits_fn}[/green]")
        return Path(fits_fn)


@fits_app.command("solve")
def solve_fits(fits_fname: Path, **kwargs) -> Path | None:  # noqa: ANN003
    """Plate-solve a FITS file."""
    print(f"[green]Solving {fits_fname}[/green]")
    try:
        solve_info = fits_utils.get_solve_field(fits_fname, **kwargs)
    except error.InvalidSystemCommand as e:
        print(f"[red]Error while trying to solve {fits_fname}: {e!r}[/red]")
        return None

    solve_fn = solve_info["solved_fits_file"]

    print(f"[green]Plate-solved file available at {solve_fn}[/green]")
    return Path(solve_fn)


if __name__ == "__main__":
    app()
