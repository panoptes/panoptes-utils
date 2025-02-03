from decimal import Decimal
from enum import IntEnum

import numpy as np
from astropy.io import fits
from astropy.stats import SigmaClip
from loguru import logger
from photutils.background import Background2D
from photutils.background import BkgZoomInterpolator
from photutils.background import MMMBackground
from photutils.background import MeanBackground
from photutils.background import MedianBackground
from photutils.background import SExtractorBackground

from panoptes.utils.images import fits as fits_utils


class RGB(IntEnum):
    """Helper class for array index access."""
    RED = 0
    R = 0
    GREEN = 1
    G = 1
    G1 = 1
    BLUE = 2
    B = 2


def get_rgb_data(data, separate_green=False):
    """Get the data split into separate channels for RGB.

    `data` can be a 2D (`W x H`) or 3D (`N x W x H`) array where W=width
    and H=height of the data, with N=number of frames.

    The return array will be a `3 x W x H` or `3 x N x W x H` array.

    The Bayer array defines a superpixel as a collection of 4 pixels
    set in a square grid::

                     R G
                     G B

    `ds9` and other image viewers define the coordinate axis from the
    lower left corner of the image, which is how a traditional x-y plane
    is defined and how most images would expect to look when viewed. This
    means that the `(0, 0)` coordinate position will be in the lower left
    corner of the image.

    When the data is loaded into a `numpy` array the data is flipped on the
    vertical axis in order to maintain the same indexing/slicing features.
    This means the the ``(0, 0)`` coordinate position is in the upper-left
    corner of the array when output. When plotting this array one can use
    the ``origin='lower'`` option to view the array as would be expected in
    a normal image although this does not change the actual index.

    Image dimensions::

         ----------------------------
         x | width  | i | columns |  5208
         y | height | j | rows    |  3476

    Bayer pattern as seen in ds9::

                                      x / j

                      0     1    2     3 ... 5204 5205 5206 5207
                    --------------------------------------------
               3475 |  R   G1    R    G1        R   G1    R   G1
               3474 | G2    B   G2     B       G2    B   G2    B
               3473 |  R   G1    R    G1        R   G1    R   G1
               3472 | G2    B   G2     B       G2    B   G2    B
                  . |
         y / i    . |
                  . |
                  3 |  R   G1    R    G1        R   G1    R   G1
                  2 | G2    B   G2     B       G2    B   G2    B
                  1 |  R   G1    R    G1        R   G1    R   G1
                  0 | G2    B   G2     B       G2    B   G2    B

    The RGGB super-pixels thus start in the upper-left.

    Bayer pattern as seen in a numpy array::

                                      x / j

                      0     1    2     3 ... 5204 5205 5206 5207
                    --------------------------------------------
                  0 | G2    B   G2     B       G2    B   G2    B
                  1 |  R   G1    R    G1        R   G1    R   G1
                  2 | G2    B   G2     B       G2    B   G2    B
                  3 |  R   G1    R    G1        R   G1    R   G1
                  . |
         y / i    . |
                  . |
               3472 | G2    B   G2     B       G2    B   G2    B
               3473 |  R   G1    R    G1        R   G1    R   G1
               3474 | G2    B   G2     B       G2    B   G2    B
               3475 |  R   G1    R    G1        R   G1    R   G1

    Here the RGGB super-pixels are flipped upside down.

    In both cases the data is in the following format::

                 | row (y) |  col (x)
             --------------| ------
              R  |  odd i, |  even j
              G1 |  odd i, |   odd j
              G2 | even i, |  even j
              B  | even i, |   odd j

    And a mask can therefore be generated as::

            bayer[1::2, 0::2] = 1 # Red
            bayer[1::2, 1::2] = 1 # Green
            bayer[0::2, 0::2] = 1 # Green
            bayer[0::2, 1::2] = 1 # Blue

    """
    rgb_masks = get_rgb_masks(data, separate_green=separate_green)

    color_data = list()

    # Red
    color_data.append(np.ma.array(data, mask=rgb_masks[0]))

    # Green
    color_data.append(np.ma.array(data, mask=rgb_masks[1]))

    if separate_green:
        color_data.append(np.ma.array(data, mask=rgb_masks[2]))

    # Blue
    color_data.append(np.ma.array(data, mask=rgb_masks[-1]))

    return np.ma.array(color_data)


