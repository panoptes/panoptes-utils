import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Pattern, Union, Dict
from warnings import warn

from astropy import units as u
from astropy.io import fits
from astropy.time import Time
from astropy.visualization import ImageNormalize, PercentileInterval, LogStretch
from astropy.wcs import WCS
from dateutil.parser import parse as parse_date
from dateutil.tz import UTC
from loguru import logger
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from panoptes.utils import error
from panoptes.utils.images.misc import mask_saturated
from panoptes.utils.images.plot import get_palette, add_colorbar
from panoptes.utils.time import flatten_time

PATH_MATCHER: Pattern[str] = re.compile(r"""^
                                (?P<pre_info>.*)?                       # Anything before unit_id
                                (?P<unit_id>PAN\d{3})                   # unit_id   - PAN + 3 digits
                                /?(?P<field_name>.*)?                   # Legacy field name - any
                                /(?P<camera_id>[a-gA-G0-9]{6})          # camera_id - 6 digits
                                /(?P<sequence_time>[0-9]{8}T[0-9]{6})   # Observation start time
                                /(?P<image_time>[0-9]{8}T[0-9]{6})      # Image start time
                                (?P<post_info>.*)?                      # Anything after (file ext)
                                $""",
                                        re.VERBOSE)


@dataclass
class ObservationPathInfo:
    """Parse the location path for an image.

    This is a small dataclass that offers some convenience methods for dealing
    with a path based on the image id.

    This would usually be instantiated via `path`:

    >>> from panoptes.utils.images.fits import ObservationPathInfo  # noqa
    >>> bucket_path = 'gs://panoptes-images-background/PAN012/Hd189733/358d0f/20180824T035917/20180824T040118.fits'
    >>> path_info = ObservationPathInfo(path=bucket_path)

    >>> path_info.id
    'PAN012_358d0f_20180824T035917_20180824T040118'

    >>> path_info.unit_id
    'PAN012'

    >>> path_info.sequence_id
    'PAN012_358d0f_20180824T035917'

    >>> path_info.image_id
    'PAN012_358d0f_20180824T040118'

    >>> path_info.as_path(base='/tmp', ext='jpg')
    PosixPath('/tmp/PAN012/358d0f/20180824T035917/20180824T040118.jpg')

    >>> ObservationPathInfo(path='foobar')
    Traceback (most recent call last):
      ...
    ValueError: Invalid path received: self.path='foobar'

    >>> # Works from a fits file directly, which reads header.
    >>> fits_fn = getfixture('unsolved_fits_file')
    >>> path_info = ObservationPathInfo.from_fits(fits_fn)
    >>> path_info.unit_id
    'PAN001'

    """
    unit_id: str = None
    camera_id: str = None
    field_name: str = None
    sequence_time: Union[str, datetime, Time] = None
    image_time: Union[str, datetime, Time] = None
    path: Union[str, Path] = None

    def __post_init__(self):
        """Parse the path when provided upon initialization."""
        if self.path is not None:
            path_match = PATH_MATCHER.match(self.path)
            if path_match is None:
                raise ValueError(f'Invalid path received: {self.path}')

            self.unit_id = path_match.group('unit_id')
            self.camera_id = path_match.group('camera_id')
            self.field_name = path_match.group('field_name')
            self.sequence_time = Time(parse_date(path_match.group('sequence_time')))
            self.image_time = Time(parse_date(path_match.group('image_time')))

    @property
    def id(self):
        """Full path info joined with underscores"""
        return self.get_full_id()

    @property
    def sequence_id(self) -> str:
        """The sequence id."""
        return f'{self.unit_id}_{self.camera_id}_{flatten_time(self.sequence_time)}'

    @property
    def image_id(self) -> str:
        """The matched image id."""
        return f'{self.unit_id}_{self.camera_id}_{flatten_time(self.image_time)}'

    def as_path(self, base: Union[Path, str] = None, ext: str = None) -> Path:
        """Return a Path object."""
        image_str = flatten_time(self.image_time)
        if ext is not None:
            image_str = f'{image_str}.{ext}'

        full_path = Path(self.unit_id, self.camera_id, flatten_time(self.sequence_time), image_str)

        if base is not None:
            full_path = base / full_path

        return full_path

    def get_full_id(self, sep='_') -> str:
        """Returns the full path id with the given separator."""
        return f'{sep}'.join([
            self.unit_id,
            self.camera_id,
            flatten_time(self.sequence_time),
            flatten_time(self.image_time)
        ])

    @classmethod
    def from_fits_header(cls, header):
        try:
            new_instance = cls(path=header['FILENAME'])
        except ValueError:
            sequence_id = header['SEQID']
            image_id = header['IMAGEID']
            unit_id, camera_id, sequence_time = sequence_id.split('_')
            _, _, image_time = image_id.split('_')

            new_instance = cls(unit_id=unit_id,
                               camera_id=camera_id,
                               sequence_time=Time(parse_date(sequence_time)),
                               image_time=Time(parse_date(image_time)))

        return new_instance

    @classmethod
    def from_fits(cls, fits_file):
        return cls.from_fits_header(getheader(fits_file))


