from datetime import datetime as dt
from datetime import timezone as tz

from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore

from astropy.coordinates import SkyCoord
from astropy import units as u

import pandas as pd
import hvplot.pandas  # noqa

from .. import listify
from ..logger import logger


def get_data(image_id=None, sequence_id=None, fields=None, firestore_client=None):
    """Access PANOPTES data from the network.

    This function is capable of searching one type of object at a time, which is
    specified via the respective id parameter.

    #TODO(wtgee): Setup firestore emulator for testing.

    >>> from panoptes.utils.data import get_data
    >>> # Get image metadata as a DataFrame with one record.
    >>> image_id = 'PAN001_14d3bd_20160911T101445'
    >>> image_info = get_data(image_id=image_id)
    >>> image_info
        airmass  background_median  ...                      time unit_id
    0  1.421225               <NA>  ... 2016-09-11 10:14:45+00:00  PAN001
    >>> type(image_info)
    pandas.core.frame.DataFrame

    >>> # Get all image metadata for the observation.
    >>> sequence_id = 'PAN001_14d3bd_20160911T095804'
    >>> observation = get_data(sequence_id=sequence_id)
    >>> observation.describe()
             airmass  dec_image    dec_mnt  ...     moonsep   ra_image     ra_mnt
    count  10.000000   4.000000  10.000000  ...   10.000000   4.000000  10.000000
    mean    1.432349  37.551726  37.550481  ...  121.816168  36.698585  36.712742
    std     0.043384   0.002276   0.000000  ...    0.058508   0.007672   0.000000
    min     1.375450  37.548547  37.550481  ...  121.734949  36.690686  36.712742
    25%     1.400616  37.551047  37.550481  ...  121.773715  36.692726  36.712742
    50%     1.427342  37.552235  37.550481  ...  121.812113  36.698786  36.712742
    75%     1.455701  37.552914  37.550481  ...  121.850095  36.704645  36.712742
    max     1.510904  37.553885  37.550481  ...  121.916972  36.706083  36.712742
    >>> # It's also possible to request certain fields
    >>> urls = get_data(sequence_id=sequence_id, fields=['public_url'])

    Args:
        image_id (str|None): The id associated with an image.
        sequence_id (str|None): The id associated with an observation.
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.
        firestore_client (`google.cloud.firestore.Client`|None): The client instance
            to use. If `None` is provided (the default), then client will attempt
            to connect with default environmental credentials.

    Returns:

    """
    if firestore_client is None:
        logger.debug(f'Getting new firestore client')
        firestore_client = firestore.Client(
            database=PROJECT_ID,
            project=PROJECT_ID,
            credentials=AnonymousCredentials()
        )

    # Get a FITS image from the bucket.
    if image_id is not None:
        return get_image(image_id=image_id, fields=fields, firestore_client=firestore_client)

    # Get observation metadata from firestore.
    if sequence_id is not None:
        return get_observation(sequence_id, fields=fields, firestore_client=firestore_client)


def get_image(image_id, fields=None, firestore_client=None):
    """Downloads the image at the given path.

    This function by default returns a `pandas.DataFrame` to be consistent with
    the `get_observation` function however that DataFrame should only contain
    a single row. Note that it will still be a DataFrame and not a `pandas.Series`.

    Args:
        image_id (str): The id for the given image.
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.
        firestore_client (`google.cloud.firestore.Client`): An authenticated
            client instance. If None is provided then an anonymous connection will
            be made.

    Returns:
        `pandas.DataFrame`: DataFrame containing the image metadata.
    """
    if firestore_client is None:
        firestore_client = firestore.Client()

    logger.debug(f'Getting metadata for image={image_id}')

    # Get document reference.
    image_doc_ref = firestore_client.document(f'images/{image_id}')
    image_doc_snapshot = image_doc_ref.get()

    if image_doc_snapshot is None:
        logger.debug(f'No document found for image_id={image_id}')
        return

    # Get the actual image metadata.
    image_doc = image_doc_snapshot.to_dict()
    image_doc['image_id'] = image_doc_snapshot.id

    # Put document into dataframe.
    df = pd.DataFrame(image_doc, index=[0])
    df = df.convert_dtypes()
    df = df.reindex(sorted(df.columns), axis=1)

    # Remove metadata metadata.
    # Remove fields if only certain fields requested.
    # TODO(wtgee) implement this filtering at the firestore level.
    if fields is not None:
        remove_cols = set(df.columns).difference(fields)
        df.drop(columns=remove_cols, inplace=True)

    # TODO(wtgee) any data cleaning or preparation for images here.

    return df


