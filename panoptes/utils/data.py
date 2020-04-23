import os
import shutil

import pandas as pd
from astroplan import download_IERS_A
from astropy.utils import data
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore

from .logger import logger

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')


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
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.
        image_id (str): The id for the given image.

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

    # Put document into dataframe
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
        fields (list|None):  A list of fields to fetch from the database. If None,
            returns all fields.
        sequence_id (str): The id for the given observation.

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


class Downloader:
    """Downloads IERS Bulletin A and astrometry.net indices.

    IERS Bulletin A contains rapid determinations for earth orientation
    parameters, and is used by astroplan. Learn more at: https://www.iers.org

    Astrometry.net provides indices used to 'plate solve', i.e. to determine
    which stars are in an arbitrary image of the night sky.
    """

    def __init__(self,
                 data_folder=None,
                 wide_field=True,
                 narrow_field=False,
                 keep_going=True,
                 verbose=False):
        """
        Args:
            data_folder: Path to directory into which to copy the astrometry.net indices.
            wide_field: If True, downloads wide field astrometry.net indices.
            narrow_field: If True, downloads narrow field astrometry.net indices.
            keep_going: If False, exceptions are not suppressed. If True, returns False if there
                are any download failures, else returns True.
            verbose (bool, optional): If console output, default False.
        """
        self.data_folder = data_folder
        self.wide_field = wide_field
        self.narrow_field = narrow_field
        self.keep_going = keep_going
        self.verbose = verbose

    def download_all_files(self):
        """Downloads the files according to the attributes of this object."""
        result = True

        result = self.download_iers()

        if self.wide_field:
            for i in range(4110, 4119):
                if not self.download_one_file(f'4100/index-{i}.fits'):
                    result = False

        if self.narrow_field:
            for i in range(4210, 4219):
                if not self.download_one_file(f'4200/index-{i}.fits'):
                    result = False
        return result

    def download_iers(self):
        """Downloads the earth rotation catalog needed for accurate coordinate positions.

        Note: This download gives us a host of problems. This function should be called
        less than every 14 days otherwise a warning will be given. Currently we
        are downloading of our own google-based mirror of the data.

        Returns:
            TYPE: Description
        """
        try:
            download_IERS_A(show_progress=self.verbose)
            return True
        except Exception as e:
            logger.warning(f'Failed to download IERS A bulletin: {e}')
            return False

    def download_one_file(self, fn):
        """Downloads one astrometry.net file into self.data_folder."""
        dest = "{}/{}".format(self.data_folder, os.path.basename(fn))
        if os.path.exists(dest):
            return True
        url = "http://data.astrometry.net/{}".format(fn)
        try:
            df = data.download_file(url)
        except Exception as e:
            if not self.keep_going:
                raise e
            logger.warning(f'Failed to download {url}: {e}')
            return False
        # The file has been downloaded to some directory. Move the file into the data folder.
        try:
            self.create_data_folder()
            shutil.move(df, dest)
            return True
        except OSError as e:
            if not self.keep_going:
                raise e
            logger.warning(f"Problem saving {url}. Check permissions: {e}")
            return False

    def create_data_folder(self):
        """Creates the data folder if it does not exist."""
        if not os.path.exists(self.data_folder):
            logger.info("Creating data folder: {}.".format(self.data_folder))
            os.makedirs(self.data_folder)
