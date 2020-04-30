import os
import shutil
import subprocess

from google.cloud import bigquery
from google.auth.credentials import AnonymousCredentials

from astropy.table import Table
from astropy.wcs import WCS
from astropy import units as u
from astropy.coordinates import SkyCoord, match_coordinates_sky

from .images import fits as fits_utils
from .logger import logger


def _get_bq_client(project_id='panoptes-exp', credentials=AnonymousCredentials()):
    logger.debug(f'Getting new bigquery client')

    bq_client = bigquery.Client(project=project_id, credentials=credentials)
    return bq_client


def get_stars_from_footprint(wcs_or_footprint, **kwargs):
    """Lookup star information from WCS footprint.

    Generates the correct layout for an SQL `POLYGON` that can be passed to
    `get_stars`.

    Args:
        wcs_or_footprint (`astropy.wcs.WCS` or array): Either the WCS or the output from `calc_footprint`.
        **kwargs: Optional keywords to pass to `get_stars`.

    """
    wcs = None
    if isinstance(wcs_or_footprint, WCS):
        wcs = wcs_or_footprint
        wcs_footprint = wcs_or_footprint.calc_footprint()
    else:
        wcs_footprint = wcs_or_footprint

    wcs_footprint = list(wcs_footprint)
    logger.debug(f'Looking up catalog stars for WCS: {wcs_or_footprint}')
    # Add the first entry to the end to complete polygon
    wcs_footprint.append(wcs_footprint[0])

    poly = ','.join([f'{c[0]:.05} {c[1]:.05f}' for c in wcs_footprint])

    catalog_stars = get_stars(shape=poly, **kwargs)

    # Get the XY positions via the WCS
    if wcs is not None:
        catalog_coords = catalog_stars[['catalog_ra', 'catalog_dec']]
        catalog_xy = wcs.all_world2pix(catalog_coords, 1)
        catalog_stars['x'] = catalog_xy.T[0]
        catalog_stars['y'] = catalog_xy.T[1]
        catalog_stars['x_int'] = catalog_stars.x.astype(int)
        catalog_stars['y_int'] = catalog_stars.y.astype(int)

    return catalog_stars


def get_stars(
        shape=None,
        vmag_min=4,
        vmag_max=17,
        bq_client=None,
        **kwargs):
    """Look star information from the TESS catalog.

    Args:
        shape (str, optional): A string representation of an SQL shape, e.g. `POLYGON`.
        vmag_min (int, optional): Minimum Vmag to include, default 4 inclusive.
        vmag_max (int, optional): Maximum Vmag to include, default 17 non-inclusive.
        bq_client (`google.cloud.bigquery.Client`): The BigQuery Client connection.
        **kwargs: Description

    Returns:
        `pandas.DataFrame`: Dataframe containing the results.

    """
    if shape is not None:
        sql_constraint = f"AND ST_CONTAINS(ST_GEOGFROMTEXT('POLYGON(({shape}))'), coords)"

    # Note that for how the BigQuery partition works, we need the parition one step
    # below the requested Vmag_max.
    sql = f"""
    SELECT
        id as picid, twomass, gaia,
        ra as catalog_ra,
        dec as catalog_dec,
        vmag as catalog_vmag,
        e_vmag as catalog_vmag_err
    FROM catalog.pic
    WHERE
      vmag_partition BETWEEN {vmag_min} AND {vmag_max - 1}
      {sql_constraint}
    """

    if bq_client is None:
        bq_client = _get_bq_client()

    try:
        df = bq_client.query(sql).to_dataframe()
        logger.debug(f'Found {len(df)} in Vmag=[{vmag_min}, {vmag_max}) and bounds=[{shape}]')

    except Exception as e:
        logger.warning(e)
        df = None

    return df


