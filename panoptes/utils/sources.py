from .logger import logger

import os
import shutil
import subprocess

from warnings import warn

from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

from astropy.table import Table
from astropy.wcs import WCS
from astropy import units as u
from astropy.coordinates import SkyCoord, match_coordinates_sky

from .images import fits as fits_utils


# Storage
try:
    bigquery_client = bigquery.Client()
except DefaultCredentialsError:
    warn("Can't load Google credentials, catalog matching will not be available. "
         "Set GOOGLE_APPLICATION_CREDENTIALS to use sources module.")


def get_stars_from_footprint(wcs_or_footprint, **kwargs):
    """Lookup star information from WCS footprint.

    Generates the correct layout for an SQL `POLYGON` that can be passed to
    `get_stars`.

    Args:
        wcs_or_footprint (`astropy.wcs.WCS` or array): Either the WCS or the output from `calc_footprint`.
        **kwargs: Optional keywords to pass to `get_stars`.

    """
    if isinstance(wcs_or_footprint, WCS):
        wcs_footprint = wcs_or_footprint.calc_footprint()
    else:
        wcs_footprint = wcs_or_footprint

    wcs_footprint = list(wcs_footprint)
    # Add the first entry to the end to complete polygon
    wcs_footprint.append(wcs_footprint[0])

    poly = ','.join([f'{c[0]:.05} {c[1]:.05f}' for c in wcs_footprint])

    return get_stars(shape=poly, **kwargs)


def get_stars(
        bq_client=None,
        shape=None,
        vmag_min=6,
        vmag_max=15,
        client=None,
        **kwargs):
    """Look star information from the TESS catalog.

    Todo:

        Add support for `ra_min`, `ra_max`, etc.

    Args:
        bq_client (TYPE): The BigQuery Client connection.
        shape (str, optional): A string representation of an SQL shape, e.g. `POLYGON`.
        vmag_min (int, optional): Description
        vmag_max (int, optional): Description
        client (None, optional): Description
        **kwargs: Description

    Returns:
        `pandas.DataFrame`: Dataframe containing the results.

    """
    if shape is not None:
        sql_constraint = f"AND ST_CONTAINS(ST_GEOGFROMTEXT('POLYGON(({shape}))'), coords)"

    sql = f"""
    SELECT
        id as picid, twomass, gaia,
        ra as catalog_ra,
        dec as catalog_dec,
        vmag as catalog_vmag,
        e_vmag as catalog_vmag_err
    FROM catalog.pic
    WHERE
      vmag_partition BETWEEN {vmag_min} AND {vmag_max}
      {sql_constraint}
    """

    if bq_client is None:
        bq_client = bigquery_client

    try:
        df = bq_client.query(sql).to_dataframe()
        logger.debug(f'Found {len(df)} in Vmag=[{vmag_min}, {vmag_max+1}) and bounds=[{shape}]')

    except Exception as e:
        logger.warning(e)
        df = None

    return df


