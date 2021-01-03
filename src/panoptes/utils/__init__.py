# -*- coding: utf-8 -*-
from pkg_resources import DistributionNotFound
from pkg_resources import get_distribution

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = 'panoptes-utils'
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:  # pragma: no cover
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound

# TODO Make this better.

from loguru import logger

logger.disable('panoptes')
