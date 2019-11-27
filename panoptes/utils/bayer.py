import os

import numpy as np

from decimal import Decimal
from decimal import ROUND_HALF_UP


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
    
    See `get_rgb_data` for description of data.

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
        raise Exception('Only 2D and 3D data allowed')

    if separate_green:
        return np.array([r_mask, g1_mask, g2_mask, b_mask])
    else:
        return np.array([r_mask, g1_mask, b_mask])


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


        This can be described by:

                 | row (y) |  col (x)
             --------------| ------
              R  |  odd i, |  even j
              G1 |  odd i, |   odd j
              G2 | even i, |  even j
              B  | even i, |   odd j

            bayer[1::2, 0::2] = 1 # Red
            bayer[1::2, 1::2] = 1 # Green
            bayer[0::2, 0::2] = 1 # Green
            bayer[0::2, 1::2] = 1 # Blue

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
