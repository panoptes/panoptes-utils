import os
import pytest
import subprocess
import shutil

from astropy.io.fits import Header
from astropy import units as u

from panoptes.utils.images import fits as fits_utils


@pytest.fixture
def solved_fits_file(data_dir):
    return os.path.join(data_dir, 'solved.fits.fz')


def test_wcsinfo(solved_fits_file):
    wcsinfo = fits_utils.get_wcsinfo(solved_fits_file)

    assert 'wcs_file' in wcsinfo
    assert wcsinfo['ra_center'].value == 303.206422334


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


def test_getheader(solved_fits_file):
    header = fits_utils.getheader(solved_fits_file)
    assert isinstance(header, Header)
    assert header['IMAGEID'] == 'PAN001_XXXXXX_20160909T081152'


def test_getval(solved_fits_file):
    img_id = fits_utils.getval(solved_fits_file, 'IMAGEID')
    assert img_id == 'PAN001_XXXXXX_20160909T081152'


def test_solve_field_unsolved(unsolved_fits_file):
    with pytest.raises(KeyError):
        fits_utils.getval(unsolved_fits_file, 'WCSAXES')

    assert 'crpix0' not in fits_utils.get_wcsinfo(unsolved_fits_file)

    proc = fits_utils.solve_field(unsolved_fits_file)
    assert isinstance(proc, subprocess.Popen)
    proc.wait()
    try:
        outs, errs = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()

    assert proc.returncode == 0, f'{outs}\n{errs}'

    wcs_info = fits_utils.get_wcsinfo(unsolved_fits_file.replace('.fits', '.new'))
    assert 'crpix0' in wcs_info
    assert wcs_info['crpix0'] == 350.5 * u.pixel


def test_get_solve_field_solved(solved_fits_file):
    orig_wcs = fits_utils.get_wcsinfo(solved_fits_file)
    assert 'crpix0' in orig_wcs

    solve_info = fits_utils.get_solve_field(solved_fits_file, skip_solved=False)
    assert isinstance(solve_info, dict)
    # 1-based numbering from WCS.
    assert 'CRPIX1' in solve_info


def test_solve_options(solved_fits_file):
    proc = fits_utils.solve_field(
        solved_fits_file, solve_opts=['--guess-scale'])
    assert isinstance(proc, subprocess.Popen)
    proc.wait()
    assert proc.returncode == 0


def test_solve_bad_field(solved_fits_file):
    proc = fits_utils.solve_field('Foo.fits')
    outs, errs = proc.communicate()
    print('outs', outs)
    print('errs', errs)
    assert 'ERROR' in errs
