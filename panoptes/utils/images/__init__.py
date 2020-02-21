import os
import subprocess
import shutil
from contextlib import suppress

from warnings import warn

from matplotlib import cm as colormap
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from astropy.wcs import WCS
from astropy.nddata import Cutout2D
from astropy.io.fits import open as open_fits
from astropy.visualization import (PercentileInterval, LogStretch, ImageNormalize)

from copy import copy
from dateutil import parser as date_parser

from panoptes.utils import current_time
from panoptes.utils import error
from panoptes.utils.images import focus as focus_utils
from panoptes.utils.images.plot import add_colorbar

palette = copy(colormap.inferno)
palette.set_over('w', 1.0)
palette.set_under('k', 1.0)
palette.set_bad('g', 1.0)


def make_images_dir():
    """Return the path of the PANDIR/images directory, creating it if necessary."""
    images_dir = os.path.join(os.getenv('PANDIR'), 'images')
    try:
        os.makedirs(images_dir, exist_ok=True)
        return images_dir
    except Exception as e:
        warn(f'Unable to create the images directory: {images_dir}')
        warn(f'Exception during os.makedirs: {e}')
        return None


def crop_data(data, box_width=200, center=None, verbose=False, data_only=True, wcs=None):
    """Return a cropped portion of the image

    Shape is a box centered around the middle of the data

    Args:
        data (`numpy.array`): Array of data.
        box_width (int, optional): Size of box width in pixels, defaults to 200px.
        center (tuple(int, int), optional): Crop around set of coords, default to image center.
        verbose (bool, optional): Print extra text output.
        data_only (bool, optional): If True (default), return only data. If False
            return the `Cutout2D` object.
        wcs (None|`astropy.wcs.WCS`, optional): A valid World Coordinate System (WCS) that will
            be cropped along with the data if provided.

    Returns:
        np.array: A clipped (thumbnailed) version of the data if `data_only=True`, otherwise
            a `astropy.nddata.Cutout2D` object.

    """
    assert data.shape[0] >= box_width, "Can't clip data, it's smaller than {} ({})".format(
        box_width, data.shape)
    # Get the center
    if verbose:
        print("Data to crop: {}".format(data.shape))

    if center is None:
        x_len, y_len = data.shape
        x_center = int(x_len / 2)
        y_center = int(y_len / 2)
    else:
        y_center = int(center[0])
        x_center = int(center[1])

    if verbose:
        print("Using center: {} {}".format(x_center, y_center))
        print("Box width: {}".format(box_width))

    cutout = Cutout2D(data, (y_center, x_center), box_width, wcs=wcs)

    if data_only:
        return cutout.data

    return cutout


def make_pretty_image(fname, title=None, timeout=15, img_type=None, link_latest=False, **kwargs):
    """Make a pretty image.

    This will create a jpg file from either a CR2 (Canon) or FITS file.

    Notes:
        See `/scripts/cr2_to_jpg.sh` for CR2 process.

    Arguments:
        fname {str} -- Name of image file, may be either .fits or .cr2
        title (None|str, optional): Title to be placed on image, default None.
        timeout (int, optional): Timeout for conversion, default 15 seconds.
        img_type (None|str, optional): Image type of fname, one of '.cr2' or '.fits'.
            The default is `None`, in which case the file extension of fname is used.
        link_latest (bool, optional): If the pretty picture should be linked to
            `$PANDIR/images/latest.jpg`, default False.
        **kwargs {dict} -- Additional arguments to be passed to external script.

    Returns:
        str -- Filename of image that was created.
    """
    if img_type is None:
        img_type = os.path.splitext(fname)[-1]

    if not os.path.exists(fname):
        warn("File doesn't exist, can't make pretty: {}".format(fname))
        return None
    elif img_type == '.cr2':
        pretty_path = _make_pretty_from_cr2(fname, title=title, timeout=timeout, **kwargs)
    elif img_type == '.fits':
        pretty_path = _make_pretty_from_fits(fname, title=title, **kwargs)
    else:
        warn("File must be a Canon CR2 or FITS file.")
        return None

    if not link_latest or not os.path.exists(pretty_path):
        return pretty_path

    # Symlink latest.jpg to the image; first remove the symlink if it already exists.
    images_dir = make_images_dir()
    if not images_dir:
        warn(f"Can't link latest.jpg to {pretty_path}")
    else:
        latest_path = os.path.join(images_dir, 'latest.jpg')
        with suppress(FileNotFoundError):
            os.remove(latest_path)
        try:
            os.symlink(pretty_path, latest_path)
        except Exception as e:
            warn("Can't link latest image: {}".format(e))

    return pretty_path


