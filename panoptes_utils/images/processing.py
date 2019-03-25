import os

import numpy as np
import logging

from decimal import Decimal
from decimal import ROUND_HALF_UP

from astropy.wcs import WCS

from panoptes_utils.images import fits as fits_utils


def get_rgb_cube(cube):
    """ Given a cube of data, return the same cube split by RGB """

    stamp_side = int(np.sqrt(cube[0].shape))
    # Get the masks
    first_frame = cube[0].reshape(stamp_side, stamp_side)
    rgb_masks = np.array([m for m in get_rgb_masks(first_frame).values()])

    def mask_frame(f):
        r = np.ma.array(f, mask=~rgb_masks[0])
        g = np.ma.array(f, mask=~rgb_masks[1])
        b = np.ma.array(f, mask=~rgb_masks[2])
        return np.ma.array([r, g, b])

    rgb_cube = np.apply_along_axis(mask_frame, 1, cube)

    # Rearrange so the color is first
    r = rgb_cube[:, 0, :]
    g = rgb_cube[:, 1, :]
    b = rgb_cube[:, 2, :]

    return np.ma.array([r, g, b])


def get_rgb_data(data, **kwargs):
    rgb_masks = get_rgb_masks(data, **kwargs)

    assert rgb_masks is not None

    color_data = list()

    r_data = np.ma.array(data, mask=~rgb_masks['r'])
    color_data.append(r_data)

    g_data = np.ma.array(data, mask=~rgb_masks['g'])
    color_data.append(g_data)

    try:
        c_data = np.ma.array(data, mask=~rgb_masks['c'])
        color_data.append(c_data)
    except KeyError:
        pass

    b_data = np.ma.array(data, mask=~rgb_masks['b'])
    color_data.append(b_data)

    return np.ma.array(color_data)


def get_rgb_masks(data, separate_green=False, mask_path=None, force_new=False, verbose=False):
    """Get the RGGB Bayer pattern for the given data.

    Args:
        data (`numpy.array`): An array of data representing an image.
        separate_green (bool, optional): If the two green channels should be separated,
            default False.
        mask_path (str, optional): Path to file to save/lookup mask.
        force_new (bool, optional): If a new file should be generated, default False.
        verbose (bool, optional): Verbose, default False.

    Returns:
        TYPE: Description
    """
    if mask_path is None:
        mask_path = os.path.join(os.environ['PANDIR'],
                                 f'rgb_masks_{data.shape[0]}_{data.shape[1]}.npz')

    logging.debug('Mask path: {}'.format(mask_path))

    if force_new:
        logging.info("Forcing a new mask file")
        try:
            os.remove(mask_path)
        except FileNotFoundError:
            pass

    # Try to load existing file and if not generate new
    try:
        loaded_masks = np.load(mask_path)
        logging.debug("Loaded masks")
        mask_shape = loaded_masks[loaded_masks.files[0]].shape
        if mask_shape != data.shape:
            logging.debug("Removing mask with wrong size")
            os.remove(mask_path)
            raise FileNotFoundError
        else:
            logging.debug("Using saved masks")
            _rgb_masks = {color: loaded_masks[color] for color in loaded_masks.files}
    except Exception:
        logging.debug("Making RGB masks")

        if data.ndim > 2:
            data = data[0]

        w, h = data.shape

        # See the docstring for `pixel_color` for full description of indexing values.

        #        |   row   |  col
        #    --------------| ------
        #     R  |  odd i, | even j
        #     G1 |  odd i, |  odd j
        #     G2 | even i, | even j
        #     B  | even i, |  odd j

        def is_red(pos):
            return pos[0] % 2 == 1 and pos[1] % 2 == 0

        def is_blue(pos):
            return pos[0] % 2 == 0 and pos[1] % 2 == 1

        def is_g1(pos):
            return pos[0] % 2 == 1 and pos[1] % 2 == 1

        def is_g2(pos):
            return pos[0] % 2 == 0 and pos[1] % 2 == 0

        red_mask = (np.array(
            [
                is_red(index)
                for index, _
                in np.ndenumerate(data)
            ]
        ).reshape(w, h))

        blue_mask = (np.array(
            [
                is_blue(index)
                for index, _
                in np.ndenumerate(data)
            ]
        ).reshape(w, h))

        if separate_green:
            logging.debug("Making separate green masks")
            green1_mask = (np.array(
                [
                    is_g1(index)
                    for index, _
                    in np.ndenumerate(data)
                ]
            ).reshape(w, h))

            green2_mask = (np.array(
                [
                    is_g2(index)
                    for index, _
                    in np.ndenumerate(data)
                ]
            ).reshape(w, h))

            _rgb_masks = {
                'r': red_mask,
                'g': green1_mask,
                'c': green2_mask,
                'b': blue_mask,
            }
        else:
            green_mask = (np.array(
                [
                    is_g1(index) or is_g2(index)
                    for index, _ in
                    np.ndenumerate(data)
                ]
            ).reshape(w, h))

            _rgb_masks = {
                'r': red_mask,
                'g': green_mask,
                'b': blue_mask,
            }

        logging.debug("Saving masks files")
        np.savez_compressed(mask_path, **_rgb_masks)

    return _rgb_masks


