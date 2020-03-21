from .logger import logger


def get_stars_from_footprint(wcs_footprint, **kwargs):
    """Lookup star information from WCS footprint.

    This is just a thin wrapper around `get_stars`.

    Args:
        wcs_footprint (`astropy.wcs.WCS`): The world coordinate system (WCS) for an image.
        **kwargs: Optional keywords to pass to `get_stars`.

    Returns:
        TYPE: Description
    """
    wcs_footprint = list(wcs_footprint)
    # Add the first entry to the end to complete polygon
    wcs_footprint.append(wcs_footprint[0])

    poly = ','.join([f'{c[0]:.05} {c[1]:.05f}' for c in wcs_footprint])

    return get_stars(shape=poly, **kwargs)


def get_stars(
        bq_client,
        shape=None,
        vmag_min=6,
        vmag_max=12,
        client=None,
        **kwargs):
    """Look star information from the TESS catalog.

    Note:


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
    SELECT id, ra, dec, vmag
    FROM catalog.pic
    WHERE
      vmag_partition BETWEEN {vmag_min} AND {vmag_max}
      {sql_constraint}
    """

    try:
        df = bq_client.query(sql).to_dataframe()
    except Exception as e:
        logger.warning(e)
        df = None

    return df
