import os
import numpy as np
import pytest
import shutil
import tempfile

from astropy.nddata import Cutout2D

from panoptes.utils import images as img_utils
from panoptes.utils import error


def test_crop_data():
    ones = np.ones((201, 201))
    assert ones.sum() == 40401.0

    cropped01 = img_utils.crop_data(ones)  # False to exercise coverage.
    assert cropped01.sum() == 40000.0

    cropped02 = img_utils.crop_data(ones, box_width=10)
    assert cropped02.sum() == 100.0

    cropped03 = img_utils.crop_data(ones, box_width=6, center=(50, 50))
    assert cropped03.sum() == 36.0

    # Test the Cutout2D object
    cropped04 = img_utils.crop_data(ones, box_width=20, center=(50, 50), data_only=False)
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
            assert not img_utils.make_pretty_image("Foobar")

        # Can handle the fits file, and creating the images dir for linking
        # the latest image.
        imgdir = os.path.join(tmpdir, "images")
        assert not os.path.isdir(imgdir)
        os.makedirs(imgdir, exist_ok=True)
        os.environ["PANDIR"] = tmpdir

        link_path = os.path.expandvars("$PANDIR/latest.jpg")
        pretty = img_utils.make_pretty_image(solved_fits_file, link_path=link_path)
        assert pretty
        assert os.path.isfile(pretty)
        assert os.path.isdir(imgdir)
        assert link_path == pretty
        os.remove(link_path)
        os.rmdir(imgdir)

        # Try again, but without link_path.
        pretty = img_utils.make_pretty_image(tiny_fits_file, title="some text")
        assert pretty
        assert os.path.isfile(pretty)
        assert not os.path.isdir(imgdir)


@pytest.mark.skipif(
    "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
    reason="Skipping this test on Travis CI.",
)
def test_make_pretty_image_cr2_fail():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, "bad.cr2")
        with open(tmpfile, "w") as f:
            f.write("not an image file")
        with pytest.raises(error.InvalidCommand):
            img_utils.make_pretty_image(tmpfile, title="some text")
        with pytest.raises(error.InvalidCommand):
            img_utils.make_pretty_image(tmpfile)


def test_make_pretty_image_cr2(cr2_file):
    link_path = os.path.expandvars("$PANDIR/images/latest.jpg")
    pretty_path = img_utils.make_pretty_image(
        cr2_file, title="CR2 Test", image_type="cr2", link_path=link_path
    )

    assert os.path.exists(pretty_path)
    assert pretty_path == link_path


def test_overlay_grid_image(tiny_fits_file, tiny_jpeg_file):  # TODO: Find out where jpeg comes from

    overlay_path = img_utils._overlay_grid_image(
        tiny_fits_file, fname_jpg="$PANDIR/images/latest.jpg", output_filename="test-output.png"
    )

    assert os.path.exists(overlay_path)


def test_overlay_grid_image_fail():
    with tempfile.TemporaryDirectory as tmpdir:
        tmpfile_fits = os.path.join(tmpdir, "bad.fits")
        tmpfile_jpeg = os.path.join(tmpdir, "bad.jpg")
        with open(tmpfile_fits, "w") as f1, open(tmpfile_jpeg, "w") as f2:
            f1.write("Not an image file.")
            f2.write("Not an image file.")
        with pytest.raises(error.InvalidCommand):
            img_utils.overlay_grid_image(tmpfile_fits, tmpfile_jpeg)
