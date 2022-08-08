import os
from _warnings import warn
from contextlib import suppress
from pathlib import Path
from typing import Optional

from panoptes.utils.images.cr2 import cr2_to_jpg
from panoptes.utils.images.fits import fits_to_jpg


def make_pretty_image(fname,
                      title=None,
                      img_type=None,
                      link_path=None,
                      **kwargs) -> Optional[Path]:
    """Make a pretty image.

    This will create a jpg file from either a CR2 (Canon) or FITS file.

    Arguments:
        fname (str): The path to the raw image.
        title (None|str, optional): Title to be placed on image, default None.
        img_type (None|str, optional): Image type of fname, one of '.cr2' or '.fits'.
            The default is `None`, in which case the file extension of fname is used.
        link_path (None|str, optional): Path to location that image should be symlinked.
            The directory must exist.
        **kwargs {dict} -- Additional arguments to be passed to external script.

    Returns:
        str -- Filename of image that was created.

    """
    if img_type is None:
        img_type = os.path.splitext(fname)[-1]

    if not os.path.exists(fname):
        warn(f"File doesn't exist, can't make pretty: {fname}")
        return None
    elif img_type == '.cr2':
        pretty_path = cr2_to_jpg(Path(fname), title=title, **kwargs)
    elif img_type in ['.fits', '.fz']:
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
