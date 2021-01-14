from decimal import Decimal

import numpy as np
from astropy.stats import SigmaClip
from loguru import logger
from panoptes.utils.images import fits as fits_utils
from photutils import Background2D
from photutils import BkgZoomInterpolator
from photutils import MeanBackground
from photutils import MedianBackground
from photutils import MMMBackground
from photutils import SExtractorBackground


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


def get_stamp_slice(x, y, stamp_size=(14, 14), ignore_superpixel=False):
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
        >>> stamp0[pixel_index]
        'G1'
        >>> stamp1[pixel_index]
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

    This puts the requested pixel in the center but does not offer any guarantees about the RGGB pattern.

    Args:
        x (float): X pixel position.
        y (float): Y pixel position.
        stamp_size (tuple, optional): The size of the cutout, default (14, 14).
        ignore_superpixel (bool): If superpixels should be ignored, default False.
    Returns:
        `slice`: A slice object for the data.
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

    return (slice(y_min, y_max), slice(x_min, x_max))


def get_rgb_background(fits_fn,
                       box_size=(84, 84),
                       filter_size=(3, 3),
                       camera_bias=0,
                       estimator='mean',
                       interpolator='zoom',
                       sigma=5,
                       iters=5,
                       exclude_percentile=100,
                       return_separate=False,
                       *args,
                       **kwargs
                       ):
    """Get the background for each color channel.

    Most of the options are described in the `photutils.Background2D` page:
    https://photutils.readthedocs.io/en/stable/background.html#d-background-and-noise-estimation

    >>> from panoptes.utils.images import fits as fits_utils
    >>> fits_fn = getfixture('solved_fits_file')

    >>> data = fits_utils.getdata(fits_fn)
    >>> data.mean()
    2236...

    >>> rgb_back = get_rgb_background(fits_fn)
    >>> rgb_back.mean()
    2202...

    >>> rgb_backs = get_rgb_background(fits_fn, return_separate=True)
    >>> rgb_backs[0]
    <photutils.background.background_2d.Background2D...>
    >>> {color:data.background_rms_median for color, data in zip('rgb', rgb_backs)}
    {'r': 20..., 'g': 32..., 'b': 23...}


    Args:
        fits_fn (str): The filename of the FITS image.
        box_size (tuple, optional): The box size over which to compute the
            2D-Background, default (84, 84).
        filter_size (tuple, optional): The filter size for determining the median,
            default (3, 3).
        camera_bias (int, optional): The built-in camera bias, default 0. A zero camera
            bias means the bias will be considered as part of the background.
        estimator (str, optional): The estimator object to use, default 'median'.
        interpolator (str, optional): The interpolater object to user, default 'zoom'.
        sigma (int, optional): The sigma on which to filter values, default 5.
        iters (int, optional): The number of iterations to sigma filter, default 5.
        exclude_percentile (int, optional): The percentage of the data (per channel)
            that can be masked, default 100 (i.e. all).
        return_separate (bool, optional): If the function should return a separate array
            for color channel, default False.
        *args: Description
        **kwargs: Description

    Returns:
        `numpy.array`|list: Either a single numpy array representing the entire
          background, or a list of masked numpy arrays in RGB order. The background
          for each channel has full interploation across all pixels, but the mask covers
          them.
    """
    logger.info(f"Getting background for {fits_fn}")
    logger.debug(
        f"{estimator} {interpolator} {box_size} {filter_size} {camera_bias} σ={sigma} n={iters}")

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

    data = fits_utils.getdata(fits_fn) - camera_bias

    # Get the data per color channel.
    rgb_data = get_rgb_data(data)

    backgrounds = list()
    for color, color_data in zip(['R', 'G', 'B'], rgb_data):
        logger.debug(f'Performing background {color} for {fits_fn}')

        bkg = Background2D(color_data,
                           box_size,
                           filter_size=filter_size,
                           sigma_clip=SigmaClip(sigma=sigma, maxiters=iters),
                           bkg_estimator=bkg_estimator,
                           exclude_percentile=exclude_percentile,
                           mask=color_data.mask,
                           interpolator=interp)

        # Create a masked array for the background
        if return_separate:
            backgrounds.append(bkg)
        else:
            backgrounds.append(np.ma.array(data=bkg.background, mask=color_data.mask))
        logger.debug(
            f"{color} Value: {bkg.background_median:.02f} RMS: {bkg.background_rms_median:.02f}")

    if return_separate:
        return backgrounds

    # Create one array for the backgrounds, where any holes are filled with zeros.
    full_background = np.ma.array(backgrounds).sum(0).filled(0)

    return full_background