def spiral_matrix(A):
    """Simple function to spiral a matrix.

    Args:
        A (`numpy.array`): Array to spiral.

    Returns:
        `numpy.array`: Spiralled array.
    """
    A = np.array(A)
    out = []
    while(A.size):
        out.append(A[:, 0][::-1])  # take first row and reverse it
        A = A[:, 1:].T[::-1]       # cut off first row and rotate counterclockwise
    return np.concatenate(out)


def get_pixel_index(x):
    """Find corresponding index position of `x` pixel position.

    Note:
        Due to the standard rounding policy of python that will round half integers
        to their nearest even whole integer, we instead use a `Decimal` with correct
        round up policy.

    Args:
        x (float): x coordinate position.

    Returns:
        int: Index position for zero-based index
    """
    return int(Decimal(x - 1).to_integral_value(ROUND_HALF_UP))


def pixel_color(x, y):
    """ Given an x,y position, return the corresponding color.

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

        Bayer Pattern:

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


        This can be described by:

                 | row (y) |  col (x)
             --------------| ------
              R  |  odd i, |  even j
              G1 |  odd i, |   odd j
              G2 | even i, |  even j
              B  | even i, |   odd j

            bayer[1::2, 0::2, 0] = 1 # Red
            bayer[1::2, 1::2, 1] = 1 # Green
            bayer[0::2, 0::2, 1] = 1 # Green
            bayer[0::2, 1::2, 2] = 1 # Blue

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


def get_stamp_slice(x, y, stamp_size=(14, 14), verbose=False, ignore_superpixel=False):
    """Get the slice around a given position with fixed Bayer pattern.

    Given an x,y pixel position, get the slice object for a stamp of a given size
    but make sure the first position corresponds to a red-pixel. This means that
    x,y will not necessarily be at the center of the resulting stamp.

    Args:
        x (float): X pixel position.
        y (float): Y pixel position.
        stamp_size (tuple, optional): The size of the cutout, default (14, 14).
        verbose (bool, optional): Verbose, default False.

    Returns:
        `slice`: A slice object for the data.
    """
    # Make sure requested size can have superpixels on each side.
    if not ignore_superpixel:
        for side_length in stamp_size:
            side_length -= 2  # Subtract center superpixel
            if int(side_length / 2) % 2 != 0:
                print("Invalid slice size: ", side_length + 2,
                      " Slice must have even number of pixels on each side of",
                      " the center superpixel.",
                      "i.e. 6, 10, 14, 18...")
                return

    # Pixels have nasty 0.5 rounding issues
    x = Decimal(float(x)).to_integral()
    y = Decimal(float(y)).to_integral()
    color = pixel_color(x, y)
    if verbose:
        print(x, y, color)

    x_half = int(stamp_size[0] / 2)
    y_half = int(stamp_size[1] / 2)

    x_min = int(x - x_half)
    x_max = int(x + x_half)

    y_min = int(y - y_half)
    y_max = int(y + y_half)

    # Alter the bounds depending on identified center pixel
    if color == 'B':
        x_min -= 1
        x_max -= 1
        y_min -= 0
        y_max -= 0
    elif color == 'G1':
        x_min -= 1
        x_max -= 1
        y_min -= 1
        y_max -= 1
    elif color == 'G2':
        x_min -= 0
        x_max -= 0
        y_min -= 0
        y_max -= 0
    elif color == 'R':
        x_min -= 0
        x_max -= 0
        y_min -= 1
        y_max -= 1

    # if stamp_size is odd add extra
    if (stamp_size[0] % 2 == 1):
        x_max += 1
        y_max += 1

    if verbose:
        print(x_min, x_max, y_min, y_max)
        print()

    return (slice(y_min, y_max), slice(x_min, x_max))


def get_pixel_drift(coords, files):
    """Get the pixel drift for a given set of coordinates.

    Args:
        coords (`astropy.coordinates.SkyCoord`): Coordinates of source.
        files (list): A list of FITS files with valid WCS.

    Returns:
        `numpy.array, numpy.array`: A 2xN array of pixel deltas where
            N=len(files)
    """
    # Get target positions for each frame
    target_pos = list()
    for fn in files:
        h0 = fits_utils.getheader(fn)
        pos = WCS(h0).all_world2pix(coords.ra, coords.dec, 1)
        target_pos.append(pos)

    target_pos = np.array(target_pos)

    # Subtract out the mean to get just the pixel deltas
    x_pos = target_pos[:, 0]
    y_pos = target_pos[:, 1]

    x_pos -= x_pos.mean()
    y_pos -= y_pos.mean()

    return x_pos, y_pos
