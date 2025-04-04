import os
import shutil
import subprocess
from json import loads
from pathlib import Path
from typing import Union, Optional
from warnings import warn

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from astropy.io import fits
from dateutil.parser import parse as date_parse
from loguru import logger

from panoptes.utils import error
from panoptes.utils.images import fits as fits_utils


def cr2_to_fits(
        cr2_fname: Union[str, Path],
        fits_fname: str = None,
        overwrite: bool = False,
        headers: dict = None,
        fits_headers: dict = None,
        remove_cr2: bool = False,
        **kwargs) -> Union[Path, None]:  # pragma: no cover
    """Convert a CR2 file to FITS.

    This is a convenience function that first converts the CR2 to PGM via ~cr2_to_pgm.
    Also adds keyword headers to the FITS file.

    Note:
        The intermediate PGM file is automatically removed

    Arguments:
        cr2_fname (str): Name of the CR2 file to be converted.
        fits_fname (str, optional): Name of the FITS file to output. Default is `None`, in which
            case the `cr2_fname` is used as the base.
        overwrite (bool, optional): Overwrite existing FITS, default False.
        headers (dict, optional): Header data added to the FITS file.
        fits_headers (dict, optional): Header data added to the FITS file without filtering.
        remove_cr2 (bool, optional): If CR2 should be removed after processing, default False.
        **kwargs: Description

    Returns:
        str: The full path to the generated FITS file.

    """
    if fits_headers is None:
        fits_headers = {}
    if headers is None:
        headers = {}

    # Convert path to just a str.
    if isinstance(cr2_fname, Path):
        cr2_fname = str(cr2_fname)

    if isinstance(fits_fname, Path):
        fits_fname = str(fits_fname)

    if fits_fname is None:
        fits_fname = cr2_fname.replace('.cr2', '.fits')

    if not os.path.exists(fits_fname) or overwrite:
        logger.debug(f'Converting CR2 to PGM: {cr2_fname}')

        # Convert the CR2 to a PGM file then delete PGM
        try:
            pgm = read_pgm(cr2_to_pgm(cr2_fname), remove_after=True)
        except error.InvalidSystemCommand:
            logger.warning(f'No dcraw on the system, cannot proceed.')
            return None

        # Add the EXIF information from the CR2 file
        exif = read_exif(cr2_fname)

        # Set the PGM as the primary data for the FITS file
        hdu = fits.PrimaryHDU(pgm)

        obs_date = date_parse(exif.get('DateTimeOriginal', '').replace(':', '-', 2)).isoformat()

        # Set some default headers
        hdu.header.set('FILTER', 'RGGB')
        hdu.header.set('ISO', exif.get('ISO', ''))
        hdu.header.set('EXPTIME', exif.get('ExposureTime', 'Seconds'))
        hdu.header.set('CAMTEMP', exif.get('CameraTemperature', ''), 'Celsius - From CR2')
        hdu.header.set('CIRCCONF', exif.get('CircleOfConfusion', ''), 'From CR2')
        hdu.header.set('COLORTMP', exif.get('ColorTempMeasured', ''), 'From CR2')
        hdu.header.set('FILENAME', exif.get('FileName', ''), 'From CR2')
        hdu.header.set('INTSN', exif.get('InternalSerialNumber', ''), 'From CR2')
        hdu.header.set('CAMSN', exif.get('SerialNumber', ''), 'From CR2')
        hdu.header.set('MEASEV', exif.get('MeasuredEV', ''), 'From CR2')
        hdu.header.set('MEASEV2', exif.get('MeasuredEV2', ''), 'From CR2')
        hdu.header.set('MEASRGGB', exif.get('MeasuredRGGB', ''), 'From CR2')
        hdu.header.set('WHTLVLN', exif.get('NormalWhiteLevel', ''), 'From CR2')
        hdu.header.set('WHTLVLS', exif.get('SpecularWhiteLevel', ''), 'From CR2')
        hdu.header.set('REDBAL', exif.get('RedBalance', ''), 'From CR2')
        hdu.header.set('BLUEBAL', exif.get('BlueBalance', ''), 'From CR2')
        hdu.header.set('WBRGGB', exif.get('WB RGGBLevelAsShot', ''), 'From CR2')
        hdu.header.set('DATE-OBS', obs_date)

        for key, value in fits_headers.items():
            try:
                hdu.header.set(key.upper()[0: 8], value)
            except Exception:
                pass

        try:
            logger.debug(f'Saving fits file to: {fits_fname}')

            hdu.writeto(fits_fname, output_verify='silentfix', overwrite=overwrite)
        except Exception as e:
            warn(f'Problem writing FITS file: {e}')
        else:
            if remove_cr2:
                os.unlink(cr2_fname)

        fits_utils.update_observation_headers(fits_fname, headers)

    return Path(fits_fname)


