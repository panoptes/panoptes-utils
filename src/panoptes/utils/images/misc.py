import os
import shutil
import subprocess
from _warnings import warn
from contextlib import suppress
from pathlib import Path
from typing import Optional

import numpy as np
from astropy import units as u
from astropy.nddata import Cutout2D
from loguru import logger

from panoptes.utils import error
from panoptes.utils.images.cr2 import cr2_to_jpg
from panoptes.utils.images.fits import fits_to_jpg


def make_timelapse(
        directory,
        fn_out=None,
        glob_pattern='20[1-9][0-9]*T[0-9]*.jpg',
        overwrite=False,
        timeout=60,
        **kwargs):
    """Create a timelapse.

    A timelapse is created from all the images in given ``directory``

    Args:
        directory (str): Directory containing image files.
        fn_out (str, optional): Full path to output file name, if not provided,
            defaults to `directory` basename.
        glob_pattern (str, optional): A glob file pattern of images to include,
            default '20[1-9][0-9]*T[0-9]*.jpg', which corresponds to the observation
            images but excludes any pointing images. The pattern should be relative
            to the local directory.
        overwrite (bool, optional): Overwrite timelapse if exists, default False.
        timeout (int): Timeout for making movie, default 60 seconds.
        **kwargs (dict):

    Returns:
        str: Name of output file

    Raises:
        error.InvalidSystemCommand: Raised if ffmpeg command is not found.
        FileExistsError: Raised if fn_out already exists and overwrite=False.
    """
    if fn_out is None:
        head, tail = os.path.split(directory)
        if tail == '':
            head, tail = os.path.split(head)

        field_name = head.split('/')[-2]
        cam_name = head.split('/')[-1]
        fname = f'{field_name}_{cam_name}_{tail}.mp4'
        fn_out = os.path.normpath(os.path.join(directory, fname))

    if os.path.exists(fn_out) and not overwrite:
        raise FileExistsError("Timelapse exists. Set overwrite=True if needed")

    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        raise error.InvalidSystemCommand("ffmpeg not found, can't make timelapse")

    inputs_glob = os.path.join(directory, glob_pattern)

    try:
        ffmpeg_cmd = [
            ffmpeg,
            '-r', '3',
            '-pattern_type', 'glob',
            '-i', inputs_glob,
            '-s', 'hd1080',
            '-vcodec', 'libx264',
        ]

        if overwrite:
            ffmpeg_cmd.append('-y')

        ffmpeg_cmd.append(fn_out)

        logger.debug(ffmpeg_cmd)

        proc = subprocess.Popen(ffmpeg_cmd, universal_newlines=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            # Don't wait forever
            outs, errs = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
        finally:
            logger.debug(f"Output: {outs}")
            logger.debug(f"Errors: {errs}")

            # Double-check for file existence
            if not os.path.exists(fn_out):
                fn_out = None
    except Exception as e:
        raise error.PanError(f"Problem creating timelapse in {fn_out}: {e!r}")

    return fn_out


def crop_data(data, box_width=200, center=None, data_only=True, wcs=None, **kwargs):
    """Return a cropped portion of the image.

    Shape is a box centered around the middle of the data

    Args:
        data (`numpy.array`): Array of data.
        box_width (int, optional): Size of box width in pixels, defaults to 200px.
        center (tuple(int, int), optional): Crop around set of coords, default to image center.
        data_only (bool, optional): If True (default), return only data. If False
            return the `Cutout2D` object.
        wcs (None|`astropy.wcs.WCS`, optional): A valid World Coordinate System (WCS) that will
            be cropped along with the data if provided.

    Returns:
        np.array: A clipped (thumbnailed) version of the data if `data_only=True`, otherwise
            a `astropy.nddata.Cutout2D` object.

    """
    assert data.shape[
               0] >= box_width, f"Can't clip data, it's smaller than {box_width} ({data.shape})"
    # Get the center
    if center is None:
        x_len, y_len = data.shape
        x_center = int(x_len / 2)
        y_center = int(y_len / 2)
    else:
        y_center = int(center[0])
        x_center = int(center[1])

    logger.debug(f"Using center: {x_center} {y_center}")
    logger.debug(f"Box width: {box_width}")

    cutout = Cutout2D(data, (y_center, x_center), box_width, wcs=wcs)

    if data_only:
        return cutout.data

    return cutout


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


def mask_saturated(data, saturation_level=None, threshold=0.9, bit_depth=None, dtype=None):
    """Convert data to a masked array with saturated values masked.

    Args:
        data (array_like): The numpy data array.
        saturation_level (scalar, optional): The saturation level. If not given then the
            saturation level will be set to threshold times the maximum pixel value.
        threshold (float, optional): The fraction of the maximum pixel value to use as
            the saturation level, default 0.9.
        bit_depth (astropy.units.Quantity or int, optional): The effective bit depth of the
            data. If given the maximum pixel value will be assumed to be 2**bit_depth,
            otherwise an attempt will be made to infer the maximum pixel value from the
            data type of the data. If data is not an integer type the maximum pixel value
            cannot be inferred and an IllegalValue exception will be raised.
        dtype (numpy.dtype, optional): The requested dtype for the masked array. If not given
            the dtype of the masked array will be same as data.

    Returns:
        numpy.ma.array: The masked numpy array.

    Raises:
        error.IllegalValue: Raised if bit_depth is an astropy.units.Quantity object but the
            units are not compatible with either bits or bits/pixel.
        error.IllegalValue: Raised if neither saturation level or bit_depth are given, and data
            has a non integer data type.
    """
    if not saturation_level:
        if bit_depth is not None:
            try:
                with suppress(AttributeError):
                    bit_depth = bit_depth.to_value(unit=u.bit)
            except u.UnitConversionError:
                try:
                    bit_depth = bit_depth.to_value(unit=u.bit / u.pixel)
                except u.UnitConversionError:
                    raise error.IllegalValue("bit_depth must have units of bits or bits/pixel, " +
                                             f"got {bit_depth!r}")

            bit_depth = int(bit_depth)
            logger.trace(f"Using bit depth {bit_depth!r}")
            saturation_level = threshold * (2 ** bit_depth - 1)
        else:
            # No bit depth specified, try to guess.
            logger.trace(f"Inferring bit_depth from data type, {data.dtype!r}")
            try:
                # Try to use np.iinfo to compute machine limits. Will work for integer types.
                saturation_level = threshold * np.iinfo(data.dtype).max
            except ValueError:
                # ValueError from np.iinfo means not an integer type.
                raise error.IllegalValue("Neither saturation_level or bit_depth given, and data " +
                                         "is not an integer type. Cannot determine correct " +
                                         "saturation level.")
    logger.debug(f"Masking image using saturation level {saturation_level!r}")
    # Convert data to masked array of requested dtype, mask values above saturation level.
    return np.ma.array(data, mask=(data > saturation_level), dtype=dtype)
