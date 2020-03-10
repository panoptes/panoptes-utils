import os
import shutil
import subprocess

from warnings import warn

from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u

from ..logger import logger
from .. import error


def solve_field(fname, timeout=15, solve_opts=None, **kwargs):
    """ Plate solves an image.

    Note: see `get_solved_field` for preferred solving function.

    Args:
        fname(str, required):       Filename to solve in .fits extension.
        timeout(int, optional):     Timeout for the solve-field command,
                                    defaults to 60 seconds.
        solve_opts(list, optional): List of options for solve-field.
    """
    solve_field_script = shutil.which('panoptes-solve-field')

    if solve_field_script is None:  # pragma: no cover
        raise error.InvalidSystemCommand(
            "Can't find panoptes-solve-field: {}".format(solve_field_script))

    # Add the options for solving the field
    if solve_opts is not None:
        options = solve_opts
    else:
        options = [
            '--guess-scale',
            '--cpulimit', str(timeout),
            '--no-verify',
            '--no-plots',
            '--crpix-center',
            '--match', 'none',
            '--corr', 'none',
            '--wcs', 'none',
            '--downsample', '4',
        ]

        if kwargs.get('overwrite', False):
            options.append('--overwrite')
        if kwargs.get('skip_solved', False):
            options.append('--skip-solved')

        if 'ra' in kwargs:
            options.append('--ra')
            options.append(str(kwargs.get('ra')))
        if 'dec' in kwargs:
            options.append('--dec')
            options.append(str(kwargs.get('dec')))
        if 'radius' in kwargs:
            options.append('--radius')
            options.append(str(kwargs.get('radius')))

    if fname.endswith('.fz'):
        options.append('--extension=1')

    cmd = [solve_field_script] + options + [fname]

    try:
        proc = subprocess.Popen(cmd,
                                universal_newlines=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except OSError as e:
        raise error.InvalidCommand(
            "Can't send command to panoptes-solve-field: {} \t {}".format(e, cmd))
    except ValueError as e:
        raise error.InvalidCommand(
            "Bad parameters to solve_field: {} \t {}".format(e, cmd))
    except Exception as e:
        raise error.PanError("Timeout on plate solving: {}".format(e))

    return proc


def get_solve_field(fname, replace=True, remove_extras=True, **kwargs):
    """Convenience function to wait for `solve_field` to finish.

    This function merely passes the `fname` of the image to be solved along to `solve_field`,
    which returns a subprocess.Popen object. This function then waits for that command
    to complete, populates a dictonary with the EXIF informaiton and returns. This is often
    more useful than the raw `solve_field` function

    Example:

    >>> from panoptes.utils.images import fits as fits_utils

    >>> # Get our fits filename
    >>> fits_fn = getfixture('unsolved_fits_file')

    >>> # Perform the Solve
    >>> solve_info = fits_utils.get_solve_field(fits_fn)

    >>> # Show solved Filename
    >>> solve_info['solved_fits_file']
    '/var/panoptes/panoptes-utils/panoptes/tests/data/unsolved.fits'

    >>> #Try to pass a suggested location
    >>> ra = 15.23
    >>> dec = 90
    >>> fits_utils.get_solve_field(fits_fn, 'ra'=ra, 'dec'=dec)

    >>> radius = 5 # deg
    >>> fits_utils.solve_field(fits_fn, 'radius'=radius)

    Args:
        fname ({str}): Name of FITS file to be solved
        replace (bool, optional): Replace fname the solved file
        remove_extras (bool, optional): Remove the files generated by solver
        **kwargs ({dict}): Options to pass to `solve_field`

    Returns:
        dict: Keyword information from the solved field
    """
    skip_solved = kwargs.get('skip_solved', True)

    out_dict = {}
    output = None
    errs = None

    file_path, file_ext = os.path.splitext(fname)

    header = getheader(fname)
    wcs = WCS(header)

    # Check for solved file
    if skip_solved and wcs.is_celestial:
        logger.info(f"Solved file exists, skipping (use skip_solved=False to solve again): {fname}")

        out_dict.update(header)
        out_dict['solved_fits_file'] = fname
        return out_dict

    # Set a default radius of 15
    kwargs.setdefault('radius', 15)

    proc = solve_field(fname, **kwargs)
    try:
        output, errs = proc.communicate(timeout=kwargs.get('timeout', 30))
    except subprocess.TimeoutExpired:
        proc.kill()
        output, errs = proc.communicate()
        print(f'Timeout on {fname}')
        print(f'Output on {fname}: {output}')
        print(f'Errors on {fname}: {errs}')
        raise error.Timeout(f'Timeout while solving: {output!r} {errs!r}')
    else:
        logger.debug(f'Returncode: {proc.returncode}')
        logger.debug(f'Output on {fname}: {output}')
        logger.debug(f'Errors on {fname}: {errs}')

        if proc.returncode == 3:
            raise error.SolveError(f'solve-field not found: {output}')

        if not os.path.exists(fname.replace(file_ext, '.solved')):
            raise error.SolveError('File not solved')

        try:
            # Handle extra files created by astrometry.net
            new = fname.replace(file_ext, '.new')
            rdls = fname.replace(file_ext, '.rdls')
            axy = fname.replace(file_ext, '.axy')
            xyls = fname.replace(file_ext, '-indx.xyls')

            if replace and os.path.exists(new):
                # Remove converted fits
                os.remove(fname)
                # Rename solved fits to proper extension
                os.rename(new, fname)

                out_dict['solved_fits_file'] = fname
            else:
                out_dict['solved_fits_file'] = new

            if remove_extras:
                for f in [rdls, xyls, axy]:
                    if os.path.exists(f):
                        os.remove(f)

        except Exception as e:
            warn(f'Cannot remove extra files: {e!r}')

    if errs is not None and errs > '':
        warn(f'Error in solving: {errs!r}')
    else:

        try:
            out_dict.update(getheader(fname))
        except OSError:
            logger.warning(f"Can't read fits header for: {fname}")

    return out_dict


def get_wcsinfo(fits_fname, **kwargs):
    """Returns the WCS information for a FITS file.

    Uses the `wcsinfo` astrometry.net utility script to get the WCS information
    from a plate-solved file.

    Args:
        fits_fname ({str}): Name of a FITS file that contains a WCS.
        **kwargs: Args that can be passed to wcsinfo.

    Returns:
        dict: Output as returned from `wcsinfo`

    Raises:
        error.InvalidCommand: Raised if `wcsinfo` is not found (part of astrometry.net)
    """
    assert os.path.exists(fits_fname), warn(f"No file exists at: {fits_fname}")

    wcsinfo = shutil.which('wcsinfo')
    if wcsinfo is None:
        raise error.InvalidCommand('wcsinfo not found')

    run_cmd = [wcsinfo, fits_fname]

    if fits_fname.endswith('.fz'):
        run_cmd.append('-e')
        run_cmd.append('1')

    logger.debug("wcsinfo command: {}".format(run_cmd))

    proc = subprocess.Popen(run_cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True)
    try:
        output, errs = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:  # pragma: no cover
        proc.kill()
        output, errs = proc.communicate()

    unit_lookup = {
        'crpix0': u.pixel,
        'crpix1': u.pixel,
        'crval0': u.degree,
        'crval1': u.degree,
        'cd11': (u.deg / u.pixel),
        'cd12': (u.deg / u.pixel),
        'cd21': (u.deg / u.pixel),
        'cd22': (u.deg / u.pixel),
        'imagew': u.pixel,
        'imageh': u.pixel,
        'pixscale': (u.arcsec / u.pixel),
        'orientation': u.degree,
        'ra_center': u.degree,
        'dec_center': u.degree,
        'orientation_center': u.degree,
        'ra_center_h': u.hourangle,
        'ra_center_m': u.minute,
        'ra_center_s': u.second,
        'dec_center_d': u.degree,
        'dec_center_m': u.minute,
        'dec_center_s': u.second,
        'fieldarea': (u.degree * u.degree),
        'fieldw': u.degree,
        'fieldh': u.degree,
        'decmin': u.degree,
        'decmax': u.degree,
        'ramin': u.degree,
        'ramax': u.degree,
        'ra_min_merc': u.degree,
        'ra_max_merc': u.degree,
        'dec_min_merc': u.degree,
        'dec_max_merc': u.degree,
        'merc_diff': u.degree,
    }

    wcs_info = {}
    for line in output.split('\n'):
        try:
            k, v = line.split(' ')
            try:
                v = float(v)
            except Exception:
                pass

            wcs_info[k] = float(v) * unit_lookup.get(k, 1)
        except ValueError:
            pass
            # print("Error on line: {}".format(line))

    wcs_info['wcs_file'] = fits_fname

    return wcs_info


def improve_wcs(fname, remove_extras=True, replace=True, timeout=30, **kwargs):
    """Improve the world-coordinate-system (WCS) of a FITS file.

    This will plate-solve an already-solved field, using a verification process
    that will also attempt a SIP distortion correction.

    Args:
        fname (str): Full path to FITS file.
        remove_extras (bool, optional): If generated files should be removed, default True.
        replace (bool, optional): Overwrite existing file, default True.
        timeout (int, optional): Timeout for the solve, default 30 seconds.
        **kwargs: Additional keyword args for `solve_field`.

    Returns:
        dict: FITS headers, including solve information.

    Raises:
        error.SolveError: Description
        error.Timeout: Description
    """
    out_dict = {}
    output = None
    errs = None

    options = [
        '--continue',
        '-t', '3',
        '-q', '0.1',
        '--no-plots',
        '--guess-scale',
        '--cpulimit', str(timeout),
        '--no-verify',
        '--crpix-center',
        '--match', 'none',
        '--corr', 'none',
        '--wcs', 'none',
        '-V', fname,
    ]

    proc = solve_field(fname, solve_opts=options, **kwargs)
    try:
        output, errs = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise error.Timeout("Timeout while solving")
    else:
        logger.debug(f"Output: {output}")
        logger.debug(f"Errors: {errs}")

        if not os.path.exists(fname.replace('.fits', '.solved')):
            raise error.SolveError('File not solved')

        try:
            # Handle extra files created by astrometry.net
            new = fname.replace('.fits', '.new')
            rdls = fname.replace('.fits', '.rdls')
            axy = fname.replace('.fits', '.axy')
            xyls = fname.replace('.fits', '-indx.xyls')

            if replace and os.path.exists(new):
                # Remove converted fits
                os.remove(fname)
                # Rename solved fits to proper extension
                os.rename(new, fname)

                out_dict['solved_fits_file'] = fname
            else:
                out_dict['solved_fits_file'] = new

            if remove_extras:
                for f in [rdls, xyls, axy]:
                    if os.path.exists(f):
                        os.remove(f)

        except Exception as e:
            warn('Cannot remove extra files: {}'.format(e))

    if errs is not None:
        warn("Error in solving: {}".format(errs))
    else:
        try:
            out_dict.update(fits.getheader(fname))
        except OSError:
            logger.warning(f"Can't read fits header for {fname}")

    return out_dict


def fpack(fits_fname, unpack=False):
    """Compress/Decompress a FITS file

    Uses `fpack` (or `funpack` if `unpack=True`) to compress a FITS file

    Args:
        fits_fname ({str}): Name of a FITS file that contains a WCS.
        unpack ({bool}, optional): file should decompressed instead of compressed, default False.

    Returns:
        str: Filename of compressed/decompressed file.
    """
    assert os.path.exists(fits_fname), warn(
        "No file exists at: {}".format(fits_fname))

    if unpack:
        fpack = shutil.which('funpack')
        run_cmd = [fpack, '-D', fits_fname]
        out_file = fits_fname.replace('.fz', '')
    else:
        fpack = shutil.which('fpack')
        run_cmd = [fpack, '-D', '-Y', fits_fname]
        out_file = fits_fname.replace('.fits', '.fits.fz')

    try:
        assert fpack is not None
    except AssertionError:
        warn("fpack not found (try installing cfitsio). File has not been changed")
        return fits_fname

    logger.debug("fpack command: {}".format(run_cmd))

    proc = subprocess.Popen(run_cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, universal_newlines=True)
    try:
        output, errs = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        output, errs = proc.communicate()

    return out_file


def funpack(*args, **kwargs):
    """Unpack a FITS file.

    Note:
        This is a thin-wrapper around the ~fpack function
        with the `unpack=True` option specified. See ~fpack
        documentation for details.

    Args:
        *args: Arguments passed to ~fpack.
        **kwargs: Keyword arguments passed to ~fpack.

    Returns:
        str: Path to uncompressed FITS file.
    """
    return fpack(*args, unpack=True, **kwargs)


def write_fits(data, header, filename, exposure_event=None, **kwargs):
    """Write FITS file to requested location.

    >>> from panoptes.utils.images import fits as fits_utils
    >>> data = np.random.normal(size=100)
    >>> header = { 'FILE': 'delete_me', 'TEST': True }
    >>> filename = str(getfixture('tmpdir').join('temp.fits'))
    >>> fits_utils.write_fits(data, header, filename)
    >>> assert os.path.exists(filename)

    >>> fits_utils.getval(filename, 'FILE')
    'delete_me'
    >>> data2 = fits_utils.getdata(filename)
    >>> assert np.array_equal(data, data2)

    Args:
        data (array_like): The data to be written.
        header (dict): Dictionary of items to be saved in header.
        filename (str): Path to filename for output.
        exposure_event (None|`threading.Event`, optional): A `threading.Event` that
            can be triggered when the image is written.
    """
    if not isinstance(header, fits.Header):
        header = fits.Header(header)

    hdu = fits.PrimaryHDU(data, header=header)

    # Create directories if required.
    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), mode=0o775, exist_ok=True)

    try:
        hdu.writeto(filename)
    except OSError as err:
        logger.error('Error writing image to {}!'.format(filename))
        logger.error(err)
    else:
        logger.debug('Image written to {}'.format(filename))
    finally:
        if exposure_event:
            exposure_event.set()