def get_rgb_masks(data, separate_green=False):
    """Get the RGGB Bayer pattern for the given data.

    .. note::

        See :py:func:`get_rgb_data` for a description of the RGGB pattern.

    Args:
        data (`np.array`): An array of data representing an image.
        separate_green (bool, optional): If the two green channels should be separated,
            default False.

    Returns:
        tuple(np.array, np.array, np.array): A 3-tuple of numpy arrays of `bool` type.
    """

    r_mask = np.ones_like(data).astype(bool)
    g1_mask = np.ones_like(data).astype(bool)
    b_mask = np.ones_like(data).astype(bool)

    if separate_green:
        g2_mask = np.ones_like(data).astype(bool)
    else:
        g2_mask = g1_mask

    if data.ndim == 2:
        r_mask[1::2, 0::2] = False
        g1_mask[1::2, 1::2] = False
        g2_mask[0::2, 0::2] = False
        b_mask[0::2, 1::2] = False
    elif data.ndim == 3:
        r_mask[..., 1::2, 0::2] = False
        g1_mask[..., 1::2, 1::2] = False
        g2_mask[..., 0::2, 0::2] = False
        b_mask[..., 0::2, 1::2] = False
    else:
        raise TypeError('Only 2D and 3D data allowed')

    if separate_green:
        return np.array([r_mask, g1_mask, g2_mask, b_mask])
    else:
        return np.array([r_mask, g1_mask, b_mask])


def get_pixel_color(x, y):
    """ Given a zero-indexed x,y position, return the corresponding color.

    .. note::

        See :py:func:`get_rgb_data` for a description of the RGGB pattern.

    Returns:
        str: one of 'R', 'G1', 'G2', 'B'
    """
    x = int(x)
    y = int(y)
    if x % 2 == 0:
        if y % 2 == 0:
            return 'G2'
        else:
            return 'R'
    else:
        if y % 2 == 0:
            return 'B'
        else:
            return 'G1'


