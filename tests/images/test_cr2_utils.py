import os
import tempfile
from pathlib import Path


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