def _make_pretty_from_fits(fname=None,
                           title=None,
                           figsize=(10, 10 / 1.325),
                           dpi=150,
                           alpha=0.2,
                           number_ticks=7,
                           clip_percent=99.9,
                           **kwargs):

    with open_fits(fname) as hdu:
        header = hdu[0].header
        data = hdu[0].data
        data = focus_utils.mask_saturated(data)
        wcs = WCS(header)

    if not title:
        field = header.get('FIELD', 'Unknown field')
        exptime = header.get('EXPTIME', 'Unknown exptime')
        filter_type = header.get('FILTER', 'Unknown filter')

        try:
            date_time = header['DATE-OBS']
        except KeyError:
            # If we don't have DATE-OBS, check filename for date
            try:
                basename = os.path.splitext(os.path.basename(fname))[0]
                date_time = date_parser.parse(basename).isoformat()
            except Exception:
                # Otherwise use now
                date_time = current_time(pretty=True)

        date_time = date_time.replace('T', ' ', 1)

        title = '{} ({}s {}) {}'.format(field, exptime, filter_type, date_time)

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
        ra_axis.set_ticks(
            number=number_ticks,
            color='white',
            exclude_overlapping=True
        )

        dec_axis = ax.coords['dec']
        dec_axis.set_axislabel('Declination')
        dec_axis.set_major_formatter('dd:mm')
        dec_axis.set_ticks(
            number=number_ticks,
            color='white',
            exclude_overlapping=True
        )
    else:
        ax = fig.add_subplot(111)
        ax.grid(True, color='white', ls='-', alpha=alpha)

        ax.set_xlabel('X / pixels')
        ax.set_ylabel('Y / pixels')

    im = ax.imshow(data, norm=norm, cmap=palette, origin='lower')
    add_colorbar(im)
    fig.suptitle(title)

    new_filename = fname.replace('.fits', '.jpg')
    fig.savefig(new_filename, bbox_inches='tight')

    # explicitly close and delete figure
    fig.clf()
    del fig

    return new_filename


def _make_pretty_from_cr2(fname, title=None, timeout=15, **kwargs):
    verbose = kwargs.get('verbose', False)

    script_name = shutil.which('cr2-to-jpg')
    cmd = [script_name, fname]

    if title:
        cmd.append(title)

    if verbose:
        print(cmd)

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        if verbose:
            print(output)
    except Exception as e:
        raise error.InvalidCommand(f"Error executing {script_name}: {e.output!r}\nCommand: {cmd}")

    return fname.replace('cr2', 'jpg')


def make_timelapse(
        directory,
        fn_out=None,
        glob_pattern='20[1-9][0-9]*T[0-9]*.jpg',
        overwrite=False,
        timeout=60,
        verbose=False,
        **kwargs):
    """Create a timelapse.

    A timelapse is created from all the images in a given `directory`

    Args:
        directory (str): Directory containing image files
        fn_out (str, optional): Full path to output file name, if not provided,
            defaults to `directory` basename.
        glob_pattern (str, optional): A glob file pattern of images to include,
            default '20[1-9][0-9]*T[0-9]*.jpg', which corresponds to the observation
            images but excludes any pointing images. The pattern should be relative
            to the local directory.
        overwrite (bool, optional): Overwrite timelapse if exists, default False.
        timeout (int): Timeout for making movie, default 60 seconds.
        verbose (bool, optional): Show output, default False.
        **kwargs (dict): Valid keywords: verbose

    Returns:
        str: Name of output file

    Raises:
        error.InvalidSystemCommand: Raised if ffmpeg command is not found.
        FileExistsError: Raised if fn_out already exists and overwrite=False.
    """
    if fn_out is None:
        head, tail = os.path.split(directory)
        if tail == '':
            head, tail = os.path.split(head)

        field_name = head.split('/')[-2]
        cam_name = head.split('/')[-1]
        fname = '{}_{}_{}.mp4'.format(field_name, cam_name, tail)
        fn_out = os.path.normpath(os.path.join(directory, fname))

    if verbose:
        print("Timelapse file: {}".format(fn_out))

    if os.path.exists(fn_out) and not overwrite:
        raise FileExistsError("Timelapse exists. Set overwrite=True if needed")

    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        raise error.InvalidSystemCommand("ffmpeg not found, can't make timelapse")

    inputs_glob = os.path.join(directory, glob_pattern)

    try:
        ffmpeg_cmd = [
            ffmpeg,
            '-r', '3',
            '-pattern_type', 'glob',
            '-i', inputs_glob,
            '-s', 'hd1080',
            '-vcodec', 'libx264',
        ]

        if overwrite:
            ffmpeg_cmd.append('-y')

        ffmpeg_cmd.append(fn_out)

        if verbose:
            print(ffmpeg_cmd)

        proc = subprocess.Popen(ffmpeg_cmd, universal_newlines=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            # Don't wait forever
            outs, errs = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
        finally:
            if verbose:
                print(outs)
                print(errs)

            # Double-check for file existence
            if not os.path.exists(fn_out):
                fn_out = None
    except Exception as e:
        warn("Problem creating timelapse in {}: {!r}".format(fn_out, e))
        fn_out = None

    return fn_out
