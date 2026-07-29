import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from panoptes.utils import error
from panoptes.utils.images import cr2 as cr2_utils


def test_cr2_to_pgm_pathlib(cr2_file):
    """Test cr2_to_pgm with pathlib.Path input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cr2_path = Path(cr2_file)
        pgm_path = Path(tmpdir) / "test_output.pgm"

        # Test with Path objects for both input and output
        result = cr2_utils.cr2_to_pgm(cr2_path, pgm_path)

        assert pgm_path.exists()
        assert result == str(pgm_path)


def test_cr2_to_pgm_filehandle(cr2_file):
    """Test cr2_to_pgm with open filehandle input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pgm_path = os.path.join(tmpdir, "test_output_fh.pgm")

        # Test with filehandle input
        with open(cr2_file, "rb") as f:
            result = cr2_utils.cr2_to_pgm(f, pgm_path)

        assert os.path.exists(pgm_path)
        assert result == pgm_path


def test_read_exif_pathlib(cr2_file):
    """Test read_exif with pathlib.Path input."""
    cr2_path = Path(cr2_file)
    exif_data = cr2_utils.read_exif(cr2_path)

    assert isinstance(exif_data, dict)
    # Basic check that we got some EXIF data
    assert len(exif_data) > 0


def test_read_exif_filehandle(cr2_file):
    """Test read_exif with open filehandle input."""
    with open(cr2_file, "rb") as f:
        exif_data = cr2_utils.read_exif(f)

    assert isinstance(exif_data, dict)
    # Basic check that we got some EXIF data
    assert len(exif_data) > 0


def test_read_pgm_pathlib(cr2_file):
    """Test read_pgm with pathlib.Path input after converting CR2 to PGM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pgm_path = os.path.join(tmpdir, "test.pgm")

        # First convert CR2 to PGM
        cr2_utils.cr2_to_pgm(cr2_file, pgm_path)

        # Then test reading with Path object
        pgm_path_obj = Path(pgm_path)
        data = cr2_utils.read_pgm(pgm_path_obj)

        assert data is not None
        # Basic validation that we got image data
        assert hasattr(data, "shape")  # Should be a numpy array


def test_read_pgm_filehandle(cr2_file):
    """Test read_pgm with open filehandle input after converting CR2 to PGM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pgm_path = os.path.join(tmpdir, "test.pgm")

        # First convert CR2 to PGM
        cr2_utils.cr2_to_pgm(cr2_file, pgm_path)

        # Then test reading with filehandle
        with open(pgm_path, "rb") as f:
            data = cr2_utils.read_pgm(f)

        assert data is not None
        # Basic validation that we got image data
        assert hasattr(data, "shape")  # Should be a numpy array


def test_cr2_to_fits_pathlib(cr2_file):
    """Test cr2_to_fits with pathlib.Path input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cr2_path = Path(cr2_file)
        fits_path = Path(tmpdir) / "test_output.fits"

        # Test with Path objects for both input and output
        result = cr2_utils.cr2_to_fits(cr2_path, fits_path)

        assert fits_path.exists()
        assert result == str(fits_path)


def test_cr2_to_fits_filehandle(cr2_file):
    """Test cr2_to_fits with open filehandle input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fits_path = os.path.join(tmpdir, "test_output_fh.fits")

        # Test with filehandle input
        with open(cr2_file, "rb") as f:
            result = cr2_utils.cr2_to_fits(f, fits_path)

        assert os.path.exists(fits_path)
        assert result == fits_path


