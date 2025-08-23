import os
from _warnings import warn
from contextlib import suppress
from pathlib import Path
from typing import Optional, TextIO, BinaryIO

from panoptes.utils.images.cr2 import cr2_to_jpg
from panoptes.utils.images.fits import fits_to_jpg
from panoptes.utils.utils import normalize_file_input


def make_pretty_image(
    fname: str | Path | TextIO | BinaryIO, title=None, img_type=None, link_path=None, **kwargs
) -> Optional[Path]:
    """Make a pretty image.

    This will create a jpg file from either a CR2 (Canon) or FITS file.

    Arguments:
        fname: The path to the raw image. Can be a string path,
               pathlib.Path object, or open filehandle.
        title (None|str, optional): Title to be placed on image, default None.
        img_type (None|str, optional): Image type of fname, one of '.cr2' or '.fits'.
            The default is `None`, in which case the file extension of fname is used.
        link_path (None|str, optional): Path to location that image should be symlinked.
            The directory must exist.
        **kwargs {dict} -- Additional arguments to be passed to external script.

    Returns:
        str -- Filename of image that was created.

    """
    # Normalize file input to string for path operations
    fname_str = normalize_file_input(fname)

    if img_type is None:
        img_type = os.path.splitext(fname_str)[-1]

    if not os.path.exists(fname_str):
        warn(f"File doesn't exist, can't make pretty: {fname_str}")
        return None
    elif img_type == ".cr2":
        # Pass the original fname to cr2_to_jpg since it now handles different input types
        pretty_path = cr2_to_jpg(fname, title=title, **kwargs)
    elif img_type in [".fits", ".fz"]:
        # Pass the original fname to fits_to_jpg since it now handles different input types
        pretty_path = fits_to_jpg(fname, title=title, **kwargs)
    else:
        warn("File must be a Canon CR2 or FITS file.")
        return None

    if link_path is None or not os.path.exists(os.path.dirname(link_path)):
        return Path(pretty_path)

    # Remove existing symlink
    with suppress(FileNotFoundError):
        os.remove(link_path)

    try:
        os.symlink(pretty_path, link_path)
    except Exception as e:  # pragma: no cover
        warn(f"Can't link latest image: {e!r}")

    return Path(link_path)