def update_observation_headers(file_path, info):
    """Update FITS headers with items from the Observation status.

    Args:
        file_path (str): Path to a FITS file.
        info (dict): The return dict from `pocs.observatory.Observation.status`,
            which includes basic information about the observation.
    """
    with fits.open(file_path, 'update') as f:
        hdu = f[0]
        hdu.header.set('IMAGEID', info.get('image_id', ''))
        hdu.header.set('SEQID', info.get('sequence_id', ''))
        hdu.header.set('FIELD', info.get('field_name', ''))
        hdu.header.set('RA-MNT', info.get('ra_mnt', ''), 'Degrees')
        hdu.header.set('HA-MNT', info.get('ha_mnt', ''), 'Degrees')
        hdu.header.set('DEC-MNT', info.get('dec_mnt', ''), 'Degrees')
        hdu.header.set('EQUINOX', info.get('equinox', 2000.))  # Assume J2000
        hdu.header.set('AIRMASS', info.get('airmass', ''), 'Sec(z)')
        hdu.header.set('FILTER', info.get('filter', ''))
        hdu.header.set('LAT-OBS', info.get('latitude', ''), 'Degrees')
        hdu.header.set('LONG-OBS', info.get('longitude', ''), 'Degrees')
        hdu.header.set('ELEV-OBS', info.get('elevation', ''), 'Meters')
        hdu.header.set('MOONSEP', info.get('moon_separation', ''), 'Degrees')
        hdu.header.set('MOONFRAC', info.get('moon_fraction', ''))
        hdu.header.set('CREATOR', info.get('creator', ''), 'POCS Software version')
        hdu.header.set('INSTRUME', info.get('camera_uid', ''), 'Camera ID')
        hdu.header.set('OBSERVER', info.get('observer', ''), 'PANOPTES Unit ID')
        hdu.header.set('ORIGIN', info.get('origin', ''))
        hdu.header.set('RA-RATE', info.get('tracking_rate_ra', ''), 'RA Tracking Rate')


