from contextlib import suppress

from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.utils.data import download_file

import pandas as pd
import hvplot.pandas  # noqa

import pendulum

from .. import listify
from ..logger import logger


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

    Returns:

    """
    # Get a FITS image from the bucket.
    if image_id is not None:
        return get_image_metadata(image_id=image_id, fields=fields)

    # Get observation metadata from firestore.
    if sequence_id is not None:
        return get_observation_metadata(listify(sequence_id), fields=fields)


def get_image_metadata(image_id, fields=None):
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

    Returns:
        `pandas.DataFrame`: DataFrame containing the image metadata.
    """

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


def get_observation_metadata(sequence_ids, fields=None):
    """Get the metadata for given sequence_ids.

    Args:
        sequence_ids (list): A list of sequence_ids as strings.
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.

    Returns:
        `pandas.DataFrame`: DataFrame containing the observation metadata.
    """
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
        unit_id=None,
        start_date=None,
        end_date=None,
        ra=None,
        dec=None,
        coords=None,
        radius=10,  # degrees
        status=None,
        min_num_images=1,
        url='https://storage.googleapis.com/panoptes-exp.appspot.com/observations.csv'
):
    """Search PANOPTES observations.

    >>> from astropy.coordinates import SkyCoord
    >>> from panoptes.utils.data import search_observations
    >>> m42_coords = SkyCoord.from_name('M42')
    >>> search_results = search_observations(coords=m42_coords, radius=5, min_num_images=10, end_date='2020-04-27')
    >>> # The result is a DataFrame you can further work with.
    >>> search_results.groupby(['unit_id', 'field_name']).num_images.sum()
    unit_id  field_name
    PAN001   FlameNebula    754
             M42            923
    PAN006   M42             58
             Wasp 35        141
    Name: num_images, dtype: Int64
    >>> search_results.total_minutes_exptime.sum()
    2792.0

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

    Returns:
        `pandas.DataFrame`: A table with the matching observation results.
    """

    logger.debug(f'Setting up search params')

    if coords is None:
        coords = SkyCoord(ra=ra, dec=dec, unit='degree')

    # Setup defaults for search.
    if start_date is None:
        start_date = '2018-01-01'

    if end_date is None:
        end_date = pendulum.now()

    with suppress(TypeError):
        start_date = pendulum.parse(start_date).replace(tzinfo=None)
    with suppress(TypeError):
        end_date = pendulum.parse(end_date).replace(tzinfo=None)

    ra_max = (coords.ra + (radius * u.degree)).value
    ra_min = (coords.ra - (radius * u.degree)).value
    dec_max = (coords.dec + (radius * u.degree)).value
    dec_min = (coords.dec - (radius * u.degree)).value

    logger.debug(f'Getting list of observations')

    # Get the observation list
    local_path = download_file(url, cache='update', show_progress=False, pkgname='panoptes')
    obs_df = pd.read_csv(local_path).convert_dtypes()

    logger.debug(f'Found {len(obs_df)} total observations')

    # Perform filtering on other fields here.
    logger.debug(f'Filtering observations')
    obs_df.query(
        f'dec >= {dec_min} and dec <= {dec_max}'
        ' and '
        f'ra >= {ra_min} and ra <= {ra_max}'
        ,
        inplace=True
    )
    logger.debug(f'Found {len(obs_df)} observations after initial filter')

    unit_ids = listify(unit_id)
    if len(unit_ids) > 0 and unit_ids != 'The Whole World! 🌎':
        obs_df.query(f'unit_id in {listify(unit_ids)}', inplace=True)
    logger.debug(f'Found {len(obs_df)} observations after unit filter')

    if status is not None:
        obs_df.query(f'status in {listify(status)}', inplace=True)
    logger.debug(f'Found {len(obs_df)} observations after status filter')

    logger.debug(f'Found {len(obs_df)} observations after filtering')

    obs_df = obs_df.reindex(sorted(obs_df.columns), axis=1)
    obs_df.sort_values(by=['time'], inplace=True)

    # TODO(wtgee) any data cleaning or preparation for observations here.

    return obs_df
