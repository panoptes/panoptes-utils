from datetime import datetime as dt
from datetime import timezone as tz

from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore

from astropy.coordinates import SkyCoord
from astropy import units as u

import pandas as pd
import hvplot.pandas  # noqa

from dateutil.parser import parse as date_parse

from .. import listify
from ..logger import logger


def _get_firestore_client(project_id='panoptes-exp', database='(default)'):
    logger.debug(f'Getting new firestore client')
    firestore_client = firestore.Client(
        project=project_id,
        database=database,
        credentials=AnonymousCredentials()
    )
    return firestore_client


def get_metadata(image_id=None, sequence_id=None, fields=None, firestore_client=None):
    """Access PANOPTES data from the network.

    This function is capable of searching one type of object at a time, which is
    specified via the respective id parameter.

    #TODO(wtgee): Setup firestore emulator for testing. #179

    >>> from panoptes.utils.data import get_metadata
    >>> # Get image metadata as a DataFrame with one record.
    >>> image_id = 'PAN001_14d3bd_20181204T134406'
    >>> image_df = get_metadata(image_id=image_id)
    >>> type(image_df)
    <class 'pandas.core.frame.DataFrame'>
    >>> # This can easily be saved to csv or cast to dict.
    >>> image_metadata = image_df.to_dict(orient='record')[0]
    >>> image_metadata['status']
    'solved'
    >>> image_metadata['received_time']
    Timestamp('2020-04-17 09:16:20.371000+0000', tz='UTC')

    >>> # Get all image metadata for the observation.
    >>> sequence_id = 'PAN001_14d3bd_20181119T131353'
    >>> observation_df = get_metadata(sequence_id=sequence_id)
    >>> type(observation_df)
    <class 'pandas.core.frame.DataFrame'>
    >>> len(observation_df)
    40

    >>> # It's also possible to request certain fields
    >>> airmass_df = get_metadata(sequence_id=sequence_id, fields=['airmass'])
    >>> airmass_df.head()
        airmass
    0  1.161770
    1  1.166703
    2  1.172055
    3  1.177555
    4  1.183283

    Args:
        image_id (str|None): The id associated with an image.
        sequence_id (str|list|None): The list of sequence_ids associated with an observation.
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.
        firestore_client (`google.cloud.firestore.Client`|None): The client instance
            to use. If `None` is provided (the default), then client will attempt
            to connect with default environmental credentials.

    Returns:

    """
    if firestore_client is None:
        firestore_client = _get_firestore_client()

    # Get a FITS image from the bucket.
    if image_id is not None:
        return get_image_metadata(image_id=image_id, fields=fields, firestore_client=firestore_client)

    # Get observation metadata from firestore.
    if sequence_id is not None:
        return get_observation_metadata(listify(sequence_id), fields=fields, firestore_client=firestore_client)


