import os
import shutil
import subprocess

from warnings import warn

from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u

from panoptes.utils import error


def solve_field(fname, timeout=15, solve_opts=None, **kwargs):
    """ Plate solves an image.

    Args:
        fname(str, required):       Filename to solve in .fits extension.
        timeout(int, optional):     Timeout for the solve-field command,
                                    defaults to 60 seconds.
        solve_opts(list, optional): List of options for solve-field.
        verbose(bool, optional):    Show output, defaults to False.
    """
    verbose = kwargs.get('verbose', False)
    if verbose:
        print("Entering solve_field")

    solve_field_script = os.path.join(
        os.getenv('PANDIR'), 'panoptes-utils', 'scripts', 'solve_field.sh')

    if not os.path.exists(solve_field_script):  # pragma: no cover
        raise error.InvalidSystemCommand(
            "Can't find solve-field: {}".format(solve_field_script))

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
    if verbose:
        print("Cmd:", cmd)

    try:
        proc = subprocess.Popen(cmd, universal_newlines=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as e:
        raise error.InvalidCommand(
            "Can't send command to solve_field.sh: {} \t {}".format(e, cmd))
    except ValueError as e:
        raise error.InvalidCommand(
            "Bad parameters to solve_field: {} \t {}".format(e, cmd))
    except Exception as e:
        raise error.PanError("Timeout on plate solving: {}".format(e))

    if verbose:
        print("Returning proc from solve_field")

    return proc


def get_solve_field(fname, replace=True, remove_extras=True, **kwargs):
    """Convenience function to wait for `solve_field` to finish.

    This function merely passes the `fname` of the image to be solved along to `solve_field`,
    which returns a subprocess.Popen object. This function then waits for that command
    to complete, populates a dictonary with the EXIF informaiton and returns. This is often
    more useful than the raw `solve_field` function

    Args:
        fname ({str}): Name of FITS file to be solved
        replace (bool, optional): Replace fname the solved file
        remove_extras (bool, optional): Remove the files generated by solver
        **kwargs ({dict}): Options to pass to `solve_field`

    Returns:
        dict: Keyword information from the solved field
    """
    verbose = kwargs.get('verbose', False)
    skip_solved = kwargs.get('skip_solved', True)

    out_dict = {}
    output = None
    errs = None

    file_path, file_ext = os.path.splitext(fname)

    header = getheader(fname)
    wcs = WCS(header)

    # Check for solved file
    if skip_solved and wcs.is_celestial:

        if verbose:
            print("Solved file exists, skipping",
                  "(pass skip_solved=False to solve again):",
                  fname)

        out_dict.update(header)
        out_dict['solved_fits_file'] = fname
        return out_dict

    if verbose:
        print("Entering get_solve_field:", fname)

    # Set a default radius of 15
    kwargs.setdefault('radius', 15)

    proc = solve_field(fname, **kwargs)
    try:
        output, errs = proc.communicate(timeout=kwargs.get('timeout', 30))
    except subprocess.TimeoutExpired:
        proc.kill()
        raise error.Timeout("Timeout while solving")
    else:
        if verbose:
            print("Returncode:", proc.returncode)
            print("Output:", output)
            print("Errors:", errs)

        if proc.returncode == 3:
            raise error.SolveError('solve-field not found: {}'.format(output))

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
            warn('Cannot remove extra files: {}'.format(e))

    if errs is not None:
        warn("Error in solving: {}".format(errs))
    else:

        try:
            out_dict.update(getheader(fname))
        except OSError:
            if verbose:
                print("Can't read fits header for:", fname)

    return out_dict


def get_wcsinfo(fits_fname, verbose=False):
    """Returns the WCS information for a FITS file.

    Uses the `wcsinfo` astrometry.net utility script to get the WCS information
    from a plate-solved file.

    Parameters
    ----------
    fits_fname : {str}
        Name of a FITS file that contains a WCS.
    verbose : {bool}, optional
        Verbose (the default is False)
    Returns
    -------
    dict
        Output as returned from `wcsinfo`
    """
    assert os.path.exists(fits_fname), warn(
        "No file exists at: {}".format(fits_fname))

    wcsinfo = shutil.which('wcsinfo')
    if wcsinfo is None:
        raise error.InvalidCommand('wcsinfo not found')

    run_cmd = [wcsinfo, fits_fname]

    if fits_fname.endswith('.fz'):
        run_cmd.append('-e')
        run_cmd.append('1')

    if verbose:
        print("wcsinfo command: {}".format(run_cmd))

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
        **kwargs: Additional keyword args for `solve_field`. Can also include a
            `verbose` flag.

    Returns:
        dict: FITS headers, including solve information.

    Raises:
        error.SolveError: Description
        error.Timeout: Description
    """
    verbose = kwargs.get('verbose', False)
    out_dict = {}
    output = None
    errs = None

    if verbose:
        print("Entering improve_wcs: {}".format(fname))

    options = [
        '--continue',
        '-t', '3',
        '-q', '0.01',
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
        if verbose:
            print("Output: {}", output)
            print("Errors: {}", errs)

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
            if verbose:
                print("Can't read fits header for {}".format(fname))

    return out_dict


def fpack(fits_fname, unpack=False, verbose=False):
    """Compress/Decompress a FITS file

    Uses `fpack` (or `funpack` if `unpack=True`) to compress a FITS file

    Args:
        fits_fname ({str}): Name of a FITS file that contains a WCS.
        unpack ({bool}, optional): file should decompressed instead of compressed, default False.
        verbose ({bool}, optional): Verbose, default False.

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

    if verbose:
        print("fpack command: {}".format(run_cmd))

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


def write_fits(data, header, filename, logger=None, exposure_event=None):
    """
    Write FITS file to requested location
    """
    hdu = fits.PrimaryHDU(data, header=header)

    # Create directories if required.
    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), mode=0o775, exist_ok=True)

    try:
        hdu.writeto(filename)
    except OSError as err:
        if logger:
            logger.error('Error writing image to {}!'.format(filename))
            logger.error(err)
    else:
        if logger:
            logger.debug('Image written to {}'.format(filename))
    finally:
        if exposure_event:
            exposure_event.set()


def update_headers(file_path, info):
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

    Args:
        fn (str): Path to FITS file.

    Returns:
        str or float: Value from header (with no type conversion).
    """
    ext = 0
    if fn.endswith('.fz'):
        ext = 1
    return fits.getval(fn, *args, ext=ext, **kwargs)