def lookup_point_sources(fits_file,
                         catalog_match=False,
                         method='sextractor',
                         force_new=False,
                         **kwargs
                         ):
    """Extract point sources from image.

    This function will extract the sources from the image using the given method
    (currently only `sextractor`). This is returned as a `pandas.DataFrame`. If
    `catalog_match=True` then the resulting sources will be matched against the
    PANOPTES catalog, which is a filtered version of the TESS Input Catalog. See
    `get_catalog_match` for details and column list.

    Sextractor will return the following columns:

        * ALPHA_J2000   ->  sextractor_ra
        * DELTA_J2000   ->  sextractor_dec
        * XPEAK_IMAGE   ->  sextractor_x
        * YPEAK_IMAGE   ->  sextractor_y
        * X_IMAGE       ->  sextractor_x_image
        * Y_IMAGE       ->  sextractor_y_image
        * ELLIPTICITY   ->  sextractor_ellipticity
        * THETA_IMAGE   ->  sextractor_theta_image
        * FLUX_BEST     ->  sextractor_flux_best
        * FLUXERR_BEST  ->  sextractor_fluxerr_best
        * FLUX_MAX      ->  sextractor_flux_max
        * FLUX_GROWTH   ->  sextractor_flux_growth
        * MAG_BEST      ->  sextractor_mag_best
        * MAGERR_BEST   ->  sextractor_magerr_best
        * FWHM_IMAGE    ->  sextractor_fwhm_image
        * BACKGROUND    ->  sextractor_background
        * FLAGS         ->  sextractor_flags

    Notes:
            * Sources within a certain `trim_size` (default 10) of the image edges will be
            automatically pruned.

        >>> from panoptes.utils.stars import lookup_point_sources
        >>> fits_fn = getfixture('solved_fits_file')

        >>> point_sources = lookup_point_sources(fits_fn)
        >>> point_sources.describe()
               sextractor_ra  sextractor_dec  ...  sextractor_background  sextractor_flags
        count     473.000000      473.000000  ...             473.000000        473.000000
        mean      303.284052       46.011116  ...            2218.525156          1.143763
        std         0.810261        0.582264  ...               4.545206          3.130030
        min       301.794797       45.038730  ...            2205.807000          0.000000
        25%       302.598079       45.503276  ...            2215.862000          0.000000
        50%       303.243873       46.021710  ...            2218.392000          0.000000
        75%       303.982358       46.497813  ...            2221.577000          0.000000
        max       304.637887       47.015707  ...            2229.050000         27.000000
        ...
        >>> type(point_sources)
        <class 'pandas.core.frame.DataFrame'>

    Args:
        fits_file (str, optional): Path to FITS file to search for stars.
        catalog_match (bool, optional): If `get_catalog_match` should be called after looking up sources. Default False. If True, the `args` and `kwargs` will be passed to `get_catalog_match`.
        method (str, optional): Method for looking up sources, default (and currently only) is `sextractor`.
        force_new (bool, optional): Force a new catalog to be created,
            defaults to False.
        **kwargs: Passed to `get_catalog_match` when `catalog_match=True`.

    Raises:
        Exception: Raised for any exception.

    Returns:
        `pandas.DataFrame`: A dataframe contained the sources.

    """
    if catalog_match:
        wcs = fits_utils.getwcs(fits_file)
        assert wcs is not None and wcs.is_celestial, logger.warning("Need a valid WCS")

    logger.debug(f"Looking up sources for {fits_file}")

    # Only one supported method for now.
    lookup_function = {
        'sextractor': _lookup_via_sextractor,
    }

    # Lookup our appropriate method and call it with the fits file and kwargs
    try:
        logger.debug(f"Using {method} method for {fits_file}")
        point_sources = lookup_function[method](fits_file, force_new=force_new, **kwargs)
    except Exception as e:
        raise Exception(f"Problem looking up sources: {e!r} {fits_file}")

    if catalog_match:
        logger.debug(f'Doing catalog match against stars {fits_file}')
        try:
            point_sources = get_catalog_match(point_sources, wcs, **kwargs)
            logger.debug(f'Done with catalog match for {fits_file}')
        except Exception as e:
            logger.error(f'Error in catalog match, returning unmathed results: {e!r} {fits_file}')

    logger.debug(f'Point sources: {len(point_sources)} {fits_file}')
    return point_sources


