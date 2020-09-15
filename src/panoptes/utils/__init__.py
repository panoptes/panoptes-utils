# -*- coding: utf-8 -*-
from pkg_resources import get_distribution, DistributionNotFound

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = 'panoptes-utils'
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound

from panoptes.utils.utils import listify, get_quantity_value, altaz_to_radec, get_free_space
from panoptes.utils.time import current_time, flatten_time, wait_for_events, CountdownTimer

from loguru import logger

logger.disable('panoptes')
