import pytest
import numpy as np

from panoptes.utils.images import bayer


def test_get_rgb_2d_data():
    data_2d = np.ones((10, 10))
    rgb_data = bayer.get_rgb_data(data_2d)

    assert isinstance(rgb_data, np.ma.core.MaskedArray)
    assert len(rgb_data) == 3

    # Red and Blue will add to 25 for a 10x10 data stamp
    assert rgb_data[0].sum() == 25
    assert rgb_data[-1].sum() == 25

    assert rgb_data[1].sum() == 50

    rgb_data = bayer.get_rgb_data(data_2d, separate_green=True)

    assert isinstance(rgb_data, np.ma.core.MaskedArray)
    assert len(rgb_data) == 4

    # Red and Blue will add to 25 for a 10x10 data stamp
    assert rgb_data[0].sum() == 25
    assert rgb_data[1].sum() == 25
    assert rgb_data[2].sum() == 25
    assert rgb_data[3].sum() == 25


def test_get_rgb_3d_data():
    data_2d = np.ones((10, 10, 10))
    rgb_data = bayer.get_rgb_data(data_2d)

    assert isinstance(rgb_data, np.ma.core.MaskedArray)
    assert len(rgb_data) == 3

    # Red and Blue will add to 25 for a 10x10 data stamp
    assert rgb_data[0].sum() == 250
    assert rgb_data[-1].sum() == 250

    assert rgb_data[1].sum() == 500

    rgb_data = bayer.get_rgb_data(data_2d, separate_green=True)

    assert isinstance(rgb_data, np.ma.core.MaskedArray)
    assert len(rgb_data) == 4

    # Red and Blue will add to 25 for a 10x10 data stamp
    assert rgb_data[0].sum() == 250
    assert rgb_data[1].sum() == 250
    assert rgb_data[2].sum() == 250
    assert rgb_data[3].sum() == 250


def test_get_rgb_4d_data():
    data = np.ones((10, 10, 10, 10))
    with pytest.raises(TypeError):
        bayer.get_rgb_data(data)


def test_get_pixel_color():
    """
        From the docstring:

                 | row (y) |  col (x)
             --------------| ------
              R  |  odd i, |  even j
              G1 |  odd i, |   odd j
              G2 | even i, |  even j
              B  | even i, |   odd j

    """

    assert bayer.get_pixel_color(0, 1) == 'R'
    assert bayer.get_pixel_color(1, 1) == 'G1'
    assert bayer.get_pixel_color(2, 2) == 'G2'
    assert bayer.get_pixel_color(1, 2) == 'B'

    # Test with some fractional pixels
    assert bayer.get_pixel_color(0, 1.1) == 'R'
    assert bayer.get_pixel_color(1.9, 1) == 'G1'
    assert bayer.get_pixel_color(2, 2.5) == 'G2'
    assert bayer.get_pixel_color(1.5, 2) == 'B'
