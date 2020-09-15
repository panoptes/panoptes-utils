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

# TODO Make this better.
from panoptes.utils.utils import listify
from panoptes.utils.utils import get_quantity_value
from panoptes.utils.utils import altaz_to_radec
from panoptes.utils.utils import image_id_from_path
from panoptes.utils.utils import sequence_id_from_path
from panoptes.utils.time import current_time, flatten_time, wait_for_events, CountdownTimer

from loguru import logger

logger.disable('panoptes')
