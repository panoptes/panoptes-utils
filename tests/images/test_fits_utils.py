import os
import shutil
import subprocess
from contextlib import suppress

import pytest
from astropy import units as u
from astropy.io.fits import Header

from panoptes.utils import error
from panoptes.utils.images import fits as fits_utils


@pytest.mark.plate_solve
def test_wcsinfo(solved_fits_file):
    wcsinfo = fits_utils.get_wcsinfo(solved_fits_file)

    assert 'wcs_file' in wcsinfo
    assert wcsinfo['ra_center'].value == pytest.approx(303.20, rel=1e-2)


@pytest.mark.plate_solve
def test_fpack(solved_fits_file):
    new_file = solved_fits_file.replace('solved', 'solved_copy')
    copy_file = shutil.copyfile(solved_fits_file, new_file)
    info = os.stat(copy_file)
    assert info.st_size > 0.

    uncompressed = fits_utils.funpack(copy_file)
    assert os.stat(uncompressed).st_size > info.st_size

    compressed = fits_utils.fpack(uncompressed)
    assert os.stat(compressed).st_size == info.st_size

    os.remove(copy_file)


@pytest.mark.plate_solve
def test_no_overwrite_fpack(solved_fits_file):
    new_file = solved_fits_file.replace('solved', 'solved_copy')
    copy_file = shutil.copyfile(solved_fits_file, new_file)

    # Unpack the file. This removes the packed version.
    uncompressed = fits_utils.funpack(copy_file)

    # Copy file again so now the packed version exists alongside unpacked.
    copy_file = shutil.copyfile(solved_fits_file, new_file)

    # Deny overwriting gives error.
    with pytest.raises(FileExistsError):
        _ = fits_utils.fpack(uncompressed, overwrite=False)

    # Default is overwrite=True.
    compressed = fits_utils.fpack(uncompressed)

    # Cleanup test.
    for file in [copy_file, uncompressed, compressed]:
        with suppress(FileNotFoundError):
            os.remove(file)


def test_getheader(solved_fits_file):
    header = fits_utils.getheader(solved_fits_file)
    assert isinstance(header, Header)
    assert header['IMAGEID'] == 'PAN001_XXXXXX_20160909T081152'


def test_getval(solved_fits_file):
    img_id = fits_utils.getval(solved_fits_file, 'IMAGEID')
    assert img_id == 'PAN001_XXXXXX_20160909T081152'


@pytest.mark.plate_solve
def test_solve_field_unsolved(unsolved_fits_file):
    with pytest.raises(KeyError):
        fits_utils.getval(unsolved_fits_file, 'WCSAXES')

    assert 'crpix0' not in fits_utils.get_wcsinfo(unsolved_fits_file)

    proc = fits_utils.solve_field(unsolved_fits_file)
    assert isinstance(proc, subprocess.Popen)
    proc.wait()
    outs, errs = proc.communicate(timeout=15)

    assert proc.returncode == 0, f'{outs}\n{errs}'

    wcs_info = fits_utils.get_wcsinfo(unsolved_fits_file.replace('.fits', '.new'))
    assert 'crpix0' in wcs_info
    assert wcs_info['crpix0'] == 350.5 * u.pixel

    for ext in ['.wcs', '.new']:
        with suppress(FileNotFoundError):
            os.remove(unsolved_fits_file.replace('.fits', ext))


@pytest.mark.plate_solve
def test_get_solve_field_solved(solved_fits_file):
    orig_wcs = fits_utils.get_wcsinfo(solved_fits_file)
    assert 'crpix0' in orig_wcs

    solve_info = fits_utils.get_solve_field(solved_fits_file, skip_solved=False)
    assert isinstance(solve_info, dict)
    # 1-based numbering from WCS.
    assert 'CRPIX1' in solve_info


@pytest.mark.plate_solve
def test_get_solve_field_timeout(unsolved_fits_file):
    with pytest.raises(error.Timeout):
        solve_info = fits_utils.get_solve_field(unsolved_fits_file, timeout=1)


@pytest.mark.plate_solve
def test_solve_bad_field():
    proc = fits_utils.solve_field('Foo.fits')
    outs, errs = proc.communicate()
    print('outs', outs)
    print('errs', errs)
    assert 'ERROR' in errs
