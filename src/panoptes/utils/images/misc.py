import os
import shutil
import subprocess
from contextlib import suppress

import numpy as np
from astropy import units as u
from astropy.nddata import Cutout2D
from loguru import logger

from panoptes.utils import error


def make_timelapse(
        directory,
        fn_out=None,
        glob_pattern='20[1-9][0-9]*T[0-9]*.jpg',
        overwrite=False,
        timeout=60,
        **kwargs):  # pragma: no cover
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

    .. plot::
        :include-source:

        >>> from matplotlib import pyplot as plt
        >>> from astropy.wcs import WCS
        >>> from panoptes.utils.images.misc import crop_data
        >>> from panoptes.utils.images.plot import add_colorbar, get_palette
        >>> from panoptes.utils.images.fits import getdata
        >>>
        >>> fits_url = 'https://github.com/panoptes/panoptes-utils/raw/develop/tests/data/solved.fits.fz'
        >>> data, header = getdata(fits_url, header=True)
        >>> wcs = WCS(header)
        >>> # Crop a portion of the image by WCS and get Cutout2d object.
        >>> cropped = crop_data(data, center=(600, 400), box_width=100, wcs=wcs, data_only=False)
        >>> fig, ax = plt.subplots()
        >>> im = ax.imshow(cropped.data, origin='lower', cmap=get_palette())
        >>> add_colorbar(im)
        >>> plt.show()


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


def mask_saturated(data, saturation_level=None, threshold=0.9, bit_depth=None, dtype=None):
    """Convert data to a masked array with saturated values masked.

    .. plot::
        :include-source:

        >>> from matplotlib import pyplot as plt
        >>> from astropy.wcs import WCS
        >>> from panoptes.utils.images.misc import crop_data, mask_saturated
        >>> from panoptes.utils.images.plot import add_colorbar, get_palette
        >>> from panoptes.utils.images.fits import getdata
        >>>
        >>> fits_url = 'https://github.com/panoptes/panoptes-utils/raw/develop/tests/data/solved.fits.fz'
        >>> data, header = getdata(fits_url, header=True)
        >>> wcs = WCS(header)
        >>> # Crop a portion of the image by WCS and get Cutout2d object.
        >>> cropped = crop_data(data, center=(600, 400), box_width=100, wcs=wcs, data_only=False)
        >>> masked = mask_saturated(cropped.data, saturation_level=11535)
        >>> fig, ax = plt.subplots()
        >>> im = ax.imshow(masked, origin='lower', cmap=get_palette())
        >>> add_colorbar(im)
        >>> fig.show()


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