def solve_field(fname, timeout=15, solve_opts=None, *args, **kwargs):
    """ Plate solves an image.

    Note: This is a low-level wrapper around the underlying `solve-field`
        program. See `get_solve_field` for more typical usage and examples.


    Args:
        fname(str, required):       Filename to solve in .fits extension.
        timeout(int, optional):     Timeout for the solve-field command,
                                    defaults to 60 seconds.
        solve_opts(list, optional): List of options for solve-field.
    """
    solve_field_script = shutil.which('solve-field')

    if solve_field_script is None:  # pragma: no cover
        raise error.InvalidSystemCommand("Can't find solve-field, is astrometry.net installed?")

    # Add the options for solving the field
    if solve_opts is not None:
        options = solve_opts
    else:
        # Default options
        options = [
            '--guess-scale',
            '--cpulimit', str(timeout),
            '--no-verify',
            '--crpix-center',
            '--temp-axy',
            '--index-xyls', 'none',
            '--solved', 'none',
            '--match', 'none',
            '--rdls', 'none',
            '--corr', 'none',
            '--downsample', '4',
            '--no-plots',
        ]

        if 'ra' in kwargs:
            options.append('--ra')
            options.append(str(kwargs.get('ra')))
        if 'dec' in kwargs:
            options.append('--dec')
            options.append(str(kwargs.get('dec')))
        if 'radius' in kwargs:
            options.append('--radius')
            options.append(str(kwargs.get('radius')))

    # Gather all the kwargs that start with `--` and are not already present.
    logger.debug(f'Adding kwargs: {kwargs!r}')

    def _modify_opt(opt, val):
        if isinstance(val, bool):
            opt_string = str(opt)
        else:
            opt_string = f'{opt}={val}'

        return opt_string

    options.extend([_modify_opt(opt, val)
                    for opt, val
                    in kwargs.items()
                    if opt.startswith('--') and opt not in options])

    cmd = [solve_field_script] + options + [fname]

    logger.debug(f'Solving with: {cmd}')
    try:
        proc = subprocess.Popen(cmd,
                                universal_newlines=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except Exception as e:
        raise error.PanError(f"Problem plate-solving in solve_field: {e!r}")

    return proc


def get_solve_field(fname: Union[str, Path],
                    replace: bool = True,
                    overwrite: bool = True,
                    timeout: float = 30, **kwargs) -> Dict:
    """Convenience function to wait for `solve_field` to finish.

    This function merely passes the `fname` of the image to be solved along to `solve_field`,
    which returns a subprocess.Popen object. This function then waits for that command
    to complete, populates a dictonary with the EXIF informaiton and returns. This is often
    more useful than the raw `solve_field` function.

    Example:

    >>> from panoptes.utils.images import fits as fits_utils

    >>> # Get our fits filename.
    >>> fits_fn = getfixture('unsolved_fits_file')

    >>> # Perform the solve.
    >>> solve_info = fits_utils.get_solve_field(fits_fn)  # doctest: +SKIP

    >>> # Show solved filename.
    >>> solve_info['solved_fits_file']  # doctest: +SKIP
    '.../unsolved.fits'

    >>> # Pass a suggested location.
    >>> ra = 15.23
    >>> dec = 90
    >>> radius = 5 # deg
    >>> solve_info = fits_utils.solve_field(fits_fn, ra=ra, dec=dec, radius=radius)  # doctest: +SKIP

    >>> # Pass kwargs to `solve-field` program.
    >>> solve_kwargs = {'--pnm': '/tmp/awesome.bmp'}
    >>> solve_info = fits_utils.get_solve_field(fits_fn, skip_solved=False, **solve_kwargs) # doctest: +SKIP
    >>> assert os.path.exists('/tmp/awesome.bmp') # doctest: +SKIP

    Args:
        fname ({str}): Name of FITS file to be solved.
        replace (bool, optional): Saves the WCS back to the original file,
            otherwise output base filename with `.new` extension. Default True.
        overwrite (bool, optional): Clobber file, default True. Required if `replace=True`.
        timeout (int, optional): The timeout for solving, default 30 seconds.
        **kwargs ({dict}): Options to pass to `solve_field` should start with `--`.

    Returns:
        dict: Keyword information from the solved field.
    """
    skip_solved = kwargs.get('skip_solved', True)

    if isinstance(fname, Path):
        fname = str(fname)

    out_dict = {}

    header = getheader(fname)
    wcs = WCS(header)

    # Check for solved file
    if skip_solved and wcs.is_celestial:
        logger.info(f"Skipping solved file (use skip_solved=False to solve again): {fname}")

        out_dict.update(header)
        out_dict['solved_fits_file'] = fname
        return out_dict

    # Set a default radius of 15
    if overwrite:
        kwargs['--overwrite'] = True

    # Use unpacked version of file.
    was_compressed = False
    if fname.endswith('.fz'):
        logger.debug(f'Uncompressing {fname}')
        fname = funpack(fname)
        logger.debug(f'Using {fname} for solving')
        was_compressed = True

    logger.debug(f'Use solve arguments: {kwargs!r}')
    proc = solve_field(fname, timeout=timeout, **kwargs)
    try:
        # Timeout plus a small buffer.
        output, errs = proc.communicate(timeout=(timeout))
    except subprocess.TimeoutExpired:
        proc.kill()
        output, errs = proc.communicate()
        raise error.Timeout(f'Timeout while solving: {output!r} {errs!r}')
    else:
        if proc.returncode != 0:
            logger.debug(f'Returncode: {proc.returncode}')
        for log in [output, errs]:
            if log and log > '':
                logger.debug(f'Output on {fname}: {log}')

        if proc.returncode == 3:
            raise error.SolveError(f'solve-field not found: {output}')

    new_fname = fname.replace('.fits', '.new')
    if replace:
        logger.debug(f'Overwriting original {fname}')
        os.replace(new_fname, fname)
    else:
        fname = new_fname

    try:
        header = getheader(fname)
        header.remove('COMMENT', ignore_missing=True, remove_all=True)
        header.remove('HISTORY', ignore_missing=True, remove_all=True)
        out_dict.update(header)
    except OSError:
        logger.warning(f"Can't read fits header for: {fname}")

    # Check it was solved.
    if WCS(header).is_celestial is False:
        raise error.SolveError('File not properly solved, no WCS header present.')

    # Remove WCS file.
    os.remove(fname.replace('.fits', '.wcs'))

    if was_compressed and replace:
        logger.debug(f'Compressing plate-solved {fname}')
        fname = fpack(fname)

    out_dict['solved_fits_file'] = fname

    return out_dict


def get_wcsinfo(fits_fname, **kwargs):
    """Returns the WCS information for a FITS file.

    Uses the `wcsinfo` astrometry.net utility script to get the WCS information
    from a plate-solved file.

    Args:
        fits_fname ({str}): Name of a FITS file that contains a WCS.
        **kwargs: Args that can be passed to wcsinfo.

    Returns:
        dict: Output as returned from `wcsinfo`.

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


def fpack(fits_fname, unpack=False, overwrite=True):
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

    if os.path.exists(out_file):
        if overwrite is False:
            raise FileExistsError('Destination file already exists at location and overwrite=False')
        else:
            os.remove(out_file)

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
        kwargs (dict): Options that are passed to the `astropy.io.fits.PrimaryHDU.writeto`
            method.
    """
    if not isinstance(header, fits.Header):
        header = fits.Header(header)

    hdu = fits.PrimaryHDU(data, header=header)

    # Create directories if required.
    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), mode=0o775, exist_ok=True)

    try:
        hdu.writeto(filename, **kwargs)
    except OSError as err:
        logger.error(f'Error writing image to {filename}: {err!r}')
    else:
        logger.debug(f'Image written to {filename}')
    finally:
        if exposure_event:
            exposure_event.set()


