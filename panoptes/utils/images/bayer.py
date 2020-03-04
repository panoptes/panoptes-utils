
import numpy as np


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
