#!/usr/bin/env python

import os
import click

from panoptes.utils.data import Downloader
from panoptes.utils.logger import logger

DEFAULT_DATA_FOLDER = os.path.expandvars("$PANDIR/astrometry/data")


@click.command()
@click.option('--folder',
              default=DEFAULT_DATA_FOLDER,
              help=f'Destination folder for astrometry indices. Default: {DEFAULT_DATA_FOLDER}')
@click.option('--keep-going/--no-keep-going',
              default=True,
              help='Ignore download failures and keep going to other downloads, default True.')
@click.option('--narrow-field/--no-narrow-field',
              default=False,
              help='Download narrow field indices, default False.')
@click.option('--wide-field/--no-wide-field',
              default=False,
              help='Download wide field indices, default False.')
@click.option('--verbose', is_flag=True, default=False, help='Log output to console.')
def main(folder=DEFAULT_DATA_FOLDER,
         keep_going=True,
         narrow_field=False,
         wide_field=False,
         verbose=False):

    if verbose:
        logger.enable('panoptes')
    else:
        logger.remove(0)

    if not os.path.exists(folder):
        logger.warning(f"Warning, data folder {folder} does not exist, will create.")

    # --no_narrow_field is the default, so the the args list below ignores args.no_narrow_field.
    dl = Downloader(
        data_folder=folder,
        keep_going=keep_going,
        narrow_field=narrow_field,
        wide_field=wide_field,
        verbose=verbose)

    success = dl.download_all_files()
    if success:
        logger.success(f'Downloaded all files')

    return success


if __name__ == '__main__':
    main()
