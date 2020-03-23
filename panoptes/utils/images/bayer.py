import numpy as np

from astropy.stats import SigmaClip

from photutils import Background2D
from photutils import MeanBackground
from photutils import MMMBackground
from photutils import MedianBackground
from photutils import SExtractorBackground
from photutils import BkgZoomInterpolator

from ..logger import logger
from . import fits as fits_utils


def get_rgb_data(data, separate_green=False):
    """Get the data split into separate channels for RGB.

    `data` can be a 2D (`W x H`) or 3D (`N x W x H`) array where `W`=width
    and `H`=height of the data, with `N`=number of frames.

    The return array will be a `3 x W x H` or `3 x N x W x H` array.

    The Bayer array defines a superpixel as a collection of 4 pixels
    set in a square grid:

                     R G
                     G B

    `ds9` and other image viewers define the coordinate axis from the
    lower left corner of the image, which is how a traditional x-y plane
    is defined and how most images would expect to look when viewed. This
    means that the `(0, 0)` coordinate position will be in the lower left
    corner of the image.

    When the data is loaded into a `numpy` array the data is flipped on the
    vertical axis in order to maintain the same indexing/slicing features.
    This means the the `(0, 0)` coordinate position is in the upper-left
    corner of the array when output. When plotting this array one can use
    the `origin='lower'` option to view the array as would be expected in
    a normal image although this does not change the actual index.

    Note:

        Image dimensions:

         ----------------------------
         x | width  | i | columns |  5208
         y | height | j | rows    |  3476

        Bayer Pattern (as seen in ds9):

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


        Note: This therefore assumes the data is in the following format:

                 | row (y) |  col (x)
             --------------| ------
              R  |  odd i, |  even j
              G1 |  odd i, |   odd j
              G2 | even i, |  even j
              B  | even i, |   odd j

        Or, in other words, the bottom-left (i.e. `(0,0)`) super-pixel is an RGGB pattern.

        And a mask can therefore be generated as:

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

    > Note: See `get_rgb_data` for a description of the RGGB pattern.

    Args:
        data (`numpy.array`): An array of data representing an image.
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
    """ Given an x,y position, return the corresponding color.

    > Note: See `get_rgb_data` for a description of the RGGB pattern.

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


def get_rgb_background(fits_fn,
                       box_size=(84, 84),
                       filter_size=(3, 3),
                       camera_bias=0,
                       estimator='mean',
                       interpolator='zoom',
                       sigma=5,
                       iters=5,
                       exclude_percentile=100
                       ):
    """Get the background for each color channel.

    Most of the options are described in the `photutils.Background2D` page:
    https://photutils.readthedocs.io/en/stable/background.html#d-background-and-noise-estimation

    >>> from panoptes.utils.images import fits as fits_utils
    >>> fits_fn = getfixture('solved_fits_file')

    >>> data = fits_utils.getdata(fits_fn)
    >>> data.mean()
    2236.816...

    >>> rgb_back = get_rgb_background(fits_fn)
    >>> rgb_back.mean()
    2202.392...


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

    Returns:
        list: A list containing a `photutils.Background2D` for each color channel, in RGB order.
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
        backgrounds.append(np.ma.array(data=bkg.background, mask=color_data.mask))
        logger.debug(
            f"{color} Value: {bkg.background_median:.02f} RMS: {bkg.background_rms_median:.02f}")

    # Create one array for the backgrounds, where any holes are filled with zeros.
    full_background = np.ma.array(backgrounds).sum(0).filled(0)

    return full_background