def update_observation_headers(file_path, info):
    """Update FITS headers with items from the Observation status.

    >>> # Check the headers
    >>> from panoptes.utils.images import fits as fits_utils
    >>> fits_fn = getfixture('unsolved_fits_file')
    >>> # Show original value
    >>> fits_utils.getval(fits_fn, 'FIELD')
    'KIC 8462852'

    >>> info = {'field_name': 'Tabbys Star'}
    >>> update_observation_headers(fits_fn, info)
    >>> # Show new value
    >>> fits_utils.getval(fits_fn, 'FIELD')
    'Tabbys Star'

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


def extract_metadata(header: fits.Header) -> dict:
    """Get the metadata from a FITS image.

    This function parses some of the more common headers (some from the
    `update_observation_headers` but others as well) and puts them into a dict
    with the obvious data types converted into objects (e.g. dates and times).

    >>> # Check the headers
    >>> from panoptes.utils.images import fits as fits_utils
    >>> fits_fn = getfixture('unsolved_fits_file')
    >>> header = fits_utils.getheader(fits_fn)
    >>> metadata = extract_metadata(header)
    >>> metadata['unit']['name']
    'PAN001'

    Args:
        header (astropy.io.fits.Header): The Header object from a FITS file.
    """
    path_info = ObservationPathInfo.from_fits_header(header)

    try:
        # Add a units doc if it doesn't exist.
        unit_info = dict(
            unit_id=path_info.unit_id,
            name=header.get('OBSERVER'),
            latitude=header.get('LAT-OBS'),
            longitude=header.get('LONG-OBS'),
            elevation=float(header.get('ELEV-OBS')),
        )

        sequence_info = dict(
            unit_id=path_info.unit_id,
            sequence_id=path_info.sequence_id,
            time=path_info.sequence_time.to_datetime(timezone=UTC),
            exptime=float(header.get('EXPTIME')),
            software_version=header.get('CREATOR', ''),
            field_name=header.get('FIELD', ''),
            iso=header.get('ISO'),
            ra=header.get('CRVAL1'),
            dec=header.get('CRVAL2'),
            camera_id=path_info.camera_id,
            camera_serial_number=str(header.get('CAMSN')),
            lens_serial_number=header.get('INTSN'),
        )

        measured_rggb = header.get('MEASRGGB', '0 0 0 0').split(' ')
        if 'DATE' in header:
            file_date = parse_date(header.get('DATE')).replace(tzinfo=UTC)
        else:
            file_date = path_info.image_time.to_datetime(timezone=UTC)
        camera_date = parse_date(header.get('DATE-OBS', path_info.image_time)).replace(tzinfo=UTC)

        image_info = dict(
            uid=path_info.get_full_id(sep='_'),
            airmass=header.get('AIRMASS'),
            camera=dict(
                dateobs=camera_date,
                blue_balance=float(header.get('BLUEBAL')),
                circconf=float(header.get('CIRCCONF', '0.').split(' ')[0]),
                colortemp=float(header.get('COLORTMP')),
                measured_ev=float(header.get('MEASEV')),
                measured_ev2=float(header.get('MEASEV2')),
                measured_r=float(measured_rggb[0]),
                measured_g1=float(measured_rggb[1]),
                measured_g2=float(measured_rggb[2]),
                measured_b=float(measured_rggb[3]),
                red_balance=float(header.get('REDBAL')),
                temperature=float(header.get('CAMTEMP', 0).split(' ')[0]),
                white_lvln=header.get('WHTLVLN'),
                white_lvls=header.get('WHTLVLS'),
            ),
            exptime=float(header.get('EXPTIME')),
            file_creation_date=file_date,
            moonfrac=float(header.get('MOONFRAC')),
            moonsep=float(header.get('MOONSEP')),
            mount_dec=header.get('DEC-MNT'),
            mount_ha=header.get('HA-MNT'),
            mount_ra=header.get('RA-MNT'),
            time=path_info.image_time.to_datetime(timezone=UTC),
        )

        metadata = dict(
            unit=unit_info,
            sequence=sequence_info,
            image=image_info,
        )

    except Exception as e:
        raise error.PanError(f'Error in extracting metadata: {e!r}')

    logger.success('Metadata extracted from header')
    return metadata


def getdata(fn, *args, **kwargs):
    """Get the FITS data.

    Small wrapper around `astropy.io.fits.getdata` to auto-determine
    the FITS extension. This will return the data associated with the
    image.

    >>> fits_fn = getfixture('solved_fits_file')
    >>> d0 = getdata(fits_fn)
    >>> d0
    array([[2215, 2169, 2200, ..., 2169, 2235, 2168],
           [2123, 2191, 2133, ..., 2212, 2127, 2217],
           [2208, 2154, 2209, ..., 2159, 2233, 2187],
           ...,
           [2120, 2201, 2120, ..., 2209, 2126, 2195],
           [2219, 2151, 2199, ..., 2173, 2214, 2166],
           [2114, 2194, 2122, ..., 2202, 2125, 2204]],
          shape=(700, 700), dtype=uint16)
    >>> d1, h1 = getdata(fits_fn, header=True)
    >>> bool((d0 == d1).all())
    True
    >>> h1['FIELD']
    'KIC 8462852'

    Args:
        fn (str): Path to FITS file.
        *args: Passed to `astropy.io.fits.getdata`.
        **kwargs: Passed to `astropy.io.fits.getdata`.

    Returns:
        `np.ndarray`: The FITS data.
    """
    return fits.getdata(fn, *args, **kwargs)


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


def getwcs(fn, *args, **kwargs):
    """Get the WCS for the FITS file.

    Small wrapper around `astropy.wcs.WCS`.

    >>> from panoptes.utils.images import fits as fits_utils
    >>> fits_fn = getfixture('solved_fits_file')
    >>> wcs = fits_utils.getwcs(fits_fn)
    >>> wcs.is_celestial
    True
    >>> fits_fn = getfixture('unsolved_fits_file')
    >>> wcs = fits_utils.getwcs(fits_fn)
    >>> wcs.is_celestial
    False

    Args:
        fn (str): Path to FITS file.
        *args: Passed to `astropy.io.fits.getheader`.
        **kwargs: Passed to `astropy.io.fits.getheader`.

    Returns:
        `astropy.wcs.WCS`: The World Coordinate System information.
    """
    return WCS(getheader(fn, *args, **kwargs), *args, **kwargs)


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


def fits_to_jpg(fname=None,
                title=None,
                figsize=(10, 10 / 1.325),
                dpi=150,
                alpha=0.2,
                number_ticks=7,
                clip_percent=99.9,
                **kwargs):
    data = mask_saturated(getdata(fname))
    header = getheader(fname)
    wcs = WCS(header)

    if not title:
        field = header.get('FIELD', 'Unknown field')
        exptime = header.get('EXPTIME', 'Unknown exptime')
        filter_type = header.get('FILTER', 'Unknown filter')

        try:
            date_time = header['DATE-OBS']
        except KeyError:
            # If we don't have DATE-OBS, check filename for date.
            basename = os.path.splitext(os.path.basename(fname))[0]
            date_time = parse_date(basename).isoformat()

        date_time = date_time.replace('T', ' ', 1)

        title = f'{field} ({exptime}s {filter_type}) {date_time}'

    norm = ImageNormalize(interval=PercentileInterval(clip_percent), stretch=LogStretch())

    fig = Figure()
    FigureCanvas(fig)
    fig.set_size_inches(*figsize)
    fig.dpi = dpi

    if wcs.is_celestial:
        ax = fig.add_subplot(1, 1, 1, projection=wcs)
        ax.coords.grid(True, color='white', ls='-', alpha=alpha)

        ra_axis = ax.coords['ra']
        ra_axis.set_axislabel('Right Ascension')
        ra_axis.set_major_formatter('hh:mm')
        ra_axis.set_ticks(number=number_ticks, color='white')
        ra_axis.set_ticklabel(color='white', exclude_overlapping=True)

        dec_axis = ax.coords['dec']
        dec_axis.set_axislabel('Declination')
        dec_axis.set_major_formatter('dd:mm')
        dec_axis.set_ticks(number=number_ticks, color='white')
        dec_axis.set_ticklabel(color='white', exclude_overlapping=True)
    else:
        ax = fig.add_subplot(111)
        ax.grid(True, color='white', ls='-', alpha=alpha)

        ax.set_xlabel('X / pixels')
        ax.set_ylabel('Y / pixels')

    im = ax.imshow(data, norm=norm, cmap=get_palette(), origin='lower')
    add_colorbar(im)
    fig.suptitle(title)

    new_filename = re.sub(r'.fits(.fz)?', '.jpg', fname)
    fig.savefig(new_filename, bbox_inches='tight')

    # explicitly close and delete figure
    fig.clf()
    del fig

    return new_filename