def lookup_point_sources(fits_file,
                         catalog_match=False,
                         method='sextractor',
                         force_new=False,
                         return_unmatched=False,
                         max_separation_arcsec=None,  # arcsecs
                         **kwargs
                         ):
    """ Extract point sources from image.

    This function will extract the sources from the image using the given method
    (currently only `sextractor`). This is returned as a `pandas.DataFrame`. If
    `catalog_match=True` then the resulting sources will be matched against the
    PANOPTES catalog, which is a filtered version of the TESS Input Catalog.

    >>> from panoptes.utils.sources import lookup_point_sources
    >>> fits_fn = getfixture('solved_fits_file')

    >>> point_sources = lookup_point_sources(fits_fn)
    >>> point_sources.describe()
                   ra         dec           x  ...      flux_max  fwhm_image       flags
    count  726.000000  726.000000  726.000000  ...    726.000000  726.000000  726.000000
    mean   303.259396   46.023160  353.399449  ...   2215.879774    3.248939    0.819559
    std      0.820234    0.574604  200.200817  ...   2748.420911    2.209067    2.880939
    min    301.794797   45.038730   11.000000  ...    307.825100  -27.170000    0.000000
    25%    302.546731   45.539239  183.250000  ...    673.398775    2.280000    0.000000
    50%    303.238772   46.015271  350.000000  ...   1018.907000    2.915000    0.000000
    75%    303.932212   46.533257  530.000000  ...   2318.909000    3.795000    0.000000
    max    304.648913   47.018996  700.000000  ...  11640.210000   24.970000   27.000000
    ...
    >>> type(point_sources)
    <class 'pandas.core.frame.DataFrame'>

    Args:
        fits_file (str, optional): Path to FITS file to search for stars.
        force_new (bool, optional): Force a new catalog to be created,
            defaults to False.

    Raises:
        error.InvalidSystemCommand: Description
    """
    if catalog_match or method == 'tess_catalog':
        fits_header = fits_utils.getheader(fits_file)
        wcs = WCS(fits_header)
        assert wcs is not None and wcs.is_celestial, logger.warning("Need a valid WCS")

    logger.debug(f"Looking up sources for {fits_file}")

    lookup_function = {
        'sextractor': _lookup_via_sextractor,
    }

    # Lookup our appropriate method and call it with the fits file and kwargs
    try:
        logger.debug(f"Using {method} method for {fits_file}")
        point_sources = lookup_function[method](fits_file, force_new=force_new, **kwargs)
    except Exception as e:
        logger.debug(f"Problem looking up sources: {e!r} {fits_file}")
        raise Exception(f"Problem looking up sources: {e!r} {fits_file}")

    if catalog_match:
        logger.debug(f'Doing catalog match against stars {fits_file}')
        try:
            point_sources = get_catalog_match(point_sources,
                                              wcs,
                                              return_unmatched=return_unmatched,
                                              **kwargs)
            logger.debug(f'Done with catalog match {fits_file}')
        except Exception as e:
            logger.error(f'Error in catalog match: {e!r} {fits_file}')
        else:
            # Remove catalog matches that are too far away.
            if max_separation_arcsec is not None:
                logger.debug(f'Removing matches > {max_separation_arcsec} arcsec from catalog.')
                point_sources = point_sources.query('catalog_sep_arcsec <= @max_separation_arcsec')

    logger.debug(f'Point sources: {len(point_sources)} {fits_file}')

    return point_sources


def get_catalog_match(point_sources, wcs, return_unmatched=False, origin=1, **kwargs):
    assert point_sources is not None

    logger.debug(f'Getting catalog stars')

    # Get coords from detected point sources
    stars_coords = SkyCoord(
        ra=point_sources['sextractor_ra'].values * u.deg,
        dec=point_sources['sextractor_dec'].values * u.deg
    )

    # Lookup stars in catalog
    catalog_stars = get_stars_from_footprint(
        wcs.calc_footprint(),
        **kwargs
    )
    if catalog_stars is None:
        logger.debug('No catalog matches, returning table without ids')
        return point_sources

    # Get coords for catalog stars
    catalog_coords = SkyCoord(
        ra=catalog_stars['catalog_ra'] * u.deg,
        dec=catalog_stars['catalog_dec'] * u.deg
    )

    # Do catalog matching
    logger.debug(f'Matching catalog')
    idx, d2d, d3d = match_coordinates_sky(stars_coords, catalog_coords)
    logger.debug(f'Got {len(idx)} matched sources (includes duplicates)')

    # Add the matches and their separation.
    matches = catalog_stars.iloc[idx]
    point_sources = point_sources.join(matches.reset_index(drop=True))
    point_sources['catalog_sep_arcsec'] = d2d.to(u.arcsec).value

    # Get the xy pixel coordinates for all sources according to WCS.
    xs, ys = wcs.all_world2pix(point_sources.sextractor_ra,
                               point_sources.sextractor_dec,
                               origin,
                               ra_dec_order=True)
    point_sources['catalog_x'] = xs
    point_sources['catalog_y'] = ys

    point_sources.eval('catalog_sextractor_diff_x = catalog_x - sextractor_x_image', inplace=True)
    point_sources.eval('catalog_sextractor_diff_y = catalog_y - sextractor_y_image', inplace=True)

    ra_diff_arcsec = ((point_sources.catalog_ra - point_sources.sextractor_ra).values * u.degree).to(u.arcsec)
    dec_diff_arcsec = ((point_sources.catalog_dec - point_sources.sextractor_dec).values * u.degree).to(u.arcsec)

    point_sources['catalog_sextractor_diff_arcsec_ra'] = ra_diff_arcsec
    point_sources['catalog_sextractor_diff_arcsec_dec'] = dec_diff_arcsec

    # Sources that didn't match
    if return_unmatched:
        unmatched = catalog_stars.iloc[catalog_stars.index.difference(idx)].copy()

        # Get the xy pixel coordinates for all sources according to WCS.
        xs, ys = wcs.all_world2pix(unmatched.catalog_ra,
                                   unmatched.catalog_dec,
                                   origin,
                                   ra_dec_order=True)
        unmatched['catalog_x'] = xs
        unmatched['catalog_y'] = ys

        return point_sources.append(unmatched)

    return point_sources


