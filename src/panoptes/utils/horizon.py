import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from astropy import units as u

from panoptes.utils.utils import get_quantity_value


class Obstruction(object):

    def __init__(self, points_list):
        """ An obstruction is defined by a list of alt, az pairs in clockwise ordering.
        Args:
            points_list (list): The list of points, e.g. [[alt1, az1], [alt2, az2]].
        """
        super().__init__()

        if any([len(p) != 2 for p in points_list]):
            raise ValueError("points_list must be provided as alt/az pairs.")

        alt_array = np.array([get_quantity_value(p[0], u.deg) for p in points_list])

        if any([abs(_) > 90 for _ in alt_array]):
            raise ValueError("Alititudes must be between ±90 deg.")

        # The az array is defined as being clockwise
        az_array = np.array([get_quantity_value(p[1], u.deg) for p in points_list])
        az_array[az_array < 0] += 360

        if any([abs(_) < 0 for _ in az_array]):
            raise ValueError("Azimuths must be >=0 deg.")
        if any([abs(_) > 360 for _ in az_array]):
            raise ValueError("Azimuths must be <360 deg.")

        self._az0 = az_array[0]

        # Get angles between first point and all other points
        az_normed = self._normalise_az(az_array)

        # Linearly interpolate altitude over angles
        self._interp = interp1d(az_normed, alt_array, kind="linear", bounds_error=False,
                                fill_value=0)

    def get_horizon(self, az):
        """ Get the horizon level in degrees at a given azimuth.
        Args:
            az (float or astropy.Quantity): The azimuth. If float, assumed in degrees.
        Returns:
            astropy.Quantity: The angular horizon level.
        """
        az = get_quantity_value(az, u.deg)
        az_normed = self._normalise_az(np.array([az]))[0]
        return self._interp(az_normed) * u.deg

    def _normalise_az(self, az_array):
        """ Return the angular offset between az_array and first point in obstruction.
        Args:
            az_array (np.array): The array of azimuths in degrees.
        Returns:
            np.array: The array of azimuth offsets in degrees.
        """
        az_normed = az_array - self._az0
        az_normed[az_normed < 0] += 360
        return az_normed


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
        self.obstructions = [Obstruction(_) for _ in obstructions]

        # Add default horizon
        self._default_horizon = get_quantity_value(default_horizon, "deg") * u.deg

        # Calculate horizon at each integer azimuth
        # This is included for backwards compatibility with POCS
        self.horizon_line = np.zeros(360, dtype="float")
        for i, az in enumerate(self.horizon_line):
            self.horizon_line[i] = self.get_horizon(az).to_value(u.deg)

    def get_horizon(self, az):
        """ Get the horizon level in degrees at a given azimuth.
        Args:
            az (float or astropy.Quantity): The azimuth. If float, assumed in degrees.
        Returns:
            astropy.Quantity: The angular horizon level.
        """
        az = get_quantity_value(az, "deg") * u.deg

        horizon = self._default_horizon

        for obstruction in self.obstructions:
            horizon = max(horizon, obstruction.get_horizon(az))

        return horizon

    def make_plot(self):
        """ Make plot of horizon in alt / az coordinates. """
        xx = np.linspace(0, 360, 360)
        yy = [self.get_horizon(x).to_value(u.deg) for x in xx]

        fig, ax = plt.subplots()
        ax.plot(xx, yy, "k-")

        ax.set_xlabel("Az [deg]")
        ax.set_ylabel("Alt [deg]")

        return fig, ax
