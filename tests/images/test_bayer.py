import pytest
import numpy as np

from panoptes.utils.images import bayer
from panoptes.utils.images import fits as fits_utils


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


def test_get_stamp_slice():
    superpixel = np.array(['G2', 'B', 'R', 'G1']).reshape(2, 2)
    d0 = np.tile(superpixel, (5, 5))
    d1 = np.arange(100).reshape(10, 10)

    positions = [
        (6, 4),
        (6, 5),
        (7, 4),
        (7, 5),
    ]

    centers = {d0[y, x]: d1[y, x] for x, y in positions}
    assert centers == {'G2': 46, 'R': 56, 'B': 47, 'G1': 57}

    slices = [bayer.get_stamp_slice(x, y, stamp_size=(6, 6)) for x, y in positions]
    # They should all be the same
    for s0 in slices:
        assert s0 == (slice(2, 8, None), slice(4, 10, None))


def test_get_stamp_slice_fail():
    # Nothing small
    with pytest.raises(RuntimeError):
        bayer.get_stamp_slice(4, 4, stamp_size=(4, 4))

    # Nothing odd
    with pytest.raises(RuntimeError):
        bayer.get_stamp_slice(512, 514, stamp_size=(15, 15))

    # Unless we use `ignore_superpixel`
    s0 = bayer.get_stamp_slice(512, 514, stamp_size=(15, 15), ignore_superpixel=True)
    assert s0 == (slice(508, 523, None), slice(506, 521, None))

    # Nothing where (i-2) % 4 != 0
    with pytest.raises(RuntimeError):
        bayer.get_stamp_slice(512, 514, stamp_size=(12, 12))
    with pytest.raises(RuntimeError):
        bayer.get_stamp_slice(512, 514, stamp_size=(100, 100))


def test_save_rgb_bg_fits(solved_fits_file, tmpdir):
    d0, h0 = fits_utils.getdata(solved_fits_file, header=True)

    temp_fn = tmpdir / 'temp.fits'

    h0['test'] = True

    rgb_data = bayer.get_rgb_background(d0, return_separate=True)
    bayer.save_rgb_bg_fits(rgb_data, output_filename=str(temp_fn), header=h0, fpack=False)
    assert fits_utils.getval(str(temp_fn), 'test') is True

    with pytest.raises(OSError):
        bayer.save_rgb_bg_fits(rgb_data, output_filename=str(temp_fn), header=h0, fpack=False,
                               overwrite=False)

    temp_fn = bayer.save_rgb_bg_fits(rgb_data, output_filename=str(temp_fn), fpack=True,
                                     overwrite=True)

    # Didn't use our header.
    with pytest.raises(KeyError):
        fits_utils.getval(str(temp_fn), 'test')
