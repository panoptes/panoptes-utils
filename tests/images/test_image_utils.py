import os
import tempfile

import numpy as np
import pytest
from astropy import units as u
from astropy.nddata import Cutout2D

from panoptes.utils import error
from panoptes.utils.images import make_pretty_image
from panoptes.utils.images.misc import crop_data, mask_saturated


def test_mask_saturated():
    ones = np.ones((10, 10))
    ones[0, 0] = 256
    # Bit-depth.
    assert mask_saturated(ones, bit_depth=8).sum() == 99.0
    # Bit-depth with unit.
    assert mask_saturated(ones, bit_depth=8 * u.bit).sum() == 99.0
    # Array has int dtype so bit_depth is inferred.
    assert mask_saturated(ones.astype('int8')).sum() == 99.0


def test_mask_saturated_bad():
    ones = np.ones((10, 10))
    ones[0, 0] = 256
    with pytest.raises(error.IllegalValue):
        mask_saturated(ones, bit_depth=8 * u.meter)

    with pytest.raises(error.IllegalValue):
        mask_saturated(ones)


def test_crop_data():
    ones = np.ones((201, 201))
    assert ones.sum() == 40401.

    cropped01 = crop_data(ones)  # False to exercise coverage.
    assert cropped01.sum() == 40000.

    cropped02 = crop_data(ones, box_width=10)
    assert cropped02.sum() == 100.

    cropped03 = crop_data(ones, box_width=6, center=(50, 50))
    assert cropped03.sum() == 36.

    # Test the Cutout2D object
    cropped04 = crop_data(ones,
                          box_width=20,
                          center=(50, 50),
                          data_only=False)
    assert isinstance(cropped04, Cutout2D)
    assert cropped04.position_original == (50, 50)

    # Box is 20 pixels wide so center is at 10,10
    assert cropped04.position_cutout == (10, 10)


def test_make_pretty_image(solved_fits_file, tiny_fits_file, save_environ):
    # Make a dir and put test image files in it.
    with tempfile.TemporaryDirectory() as tmpdir:
        # TODO Add a small CR2 file to our sample image files.

        # Can't operate on a non-existent files.
        with pytest.warns(UserWarning, match="File doesn't exist"):
            assert not make_pretty_image('Foobar')

        # Can handle the fits file, and creating the images dir for linking
        # the latest image.
        imgdir = os.path.join(tmpdir, 'images')
        assert not os.path.isdir(imgdir)
        os.makedirs(imgdir, exist_ok=True)

        link_path = os.path.join(tmpdir, 'latest.jpg')
        pretty = make_pretty_image(solved_fits_file, link_path=link_path)
        assert pretty.exists()
        assert pretty.is_file()
        assert os.path.isdir(imgdir)
        assert link_path == pretty.as_posix()
        os.remove(link_path)
        os.rmdir(imgdir)

        # Try again, but without link_path.
        pretty = make_pretty_image(tiny_fits_file, title='some text')
        assert pretty.exists()
        assert pretty.is_file()
        assert not os.path.isdir(imgdir)


def test_make_pretty_image_cr2_fail():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, 'bad.cr2')
        with open(tmpfile, 'w') as f:
            f.write('not an image file')
        with pytest.raises(error.InvalidSystemCommand):
            make_pretty_image(tmpfile, title='some text')
        with pytest.raises(error.AlreadyExists):
            make_pretty_image(tmpfile)

        no_image = make_pretty_image('not-a-file')
        assert no_image is None


def test_make_pretty_image_cr2(cr2_file, tmpdir):
    link_path = str(tmpdir.mkdir('images').join('latest.jpg'))
    print(f'link_path: {link_path} cr2_file: {cr2_file}')
    pretty_path = make_pretty_image(cr2_file,
                                    title='CR2 Test',
                                    link_path=link_path,
                                    remove_cr2=True)

    assert pretty_path.exists()
    assert pretty_path.as_posix() == link_path
    assert os.path.exists(cr2_file) is False