def get_stamp_slice(x, y, stamp_size=(14, 14), ignore_superpixel=False, as_slices=True):
    """Get the slice around a given position with fixed Bayer pattern.

    Given an x,y pixel position, get the slice object for a stamp of a given size
    but make sure the first position corresponds to a red-pixel. This means that
    x,y will not necessarily be at the center of the resulting stamp.

    .. doctest::

        >>> from panoptes.utils.images import bayer
        >>> # Make a super-pixel as represented in numpy (see full stamp below).
        >>> superpixel = np.array(['G2', 'B', 'R', 'G1']).reshape(2, 2)
        >>> superpixel
        array([['G2', 'B'],
               ['R', 'G1']], dtype='<U2')
        >>> # Tile it into a 5x5 grid of super-pixels, i.e. a 10x10 stamp.
        >>> stamp0 = np.tile(superpixel, (5, 5))
        >>> stamp0
        array([['G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1'],
               ['G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1'],
               ['G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1'],
               ['G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1'],
               ['G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1', 'R', 'G1']],
              dtype='<U2')
        >>> stamp1 = np.arange(100).reshape(10, 10)
        >>> stamp1
        array([[ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9],
               [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
               [20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
               [30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
               [40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
               [50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
               [60, 61, 62, 63, 64, 65, 66, 67, 68, 69],
               [70, 71, 72, 73, 74, 75, 76, 77, 78, 79],
               [80, 81, 82, 83, 84, 85, 86, 87, 88, 89],
               [90, 91, 92, 93, 94, 95, 96, 97, 98, 99]])
        >>> x = 7
        >>> y = 5
        >>> pixel_index = (y, x)  # y=rows, x=columns
        >>> str(stamp0[pixel_index])
        'G1'
        >>> int(stamp1[pixel_index])
        57
        >>> slice0 = bayer.get_stamp_slice(x, y, stamp_size=(6, 6))
        >>> slice0
        (slice(2, 8, None), slice(4, 10, None))
        >>> stamp0[slice0]
        array([['G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1'],
               ['G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1'],
               ['G2', 'B', 'G2', 'B', 'G2', 'B'],
               ['R', 'G1', 'R', 'G1', 'R', 'G1']], dtype='<U2')
        >>> stamp1[slice0]
        array([[24, 25, 26, 27, 28, 29],
               [34, 35, 36, 37, 38, 39],
               [44, 45, 46, 47, 48, 49],
               [54, 55, 56, 57, 58, 59],
               [64, 65, 66, 67, 68, 69],
               [74, 75, 76, 77, 78, 79]])
        >>> # Return y_min, y_max, x_min, x_max
        >>> bayer.get_stamp_slice(x, y, stamp_size=(6, 6), as_slices=False)
        (2, 8, 4, 10)

    The original index had a value of `57`, which is within the center superpixel.

    Notice that the resulting stamp has a super-pixel in the center and is bordered on all sides by a complete
    superpixel. This is required by default and an invalid size

    We can use `ignore_superpixel=True` to get an odd-sized stamp.

    .. doctest::

        >>> slice1 = bayer.get_stamp_slice(x, y, stamp_size=(5, 5), ignore_superpixel=True)
        >>> slice1
        (slice(3, 8, None), slice(5, 10, None))
        >>> stamp0[slice1]
        array([['G1', 'R', 'G1', 'R', 'G1'],
               ['B', 'G2', 'B', 'G2', 'B'],
               ['G1', 'R', 'G1', 'R', 'G1'],
               ['B', 'G2', 'B', 'G2', 'B'],
               ['G1', 'R', 'G1', 'R', 'G1']], dtype='<U2')
        >>> stamp1[slice1]
        array([[35, 36, 37, 38, 39],
               [45, 46, 47, 48, 49],
               [55, 56, 57, 58, 59],
               [65, 66, 67, 68, 69],
               [75, 76, 77, 78, 79]])

    This puts the requested pixel in the center but does not offer any
    guarantees about the RGGB pattern.

    Args:
        x (float): X pixel position.
        y (float): Y pixel position.
        stamp_size (tuple, optional): The size of the cutout, default (14, 14).
        ignore_superpixel (bool): If superpixels should be ignored, default False.
        as_slices (bool): Return slice objects, default True. Otherwise returns:
            y_min, y_max, x_min, x_max
    Returns:
        `list(slice, slice)` or `list(int, int, int, int)`: A list of row and
            column slice objects or a list defining the bounding box:
            y_min, y_max, x_min, x_max. Return type depends on the `as_slices`
            parameter and defaults to a list of two slices.
    """
    # Make sure requested size can have superpixels on each side.
    if not ignore_superpixel:
        for side_length in stamp_size:
            side_length -= 2  # Subtract center superpixel
            if side_length / 2 % 2 != 0:
                raise RuntimeError(f"Invalid slice size: {side_length + 2} "
                                   f"Slice must have even number of pixels on each side"
                                   f"of center superpixel. i.e. 6, 10, 14, 18...")

    # Pixels have nasty 0.5 rounding issues
    x = Decimal(float(x)).to_integral()
    y = Decimal(float(y)).to_integral()
    color = get_pixel_color(x, y)
    logger.debug(f'Found color={color} for x={x} y={y}')

    x_half = int(stamp_size[0] / 2)
    y_half = int(stamp_size[1] / 2)

    x_min = int(x - x_half)
    x_max = int(x + x_half)

    y_min = int(y - y_half)
    y_max = int(y + y_half)

    # Alter the bounds depending on identified center pixel so we always center superpixel have:
    #   G2 B
    #   R  G1
    if color == 'R':
        x_min += 1
        x_max += 1
    elif color == 'G2':
        x_min += 1
        x_max += 1
        y_min += 1
        y_max += 1
    elif color == 'B':
        y_min += 1
        y_max += 1

    # if stamp_size is odd add extra
    if stamp_size[0] % 2 == 1:
        x_max += 1
        y_max += 1

    logger.debug(f'x_min={x_min}, x_max={x_max}, y_min={y_min}, y_max={y_max}')

    if as_slices:
        return slice(y_min, y_max), slice(x_min, x_max)
    else:
        return y_min, y_max, x_min, x_max