def get_observation(sequence_id, firestore_client=None, fields=None):
    """Get the observation metadata.

    Args:
        sequence_id (str): The id for the given observation.
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.
        firestore_client (`google.cloud.firestore.Client`): An authenticated
            client instance. If None is provided then an anonymous connection will
            be made.

    Returns:
        `pandas.DataFrame`: DataFrame containing the observation metadata.
    """
    if firestore_client is None:
        firestore_client = firestore.Client()

    logger.debug(f'Getting images metadata for observation={sequence_id}')

    # Build query
    obs_query = firestore_client.collection('images').where('sequence_id', '==', sequence_id)

    # Fetch documents into a DataFrame.
    df = pd.DataFrame([dict(image_id=doc.id, **doc.to_dict()) for doc in obs_query.stream()])

    if len(df) == 0:
        logger.debug(f'No documents found for sequence_id={sequence_id}')
        return

    df = df.convert_dtypes()
    df = df.reindex(sorted(df.columns), axis=1)
    df.sort_values(by=['time'], inplace=True)

    # TODO(wtgee) any data cleaning or preparation for observations here.

    # Remove fields if only certain fields requested.
    # TODO(wtgee) implement this filtering at the firestore level.
    if fields is not None:
        remove_cols = set(df.columns).difference(fields)
        df.drop(columns=remove_cols, inplace=True)

    return df


def search_observations(
        ra=None,
        dec=None,
        coords=None,
        radius=10,  # degrees
        start_date=None,
        end_date=None,
        unit_ids=None,
        status=None,
        min_num_images=1,
        fields=None,
        limit=5000,
        firestore_client=None,
):
    """Search PANOPTES observations.

    Args:
        ra (float|None): The RA position in degrees of the center of search.
        dec (float|None): The Dec position in degrees of the center of the search.
        coords (`astropy.coordinates.SkyCoord`|None): A valid coordinate instance.
        radius (float): The search radius in degrees. Searches are currently done in
            a square box, so this is half the length of the side of the box.
        start_date (`datetime.datetime`|None): A valid datetime instance or `None` (default).
            If `None` then the beginning of 2018 is used as a start date.
        end_date (`datetime.datetime`|None): A valid datetime instance or `None` (default).
            If `None` then today is used.
        unit_ids (str|list|None): A str or list of strs of unit_ids to include.
            Default `None` will include all.
        status (str|list|None): A str or list of observation status to include.
            Default `None` will include all.
        min_num_images (int): Mininmum number of images the observation should have, defaul 1.
        fields (str|list|None): A list of fields (columns) to include.
            Default `None` will include all.
        limit (int): The maximum number of firestore records to return, default 5000.
        firestore_client (`google.cloud.firestore.Client`|None): A firestore client instance.
            If default `None`, then the function will attempt to make an anonymous connection.

    Returns:
        `pandas.DataFrame`: A table with the matching observation results.
    """
    if firestore_client is None:
        firestore_client = firestore.Client()

    logger.debug(f'Setting up search params')

    if coords is None:
        coords = SkyCoord(ra=ra, dec=dec, unit='degree')

    # Setup defaults for search.
    if start_date is None:
        start_date = dt.strptime('2018-01-01', '%Y-%m-%d')
    if end_date is None:
        end_date = dt.now()

    ra_max = (coords.ra + (radius * u.degree)).value
    ra_min = (coords.ra - (radius * u.degree)).value
    dec_max = (coords.dec + (radius * u.degree)).value
    dec_min = (coords.dec - (radius * u.degree)).value

    logger.debug(f'Searching for observations')
    obs_query = firestore_client.collection('observations') \
        .where('dec', '>=', dec_min) \
        .where('dec', '<=', dec_max) \
        .limit(limit)

    # Fetch documents.
    docs = [dict(sequence_id=doc.id, **doc.to_dict()) for doc in obs_query.stream()]

    if len(docs) == 0:
        logger.debug(f'No documents found for collections query')
        return

    # Put documents into a DataFrame.
    df = pd.DataFrame(docs).convert_dtypes()
    logger.debug(f'Found {len(df)} observations')

    # Perform filtering on other fields here.
    logger.debug(f'Filtering observations')
    df.query(
        f'ra >= {ra_min} and ra <= {ra_max}'
        ' and '
        f'time >= "{start_date.astimezone(tz.utc)}" and time <= "{end_date.astimezone(tz.utc)}"'
        ' and '
        f'num_images >= {min_num_images}'
        ,
        inplace=True
    )
    if unit_ids is not None and unit_ids != 'The Whole World! 🌎':
        unit_ids = listify(unit_ids)
        df.query(f'unit_id in @unit_ids', inplace=True)

    if status is not None:
        status = listify(status)
        df.query(f'status in @status', inplace=True)

    logger.debug(f'Found {len(df)} observations after filtering')

    df = df.reindex(sorted(df.columns), axis=1)
    df.sort_values(by=['time'], inplace=True)

    # TODO(wtgee) any data cleaning or preparation for observations here.

    # Remove fields if only certain fields requested.
    # TODO(wtgee) implement this filtering at the firestore level.
    if fields is not None:
        remove_cols = set(df.columns).difference(fields)
        df.drop(columns=remove_cols, inplace=True)

    return df
