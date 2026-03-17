"""Tests for the panoptes-utils image CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from panoptes.utils import error
from panoptes.utils.cli.image import solve_fits
from panoptes.utils.cli.main import app


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# image cr2 to-jpg
# ---------------------------------------------------------------------------


def test_cr2_to_jpg_success(runner):
    """image cr2 to-jpg should print the source and destination paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cr2 = Path(tmpdir) / "fake.cr2"
        fake_cr2.write_bytes(b"fake cr2 data")
        jpg_path = Path(tmpdir) / "fake.jpg"
        jpg_path.write_bytes(b"fake jpg data")  # pre-create so .exists() returns True

        with patch("panoptes.utils.cli.image.cr2.cr2_to_jpg", return_value=jpg_path):
            result = runner.invoke(app, ["image", "cr2", "to-jpg", str(fake_cr2)])

    assert result.exit_code == 0
    assert "Converting" in result.stdout
    assert "Wrote" in result.stdout


def test_cr2_to_jpg_no_output_file(runner):
    """image cr2 to-jpg should not print 'Wrote' if the jpg was not created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cr2 = Path(tmpdir) / "fake.cr2"
        fake_cr2.write_bytes(b"fake cr2 data")
        missing_jpg = Path(tmpdir) / "missing.jpg"  # intentionally not created

        with patch("panoptes.utils.cli.image.cr2.cr2_to_jpg", return_value=missing_jpg):
            result = runner.invoke(app, ["image", "cr2", "to-jpg", str(fake_cr2)])

    assert result.exit_code == 0
    assert "Converting" in result.stdout
    assert "Wrote" not in result.stdout


# ---------------------------------------------------------------------------
# image cr2 to-fits
# ---------------------------------------------------------------------------


def test_cr2_to_fits_without_output_arg(runner):
    """image cr2 to-fits without an explicit output path returns no output path message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cr2 = Path(tmpdir) / "fake.cr2"
        fake_cr2.write_bytes(b"fake cr2 data")
        fits_path = Path(tmpdir) / "fake.fits"

        with patch("panoptes.utils.cli.image.cr2.cr2_to_fits", return_value=str(fits_path)):
            result = runner.invoke(app, ["image", "cr2", "to-fits", str(fake_cr2)])

    assert result.exit_code == 0
    assert "Converting" in result.stdout
    # When no --fits-fname is given the function returns early without printing the path.
    assert "FITS file available" not in result.stdout


def test_cr2_to_fits_with_output_arg(runner):
    """image cr2 to-fits with an explicit output path prints the destination."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_cr2 = Path(tmpdir) / "fake.cr2"
        fake_cr2.write_bytes(b"fake cr2 data")
        fits_path = Path(tmpdir) / "output.fits"

        with patch("panoptes.utils.cli.image.cr2.cr2_to_fits", return_value=str(fits_path)):
            result = runner.invoke(
                app,
                ["image", "cr2", "to-fits", str(fake_cr2), "--fits-fname", str(fits_path)],
            )

    assert result.exit_code == 0
    assert "Converting" in result.stdout
    assert "FITS file available" in result.stdout


# ---------------------------------------------------------------------------
# image fits solve  — tested via direct function calls because the Typer
# command accepts **kwargs which prevents invocation through the CLI runner.
# ---------------------------------------------------------------------------


def test_solve_fits_success():
    """solve_fits should return the solved file path on success."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_fits = Path(tmpdir) / "fake.fits"
        fake_fits.write_bytes(b"SIMPLE  =                    T")

        with patch(
            "panoptes.utils.cli.image.fits_utils.get_solve_field",
            return_value={"solved_fits_file": str(fake_fits)},
        ):
            result = solve_fits(fake_fits)

    assert result == fake_fits


def test_solve_fits_invalid_system_command():
    """solve_fits should return None and print an error for InvalidSystemCommand."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_fits = Path(tmpdir) / "fake.fits"
        fake_fits.write_bytes(b"SIMPLE  =                    T")

        with patch(
            "panoptes.utils.cli.image.fits_utils.get_solve_field",
            side_effect=error.InvalidSystemCommand("solve-field not found"),
        ):
            result = solve_fits(fake_fits)

    assert result is None
