# Downloads IERS Bulletin A (Earth Orientation Parameters, used by astroplan)
# and astrometry.net indices.

import os
import shutil

import pandas as pd
from astroplan import download_IERS_A
from astropy.utils import data
from google.cloud import firestore
from google.cloud import storage

from .logger import logger


def get_data(image_id=None, sequence_id=None, firestore_client=None):
    """Access PANOPTES data from the network.

    This function is capable of searching one type of object at a time, which is
    specified via the respective id parameter.

    Example:

        >>> # Download a specific image.
        >>> from panoptes.utils.images import fits as fits_utils
        >>> from panoptes.utils.data import get_data
        >>> image_id = 'PAN001_14d3bd_20160911T101445'
        >>> fits_file = get_data(image_id=image_id)  # doctest: +SKIP
        >>> fits_utils.getval(fits_file, 'FIELD')  # doctest: +SKIP
        Wasp 33

        >>> # Download observation information
        >>> sequence_id = 'PAN001_14d3bd_20160911T095804'
        >>> observation = get_data(sequence_id=sequence_id) # doctest: +SKIP
        >>> observation.describe() # doctest: +SKIP
                  exptime    dec_mnt     moonsep  ...     ha_mnt    airmass  dec_image
        count   10.000000  10.000000   10.000000  ...  10.000000  10.000000   3.000000
        mean   133.150000  37.550481  121.816168  ...  20.785812   1.432349  37.551674
        std     40.635268   0.000000    0.058508  ...   0.142363   0.043384   0.002784
        min    120.300000  37.550481  121.734949  ...  20.538607   1.375450  37.548547
        25%    120.300000  37.550481  121.773715  ...  20.704128   1.400616  37.550569
        50%    120.300000  37.550481  121.812113  ...  20.796700   1.427342  37.552590
        75%    120.300000  37.550481  121.850095  ...  20.889282   1.455701  37.553237
        max    248.800000  37.550481  121.916972  ...  20.981754   1.510904  37.553885

    Args:
        image_id (str|None): The id associated with an image.
        sequence_id (str|None): The id associated with an observation.
        firestore_client (`google.cloud.firestore.Client`|None): The client instance
            to use. If `None` is provided (the default), then client will attempt
            to connect with default environmental credentials.

    Returns:

    """
    if firestore_client is None:
        firestore_client = firestore.Client()

    # Get a FITS image from the bucket.
    if image_id is not None:
        # Lookup the full path from the firestore db
        bucket_path = firestore_client.document(f'images/{image_id}').get().get('bucket_path')
        logger.debug(f'Bucket path for {image_id}: {bucket_path}')

        return get_image(bucket_path)

    # Get observation metadata from firestore.
    if sequence_id is not None:
        return get_observation(sequence_id, firestore_client=firestore_client)


def get_image(bucket_path, bucket_name='panoptes-raw-images'):
    """Downloads the image at the given path.

    Args:
        bucket_path (str): The relative path to the object in the bucket.
        bucket_name (str): The name of the bucket to use, default `panoptes-raw-images`.

    Returns:
        str: The full path to the downloaded image.
    """
    # Get access to the storage bucket
    bucket = storage.Client().bucket(bucket_name)

    # Get image blob.
    image_path = bucket_path.replace('/', '_')
    logger.debug(f'Downloading {bucket_path} to {image_path}')
    bucket.blob(bucket_path).download_to_filename(image_path)

    return image_path


def get_observation(sequence_id, firestore_client=None):
    """Get the observation metadata.

    TODO(wtgee): Support returning the observation metatdata.

    Args:
        sequence_id (str): The id for the given observation.

    Returns:
        `pandas.DataFrame`: The
    """
    if firestore_client is None:
        firestore_client = firestore.Client()

    logger.debug(f'Getting observation={sequence_id}')

    # Build query
    obs_query = firestore_client.collection('images').where('sequence_id', '==', sequence_id)

    # Fetch documents into a DataFrame.
    df = pd.DataFrame([dict(id=doc.id, **doc.to_dict()) for doc in obs_query.stream()])

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
