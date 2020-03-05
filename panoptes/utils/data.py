# Downloads IERS Bulletin A (Earth Orientation Parameters, used by astroplan)
# and astrometry.net indices.

import os
import shutil

from astroplan import download_IERS_A
from astropy.utils import data

from .logger import logger


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