def get_image_metadata(image_id, fields=None, firestore_client=None):
    """Downloads the image at the given path.

    This function by default returns a `pandas.DataFrame` to be consistent with
    the `get_observation_metadata` function however that DataFrame should only contain
    a single row. Note that it will still be a DataFrame and not a `pandas.Series`.

    >>> from panoptes.utils.data import get_image_metadata
    >>> # Get image metadata as a DataFrame with one record.
    >>> image_id = 'PAN001_14d3bd_20181204T134406'
    >>> image_df = get_image_metadata(image_id=image_id, fields=['bucket_path'])
    >>> # Always includes the image_id and timestamp.
    >>> image_df.to_dict(orient='record')
    [{'bucket_path': 'PAN001/14d3bd/20181204T133735/20181204T134406.fits.fz',
      'image_id': 'PAN001_14d3bd_20181204T134406',
      'time': Timestamp('2018-12-04 13:44:06+0000', tz='UTC')}]
    >>> type(image_df)
    <class 'pandas.core.frame.DataFrame'>

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
        firestore_client = _get_firestore_client()

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
    df = pd.DataFrame(image_doc, index=[0]).convert_dtypes()
    df = df.reindex(sorted(df.columns), axis=1)

    # Remove metadata metadata.
    # Remove fields if only certain fields requested.
    # TODO(wtgee) implement this filtering at the firestore level.
    if fields is not None:
        remove_cols = set(df.columns).difference(fields)
        # Don't remove the id or time.
        remove_cols.remove('image_id')
        remove_cols.remove('time')
        df.drop(columns=remove_cols, inplace=True)

    # TODO(wtgee) any data cleaning or preparation for images here.

    return df


def get_observation_metadata(sequence_ids, firestore_client=None, fields=None):
    """Get the metadata for given sequence_ids.

    Args:
        sequence_ids (list): A list of sequence_ids as strings.
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.
        firestore_client (`google.cloud.firestore.Client`): An authenticated
            client instance. If None is provided then an anonymous connection will
            be made.

    Returns:
        `pandas.DataFrame`: DataFrame containing the observation metadata.
    """
    if firestore_client is None:
        firestore_client = _get_firestore_client()

    sequence_ids = listify(sequence_ids)

    observation_dfs = list()
    for sequence_id in sequence_ids:
        logger.debug(f'Getting images metadata for observation={sequence_id}')

        # Build query
        obs_query = firestore_client.collection('images').where('sequence_id', '==', sequence_id)

        # Fetch documents into a DataFrame.
        df = pd.DataFrame([dict(image_id=doc.id, **doc.to_dict()) for doc in obs_query.stream()])
        observation_dfs.append(df.convert_dtypes())

    if len(observation_dfs) == 0:
        logger.debug(f'No documents found for sequence_ids={sequence_ids}')
        return

    df = pd.concat(observation_dfs)
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

    >>> from astropy.coordinates import SkyCoord
    >>> from panoptes.utils.data import search_observations
    >>> m42_coords = SkyCoord.from_name('M42')
    >>> search_results = search_observations(coords=m42_coords, radius=5, min_num_images=10, end_date='2020-04-27')
    >>> # The result is a DataFrame you can further work with.
    >>> search_results.groupby(['unit_id', 'field_name']).num_images.sum()
    unit_id  field_name
    PAN001   FlameNebula    436
             M42            422
    PAN006   M42             40
             Wasp 35         69
    Name: num_images, dtype: Int64
    >>> search_results.total_minutes_exptime.sum()
    1422.0

    Args:
        ra (float|None): The RA position in degrees of the center of search.
        dec (float|None): The Dec position in degrees of the center of the search.
        coords (`astropy.coordinates.SkyCoord`|None): A valid coordinate instance.
        radius (float): The search radius in degrees. Searches are currently done in
            a square box, so this is half the length of the side of the box.
        start_date (str|`datetime.datetime`|None): A valid datetime instance or `None` (default).
            If `None` then the beginning of 2018 is used as a start date.
        end_date (str|`datetime.datetime`|None): A valid datetime instance or `None` (default).
            If `None` then today is used.
        unit_ids (str|list|None): A str or list of strs of unit_ids to include.
            Default `None` will include all.
        status (str|list|None): A str or list of observation status to include.
            Default `None` will include all.
        min_num_images (int): Minimum number of images the observation should have, default 1.
        fields (str|list|None): A list of fields (columns) to include.
            Default `None` will include all.
        limit (int): The maximum number of firestore records to return, default 5000.
        firestore_client (`google.cloud.firestore.Client`|None): A firestore client instance.
            If default `None`, then the function will attempt to make an anonymous connection.

    Returns:
        `pandas.DataFrame`: A table with the matching observation results.
    """
    if firestore_client is None:
        firestore_client = _get_firestore_client()

    logger.debug(f'Setting up search params')

    if coords is None:
        coords = SkyCoord(ra=ra, dec=dec, unit='degree')

    # Setup defaults for search.
    if start_date is None:
        start_date = dt.strptime('2018-01-01', '%Y-%m-%d')
    elif isinstance(start_date, str):
        start_date = date_parse(start_date)

    if end_date is None:
        end_date = dt.now()
    elif isinstance(end_date, str):
        end_date = date_parse(end_date)

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
        df.query(f'unit_id in {listify(unit_ids)}', inplace=True)

    if status is not None:
        df.query(f'status in {listify(status)}', inplace=True)

    logger.debug(f'Found {len(df)} observations after filtering')

    df = df.reindex(sorted(df.columns), axis=1)
    df.sort_values(by=['time'], inplace=True)

    # TODO(wtgee) any data cleaning or preparation for observations here.

    # Remove fields if only certain fields requested.
    # TODO(wtgee) implement this filtering at the firestore level.
    if fields is not None:
        remove_cols = set(df.columns).difference(listify(fields))
        df.drop(columns=remove_cols, inplace=True)

    return df