def _lookup_via_sextractor(fits_file,
                           sextractor_params=None,
                           trim_size=10,
                           *args, **kwargs):

    # Write the sextractor catalog to a file
    base_dir = os.path.dirname(fits_file)
    source_dir = os.path.join(base_dir, 'sextractor')
    os.makedirs(source_dir, exist_ok=True)

    img_id = os.path.splitext(os.path.basename(fits_file))[0]

    source_file = os.path.join(source_dir, f'point_sources_{img_id}.cat')

    # sextractor can't handle compressed data
    if fits_file.endswith('.fz'):
        fits_file = fits_utils.funpack(fits_file)

    logger.debug("Point source catalog: {}".format(source_file))

    if not os.path.exists(source_file) or kwargs.get('force_new', False):
        logger.debug("No catalog found, building from sextractor")
        # Build catalog of point sources
        sextractor = shutil.which('sextractor')
        if sextractor is None:
            sextractor = shutil.which('sex')
            if sextractor is None:
                raise Exception('sextractor not found')

        if sextractor_params is None:
            resources_dir = os.path.expandvars('$PANDIR/panoptes-utils/resources/sextractor')
            sextractor_params = [
                '-c', os.path.join(resources_dir, 'panoptes.sex'),
                '-CATALOG_NAME', source_file,
            ]

        logger.debug("Running sextractor...")
        cmd = [sextractor, *sextractor_params, fits_file]
        logger.debug(cmd)

        try:
            subprocess.run(cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           timeout=60,
                           check=True)
        except subprocess.CalledProcessError as e:
            raise Exception("Problem running sextractor: {}".format(e))

    # Read catalog
    logger.debug(f'Building detected source table with {source_file}')
    point_sources = Table.read(source_file, format='ascii.sextractor')

    # Remove the point sources that sextractor has flagged
    # if 'FLAGS' in point_sources.keys():
    #    point_sources = point_sources[point_sources['FLAGS'] == 0]
    #    point_sources.remove_columns(['FLAGS'])

    # Rename columns
    point_sources.rename_column('XPEAK_IMAGE', 'x')
    point_sources.rename_column('YPEAK_IMAGE', 'y')

    # Filter point sources near edge
    # w, h = data[0].shape
    w, h = (3476, 5208)

    logger.debug('Trimming sources near edge')
    top = point_sources['y'] > trim_size
    bottom = point_sources['y'] < w - trim_size
    left = point_sources['x'] > trim_size
    right = point_sources['x'] < h - trim_size

    point_sources = point_sources[top & bottom & right & left].to_pandas()
    point_sources.columns = [
        'sextractor_ra',
        'sextractor_dec',
        'sextractor_x',
        'sextractor_y',
        'sextractor_x_image',
        'sextractor_y_image',
        'sextractor_ellipticity',
        'sextractor_theta_image',
        'sextractor_flux_best',
        'sextractor_fluxerr_best',
        'sextractor_mag_best',
        'sextractor_magerr_best',
        'sextractor_flux_max',
        'sextractor_fwhm_image',
        'sextractor_flags',
    ]

    logger.debug(f'Returning {len(point_sources)} sources from sextractor')
    return point_sources
