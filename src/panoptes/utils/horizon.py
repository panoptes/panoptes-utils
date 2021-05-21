import numpy as np
from astropy import units as u

from panoptes.utils.utils import get_quantity_value

# Implicit variable used to indicate no obstruction at a given az
NO_HORIZON = None


class Obstruction(object):

    def __init__(self, points_list):
        """ An obstruction is defined by a list of alt, az pairs in clockwise ordering.
        Args:
            points_list (list): The list of points, e.g. [[alt1, az1], [alt2, az2]].
        """
        super().__init__()

        alt_list = []
        az_list = []

        if len(points_list) < 2:
            raise ValueError("Need at least two points for obstruction.")

        for p in points_list:
            if len(p) != 2:
                raise ValueError("points_list must be provided as alt/az pairs.")

            alt = get_quantity_value(p[0], u.deg)
            az = get_quantity_value(p[1], u.deg)

            if az < 0:
                az += 360

            if abs(alt) > 90:
                raise ValueError("Altitudes must be between ±90 deg.")

            if (az < 0) or (az > 360):
                raise ValueError("Azimuths must be between 0 and 360 deg.")

            alt_list.append(alt)
            az_list.append(az)

        self._alt_list = alt_list

        # Get clockwise angles between first point and all other points
        self._az0 = az_list[0]
        self._az_offset = self._get_az_offsets(az_list)

        # Ensure azimuths are ordered clockwise
        # We could sort the azimuth offsets to enforce this automatically, but safer to make user
        # explicitly provide ordered points
        if not (np.diff(self._az_offset) > 0).all():
            raise ValueError("Azimuths must be ordered clockwise.")

    def get_horizon(self, az):
        """ Get the horizon level in degrees at a given azimuth.
        Args:
            az (float or astropy.Quantity): The azimuth. If float, assumed in degrees.
        Returns:
            astropy.Quantity: The angular horizon level.
        """
        # Get azimuth offset from first point of obstruction
        az = get_quantity_value(az, u.deg)
        az_offset = self._get_az_offsets(np.array([az]))[0]

        # Return NO_HORIZON if no intersection with obstruction
        if az_offset < self._az_offset.min() or az_offset > self._az_offset.max():
            return NO_HORIZON

        alt = np.interp(az_offset, xp=self._az_offset, fp=self._alt_list) * u.deg

        return alt

    def _get_az_offsets(self, az_list):
        """ Return the angular offset between az_array and first point in obstruction.
        Args:
            az_array (np.array): The array of azimuths in degrees.
        Returns:
            np.array: The array of azimuth offsets in degrees.
        """
        az_array = np.array([get_quantity_value(az, u.deg) for az in az_list])
        az_offset = az_array - self._az0
        az_offset[az_offset < 0] += 360
        return az_offset


class Horizon(object):
    """A simple class to define some coordinate points.

    Accepts a list of lists where each list consists of two points corresponding
    to an altitude (0-90) and an azimuth (0-360).

    The list of points for a given obstruction must be in clockwise ordering.

    If azimuth is a negative number (but greater than -360) then 360 will be added to put it in the
    correct range.

    The list are points that are obstruction points beyond the default horizon.
    """

    def __init__(self, obstructions=None, default_horizon=30):
        """Create a list of horizon obstruction points.

        Each item in the `obstructions` list should be two or more points, where
        each point is an `[Alt, Az]` coordinate.

        Example:
            An example `obstruction_point` list::

                [
                [[40, 30], [40, 75]],   # From azimuth 30° to 75° there is an
                                        # obstruction that is at 40° altitude
                [[50, 180], [40, 200]], # From azimuth 180° to 200° there is
                                        # an obstruction that slopes from 50°
                                        # to 40° altitude
                ]

        Args:
            obstructions (list(list(list)), optional): A list of obstructions
                where each obstruction consists of a set of lists. The individual
                lists are alt/az pairs. Defaults to empty list in which case the
                `default_horizon` defines a flat horizon.
            default_horizon (float, optional): A default horizon to be used whenever
                there is no obstruction.

        """
        super().__init__()

        # Parse obstruction list
        if obstructions is None:
            obstructions = []
        self.obstructions = [Obstruction(obs) for obs in obstructions]

        # Add default horizon
        self._default_horizon = get_quantity_value(default_horizon, "deg") * u.deg

        # Calculate horizon at each integer azimuth
        # This is included for backwards compatibility with POCS
        self.horizon_line = np.zeros(360, dtype="float")
        for i in range(360):
            self.horizon_line[i] = self.get_horizon(i).to_value(u.deg)

    def get_horizon(self, az):
        """ Get the horizon level in degrees at a given azimuth.
        Args:
            az (float or astropy.Quantity): The azimuth. If float, assumed in degrees.
        Returns:
            astropy.Quantity: The angular horizon level.
        """
        az = get_quantity_value(az, "deg") * u.deg

        # If there are no obstructions at this az, use the default horizon
        horizon = self._default_horizon

        ob_horizons = []

        # Find obstruction horizons at this az if any exist
        for ob in self.obstructions:

            hor = ob.get_horizon(az)

            if hor != NO_HORIZON:
                ob_horizons.append(hor)

        # If there are any obstructions specified at this Az, used the one with the highest altitude
        if ob_horizons:
            horizon = max(ob_horizons)

        return horizon