def cr2_to_pgm(
        cr2_fname,
        pgm_fname=None,
        overwrite=True, *args,
        **kwargs):  # pragma: no cover
    """ Convert CR2 file to PGM

    Converts a raw Canon CR2 file to a netpbm PGM file via `dcraw`. Assumes
    `dcraw` is installed on the system

    Note:
        This is a blocking call

    Arguments:
        cr2_fname {str} -- Name of CR2 file to convert
        **kwargs {dict} -- Additional keywords to pass to script

    Keyword Arguments:
        pgm_fname {str} -- Name of PGM file to output, if None (default) then
                           use same name as CR2 (default: {None})
        dcraw {str} -- Path to installed `dcraw` (default: {'dcraw'})
        overwrite {bool} -- A bool indicating if existing PGM should be overwritten
                         (default: {True})

    Returns:
        str -- Filename of PGM that was created

    """
    dcraw = shutil.which('dcraw')
    if dcraw is None:
        raise error.InvalidCommand('dcraw not found')

    if pgm_fname is None:
        pgm_fname = cr2_fname.replace('.cr2', '.pgm')

    if os.path.exists(pgm_fname) and not overwrite:
        logger.warning(f'PGM file exists, returning existing file: {pgm_fname}')
    else:
        try:
            # Build the command for this file
            command = f'{dcraw} -t 0 -D -4 {cr2_fname}'
            cmd_list = command.split()
            logger.debug(f'PGM Conversion command: \n {cmd_list}')

            # Run the command
            if subprocess.check_call(cmd_list) == 0:
                logger.debug('PGM Conversion command successful')

        except subprocess.CalledProcessError as err:
            raise error.InvalidSystemCommand(msg=f"File: {cr2_fname} \n err: {err}")

    return pgm_fname


def read_exif(fname, exiftool='exiftool'):  # pragma: no cover
    """ Read the EXIF information

    Gets the EXIF information using exiftool

    Note:
        Assumes the `exiftool` is installed

    Args:
        fname {str} -- Name of file (CR2) to read

    Keyword Args:
        exiftool {str} -- Location of exiftool (default: {'/usr/bin/exiftool'})

    Returns:
        dict -- Dictionary of EXIF information

    """
    assert os.path.exists(fname), warn(f"File does not exist: {fname}")
    exif = {}

    try:
        # Build the command for this file
        command = f'{exiftool} -j {fname}'
        cmd_list = command.split()

        # Run the command
        exif = loads(subprocess.check_output(cmd_list).decode('utf-8'))
    except subprocess.CalledProcessError as err:
        raise error.InvalidSystemCommand(msg=f"File: {fname} \n err: {err}")

    return exif[0]


def read_pgm(fname, byteorder='>', remove_after=False):  # pragma: no cover
    """Return image data from a raw PGM file as numpy array.

    Note:
        Format Spec: http://netpbm.sourceforge.net/doc/pgm.html
        Source: http://stackoverflow.com/questions/7368739/numpy-and-16-bit-pgm

    Note:
        This is correctly processed as a Big endian even though the CR2 itself
        marks it as a Little endian. See the notes in Source page above as well
        as the comment about significant bit in the Format Spec

    Args:
        fname(str):         Filename of PGM to be converted
        byteorder(str):     Big endian
        remove_after(bool): Delete fname file after reading, defaults to False.
        overwrite(bool):      overwrite existing PGM or not, defaults to True

    Returns:
        numpy.array:        The raw data from the PGMx

    """

    with open(fname, 'rb') as f:
        buffer = f.read()

    # We know our header info is 19 chars long
    header_offset = 19

    img_type, img_size, img_max_value, _ = buffer[
                                           0:header_offset].decode().split('\n')

    assert img_type == 'P5', warn("Not a PGM file")

    # Get the width and height (as strings)
    width, height = img_size.split(' ')

    data = np.flipud(np.frombuffer(buffer[header_offset:],
                                   dtype=byteorder + 'u2',
                                   ).reshape((int(height), int(width))))

    if remove_after:
        os.remove(fname)

    return data


def cr2_to_jpg(
        cr2_fname: Path,
        jpg_fname: str = None,
        title: str = '',
        overwrite: bool = False,
        remove_cr2: bool = False,
) -> Optional[Path]:
    """Extract a JPG image from a CR2, return the new path name."""
    exiftool = shutil.which('exiftool')
    if not exiftool:  # pragma: no cover
        raise error.InvalidSystemCommand('exiftool not found')

    jpg_fname = Path(jpg_fname) if jpg_fname else cr2_fname.with_suffix('.jpg')

    if jpg_fname.exists() and overwrite is False:
        raise error.AlreadyExists(f'{jpg_fname} already exists and overwrite is False')

    cmd = [exiftool, '-b', '-PreviewImage', cr2_fname.as_posix()]
    comp_proc = subprocess.run(cmd, check=True, stdout=jpg_fname.open('wb'))

    if comp_proc.returncode != 0:  # pragma: no cover
        raise error.InvalidSystemCommand(f'{comp_proc.returncode}')

    if title and title > '':
        try:
            im = Image.open(jpg_fname)
            id = ImageDraw.Draw(im)

            im.info['title'] = title

            try:
                fnt = ImageFont.truetype('FreeMono.ttf', 120)
            except Exception:  # pragma: no cover
                fnt = ImageFont.load_default()
            bottom_padding = 25
            position = (im.size[0] / 2, im.size[1] - bottom_padding)
            id.text(position, title, font=fnt, fill=(255, 0, 0), anchor='ms')

            logger.debug(f'Adding title={title} to {jpg_fname.as_posix()}')
            im.save(jpg_fname)
        except Exception:
            raise error.InvalidSystemCommand(f'Error adding title to {jpg_fname.as_posix()}')

    if remove_cr2:
        logger.debug(f'Removing {cr2_fname}')
        cr2_fname.unlink()

    return jpg_fname