def get_catalog_match(point_sources,
                      wcs,
                      vmag_min=4,
                      vmag_max=17,
                      max_separation_arcsec=None,
                      return_unmatched=False,
                      origin=1,
                      **kwargs):
    """Match the point source positions to the catalog.

    The catalog is matched to the PANOPTES Input Catalog (PIC), which is derived
    from the [TESS Input Catalog](https://tess.mit.edu/science/tess-input-catalogue/)
    [v8](https://heasarc.gsfc.nasa.gov/docs/tess/tess-input-catalog-version-8-tic-8-is-now-available-at-mast.html).

    The catalog is stored in a BigQuery dataset. This function will match the
    `sextractor_ra` and `sextractor_dec` columns (as output from `lookup_point_sources`)
    to the `ra` and `dec` colums of the catalog.  The actual lookup is done via
    the `get_stars_from_footprint` function.

    The columns are added to `point_sources`, which is then returned to the user.

    Columns that are added to `point_sources` include:

        * picid
        * gaia
        * twomass
        * catalog_dec
        * catalog_ra
        * catalog_sep_arcsec
        * catalog_sextractor_diff_arcsec_dec
        * catalog_sextractor_diff_arcsec_ra
        * catalog_sextractor_diff_x
        * catalog_sextractor_diff_y
        * catalog_vmag
        * catalog_vmag_err
        * catalog_x
        * catalog_y

    Note:

        Note all fields are expected to have values. In particular, the `gaia`
        and `twomass` fields are often mutually exclusive.  If `return_unmatched=True`
        (see below) then all values related to matching will be `NA` for all `sextractor`
        related columns.

    By default only the sources that are successfully matched by the catalog are returned.
    This behavior can be changed by setting `return_unmatched=True`. This will append
    *all* catalog entries within the Vmag range [vmag_min, vmag_max).

    Warning:

        Using `return_unmatched=True` can return a very large datafraame depending
        on the chosen Vmag range and galactic coordinates. However, it should be
        noted that limiting the Vmag range makes results less accurate.

        The best policy would be to try to minimize calls to this function. The
        resulting dataframe can be saved locally with `point_sources.to_csv(path_name)`.

    If a `max_separation_arcsec` is given then results will be filtered if their
    match with `sextractor` was larger than the number given. Typical values would
    be in the range of 20-30 arcsecs, which corresponds to 2-3 pixels.

    Returns:
        `pandas.DataFrame`: A dataframe with the catalog information added to the
        sources.

    Args:
        point_sources (`pandas.DataFrame`): The DataFrame containted point sources
            to be matched. This usually comes from the output of `lookup_point_sources`
            but could be done manually.
        wcs (`astropy.wcs.WCS`): The WCS instance.
        origin (int, optional): The origin for catalog matching, either 0 or 1 (default).
        max_separation_arcsec (float|None, optional): If not None, sources more
            than this many arcsecs from catalog will be filtered.
        return_unmatched (bool, optional): If all results from catalog should be
            returned, not just those with a positive match.
        **kwargs: Unused.

    """
    assert point_sources is not None
    logger.debug(f'Doing catalog match for wcs={wcs!r}')

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

    # Get the xy pixel coordinates for all sources according to WCS.
    xs, ys = wcs.all_world2pix(catalog_stars.catalog_ra,
                               catalog_stars.catalog_dec,
                               origin,
                               ra_dec_order=True)
    catalog_stars['catalog_x'] = xs
    catalog_stars['catalog_y'] = ys

    # Add the matches and their separation.
    matches = catalog_stars.iloc[idx]
    point_sources = point_sources.join(matches.reset_index(drop=True))
    point_sources['catalog_sep_arcsec'] = d2d.to(u.arcsec).value

    # All point sources so far are matched.
    point_sources['status'] = 'matched'

    # Reorder columns so id cols are first then alpha.
    new_column_order = sorted(list(point_sources.columns))
    id_cols = ['picid', 'gaia', 'twomass', 'status']
    for i, col in enumerate(id_cols):
        new_column_order.remove(col)
        new_column_order.insert(i, col)
    point_sources = point_sources.reindex(columns=new_column_order)

    # Sources that didn't match.
    if return_unmatched:
        unmatched = catalog_stars.iloc[catalog_stars.index.difference(idx)].copy()
        unmatched['status'] = 'unmatched'
        point_sources = point_sources.append(unmatched)

    # Correct some dtypes.
    point_sources.status = point_sources.status.astype('category')

    # Remove catalog matches that are too far away.
    if max_separation_arcsec is not None:
        logger.debug(f'Removing matches > {max_separation_arcsec} arcsec from catalog.')
        point_sources = point_sources.query('catalog_sep_arcsec <= @max_separation_arcsec')

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
            raise Exception(f"Problem running sextractor: {e.stderr}\n\n{e.stdout}")

    # Read catalog
    logger.debug(f'Building detected source table with {source_file}')
    point_sources = Table.read(source_file, format='ascii.sextractor')

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
        'sextractor_flux_max',
        'sextractor_flux_growth',
        'sextractor_mag_best',
        'sextractor_magerr_best',
        'sextractor_fwhm_image',
        'sextractor_background',
        'sextractor_flags',
    ]

    logger.debug(f'Returning {len(point_sources)} sources from sextractor')
    return point_sources