def get_rgb_background(data,
                       box_size=(79, 84),
                       filter_size=(11, 11),
                       estimator='mmm',
                       interpolator='zoom',
                       sigma=5,
                       iters=10,
                       exclude_percentile=100,
                       return_separate=False,
                       *args,
                       **kwargs
                       ):
    """Get the background for each color channel.

    Note: This funtion does not perform any additional calibration, such as flat, bias,
    or dark correction. It is expected you have performed any necessary pre-processing
    to `data` before passing to this function.

    By default this uses a box size of (79, 84), which gives an integer number
    of boxes. The size of the median filter box for the low resolution background
    is on the order of the stamp size.

    Most of the options are described in the `photutils.background.Background2D` page:
    https://photutils.readthedocs.io/en/stable/background.html#d-background-and-noise-estimation

    >>> from panoptes.utils.images.bayer import RGB
    >>> from panoptes.utils.images import fits as fits_utils
    >>> # Get our data and pre-process (basic bias subtract here).
    >>> fits_fn = getfixture('solved_fits_file')
    >>> camera_bias = 2048
    >>> data = fits_utils.getdata(fits_fn).astype(float) - camera_bias

    >> The default is to return a single array for the background.
    >>> rgb_back = get_rgb_background(data)
    >>> float(rgb_back.mean())
    136...
    >>> float(rgb_back.std())
    36...

    >>> # Can also return the Background2D objects, which is the input to save_rgb_bg_fits
    >>> rgb_backs = get_rgb_background(data, return_separate=True)
    >>> print(rgb_backs[RGB.RED])
    <photutils.background.background_2d.Background2D>...

    >>> {color.name:int(rgb_back[color].mean()) for color in RGB}
    {'RED': 145, 'GREEN': 127, 'BLUE': 145}

    Args:
        data (np.array): The data to use if no `fits_fn` is provided.
        box_size (tuple, optional): The box size over which to compute the
            2D-Background, default (79, 84).
        filter_size (tuple, optional): The filter size for determining the median,
            default (11, 12).
        estimator (str, optional): The estimator object to use, default 'mmm'.
        interpolator (str, optional): The interpolater object to user, default 'zoom'.
        sigma (int, optional): The sigma on which to filter values, default 5.
        iters (int, optional): The number of iterations to sigma filter, default 10.
        exclude_percentile (int, optional): The percentage of the data (per channel)
            that can be masked, default 100 (i.e. all).
        return_separate (bool, optional): If the function should return a separate array
            for color channel, default False.
        *args: Description
        **kwargs: Description

    Returns:
        `numpy.array`|list(Background2D): Either a single numpy array representing the entire
          background, or a list of masked numpy arrays in RGB order. The background
          for each channel has full interploation across all pixels, but the mask covers
          them.
    """
    logger.debug("RGB background subtraction")
    logger.debug(f"{estimator} {interpolator} {box_size} {filter_size} {sigma} {iters}")

    estimators = {
        'sexb': SExtractorBackground,
        'median': MedianBackground,
        'mean': MeanBackground,
        'mmm': MMMBackground
    }
    interpolators = {
        'zoom': BkgZoomInterpolator,
    }

    bkg_estimator = estimators[estimator]()
    interp = interpolators[interpolator]()

    # Get the data per color channel.
    logger.debug(f'Getting RGB background data ({data.shape})')
    rgb_data = get_rgb_data(data)

    backgrounds = list()
    for color, color_data in zip(RGB, rgb_data):
        logger.debug(f'Calculating background for {color.name.lower()} pixels')

        bkg = Background2D(color_data,
                           box_size,
                           filter_size=filter_size,
                           sigma_clip=SigmaClip(sigma=sigma, maxiters=iters),
                           bkg_estimator=bkg_estimator,
                           exclude_percentile=exclude_percentile,
                           mask=color_data.mask,
                           interpolator=interp)

        logger.debug(f"{color.name.lower()}: {bkg.background_median:.02f} "
                     f"RMS: {bkg.background_rms_median:.02f}")

        if return_separate:
            backgrounds.append(bkg)
        else:
            # Create a masked array for the background
            backgrounds.append(np.ma.array(data=bkg.background, mask=color_data.mask))

    if return_separate:
        return backgrounds

    # Create one array for the backgrounds, where any holes are filled with zeros.
    full_background = np.ma.array(backgrounds).sum(0).filled(0)

    return full_background


def save_rgb_bg_fits(rgb_bg_data, output_filename, header=None, fpack=True, overwrite=True):
    """Save a FITS file containing a combined background as well as separate channels.

    Args:
        rgb_bg_data (list[photutils.background.Background2D]): The RGB background data as
            returned by calling `panoptes.utils.images.bayer.get_rgb_background`
            with `return_separate=True`.
        output_filename (str): The output name for the FITS file.
        header (astropy.io.fits.Header): FITS header to be saved with the file.
        fpack (bool): If the FITS file should be compressed, default True.
        overwrite (bool): If FITS file should be overwritten, default True.
    """

    # Get combined data for Primary HDU
    combined_bg = np.array([np.ma.array(data=d.background, mask=d.coverage_mask).filled(0)
                            for d in rgb_bg_data]).sum(0)

    header = header or fits.Header()

    # Save as ing16.
    header['BITPIX'] = 16

    # Combined background is primary hdu.
    primary = fits.PrimaryHDU(combined_bg, header=header)
    primary.scale('int16')
    hdu_list = [primary]

    for color, bg in zip(RGB, rgb_bg_data):
        h0 = fits.Header()
        h0['COLOR'] = f'{color.name.lower()}'

        h0['IMGTYPE'] = 'background'
        img0 = fits.ImageHDU(bg.background, header=h0)
        img0.scale('int16')
        hdu_list.append(img0)

        h0['IMGTYPE'] = 'background_rms'
        img1 = fits.ImageHDU(bg.background_rms, header=h0)
        img1.scale('int16')
        hdu_list.append(img1)

    hdul = fits.HDUList(hdu_list)
    hdul.writeto(output_filename, overwrite=overwrite)

    if fpack:
        output_filename = fits_utils.fpack(output_filename)

    return output_filename