def test_cr2_to_jpg_pathlib(cr2_file):
    """Test cr2_to_jpg with pathlib.Path input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cr2_path = Path(cr2_file)
        jpg_path = Path(tmpdir) / "test_output.jpg"

        # Test with Path objects for both input and output
        result = cr2_utils.cr2_to_jpg(cr2_path, jpg_path)

        assert jpg_path.exists()
        assert result == str(jpg_path)


def test_cr2_to_jpg_filehandle(cr2_file):
    """Test cr2_to_jpg with open filehandle input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jpg_path = os.path.join(tmpdir, "test_output_fh.jpg")

        # Test with filehandle input
        with open(cr2_file, "rb") as f:
            result = cr2_utils.cr2_to_jpg(f, jpg_path)

        assert os.path.exists(jpg_path)
        assert result == jpg_path


def _make_fake_run(magick_calls=None):
    """Return a fake subprocess.run that stubs exiftool and optionally captures magick calls."""

    def fake_run(cmd, **kwargs):
        # Detect the exiftool preview-extraction call by its distinctive flags.
        if "-PreviewImage" in cmd:
            stdout = kwargs.get("stdout")
            if stdout is not None:
                stdout.write(b"FAKEJPG")
            result = MagicMock()
            result.returncode = 0
            return result
        # Everything else is a magick annotation call.
        if magick_calls is not None:
            magick_calls.append(cmd)
        result = MagicMock()
        result.returncode = 0
        return result

    return fake_run


def test_cr2_to_jpg_with_title(tmp_path):
    """Test cr2_to_jpg adds a title annotation via magick when title is provided."""
    cr2_fake = tmp_path / "test.cr2"
    cr2_fake.touch()
    jpg_path = tmp_path / "titled.jpg"

    with (
        patch("panoptes.utils.images.cr2.shutil.which", return_value="/usr/bin/magick"),
        patch("panoptes.utils.images.cr2.subprocess.run", side_effect=_make_fake_run()),
    ):
        result = cr2_utils.cr2_to_jpg(str(cr2_fake), jpg_path, title="Test Title")

    assert result == jpg_path
    assert jpg_path.exists()


def test_cr2_to_jpg_with_title_calls_magick(tmp_path):
    """Test that cr2_to_jpg invokes magick with the correct arguments when a title is given."""
    cr2_fake = tmp_path / "test.cr2"
    cr2_fake.touch()
    jpg_path = tmp_path / "titled2.jpg"

    magick_calls = []
    with (
        patch("panoptes.utils.images.cr2.shutil.which", return_value="/usr/bin/magick"),
        patch("panoptes.utils.images.cr2.subprocess.run", side_effect=_make_fake_run(magick_calls)),
    ):
        cr2_utils.cr2_to_jpg(str(cr2_fake), jpg_path, title="My Title")

    assert len(magick_calls) == 1
    magick_cmd = magick_calls[0]
    assert magick_cmd[0] == "/usr/bin/magick"
    assert "-annotate" in magick_cmd
    assert "My Title" in magick_cmd
    assert "-fill" in magick_cmd
    assert "red" in magick_cmd


def test_cr2_to_jpg_no_title_skips_magick(tmp_path):
    """Test that cr2_to_jpg does not call magick when no title is provided."""
    cr2_fake = tmp_path / "test.cr2"
    cr2_fake.touch()
    jpg_path = tmp_path / "no_title.jpg"

    magick_calls = []
    with (
        patch("panoptes.utils.images.cr2.shutil.which", return_value="/usr/bin/magick"),
        patch("panoptes.utils.images.cr2.subprocess.run", side_effect=_make_fake_run(magick_calls)),
    ):
        cr2_utils.cr2_to_jpg(str(cr2_fake), jpg_path, title="")

    assert len(magick_calls) == 0


def test_cr2_to_jpg_already_exists_raises(tmp_path):
    """Test that cr2_to_jpg raises AlreadyExists when output exists and overwrite=False."""
    cr2_fake = tmp_path / "test.cr2"
    cr2_fake.touch()
    jpg_path = tmp_path / "existing.jpg"
    jpg_path.touch()

    with pytest.raises(error.AlreadyExists):
        cr2_utils.cr2_to_jpg(str(cr2_fake), jpg_path, overwrite=False)