def getdata(fn, *args, **kwargs):
    """Get the FITS data.

    Small wrapper around `astropy.io.fits.getdata` to auto-determine
    the FITS extension. This will return the data associated with the
    image.

    >>> fits_fn = getfixture('solved_fits_file')
    >>> getdata(fits_fn)
    array([[2215, 2169, 2200, ..., 2169, 2235, 2168],
           [2123, 2191, 2133, ..., 2212, 2127, 2217],
           [2208, 2154, 2209, ..., 2159, 2233, 2187],
           ...,
           [2120, 2201, 2120, ..., 2209, 2126, 2195],
           [2219, 2151, 2199, ..., 2173, 2214, 2166],
           [2114, 2194, 2122, ..., 2202, 2125, 2204]], dtype=uint16)

    Args:
        fn (str): Path to FITS file.
        *args: Passed to `astropy.io.fits.getdata`.
        **kwargs: Passed to `astropy.io.fits.getdata`.

    Returns:
        `astropy.io.fits.header.Header`: The FITS data.
    """
    return fits.getdata(fn)


def getheader(fn, *args, **kwargs):
    """Get the FITS header.

    Small wrapper around `astropy.io.fits.getheader` to auto-determine
    the FITS extension. This will return the header associated with the
    image. If you need the compression header information use the astropy
    module directly.

    >>> fits_fn = getfixture('tiny_fits_file')
    >>> os.path.basename(fits_fn)
    'tiny.fits'
    >>> header = getheader(fits_fn)
    >>> header['IMAGEID']
    'PAN001_XXXXXX_20160909T081152'

    >>> # Works with fpacked files
    >>> fits_fn = getfixture('solved_fits_file')
    >>> os.path.basename(fits_fn)
    'solved.fits.fz'
    >>> header = getheader(fits_fn)
    >>> header['IMAGEID']
    'PAN001_XXXXXX_20160909T081152'

    Args:
        fn (str): Path to FITS file.
        *args: Passed to `astropy.io.fits.getheader`.
        **kwargs: Passed to `astropy.io.fits.getheader`.

    Returns:
        `astropy.io.fits.header.Header`: The FITS header for the data.
    """
    ext = 0
    if fn.endswith('.fz'):
        ext = 1
    return fits.getheader(fn, ext=ext)


def getval(fn, *args, **kwargs):
    """Get a value from the FITS header.

    Small wrapper around `astropy.io.fits.getval` to auto-determine
    the FITS extension. This will return the value from the header
    associated with the image (not the compression header). If you need
    the compression header information use the astropy module directly.

    >>> fits_fn = getfixture('tiny_fits_file')
    >>> getval(fits_fn, 'IMAGEID')
    'PAN001_XXXXXX_20160909T081152'

    Args:
        fn (str): Path to FITS file.

    Returns:
        str or float: Value from header (with no type conversion).
    """
    ext = 0
    if fn.endswith('.fz'):
        ext = 1
    return fits.getval(fn, *args, ext=ext, **kwargs)
