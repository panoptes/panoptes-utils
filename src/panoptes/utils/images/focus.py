import numpy as np
from typing import Callable


def focus_metric(
    data: np.ndarray, merit_function: str | Callable = "vollath_F4", **kwargs
) -> float:  # noqa: ANN003
    """Compute the focus metric.

    Computes a focus metric on the given data using a supplied merit function.
    The merit function can be passed either as the name of the function (must be
    defined in this module) or as a callable object. Additional keyword arguments
    for the merit function can be passed as keyword arguments to this function.

    Args:
        data (numpy array) -- 2D array to calculate the focus metric for.
        merit_function (str/callable) -- Name of merit function (if in
            panoptes.utils.images) or a callable object.

    Returns:
        scalar: result of calling merit function on data
    """
    if isinstance(merit_function, str):
        try:
            merit_function = globals()[merit_function]
        except KeyError:
            raise KeyError(f"Focus merit function {merit_function} not found.")

    return merit_function(data, **kwargs)


def vollath_F4(data: np.ndarray, axis: str | None = None) -> float:
    """Compute F4 focus metric

    Computes the F_4 focus metric as defined by Vollath (1998) for the given 2D
    numpy array. The metric can be computed in the y axis, x axis, or the mean of
    the two (default).

    Arguments:
        data (numpy array) -- 2D array to calculate F4 on.
        axis (str, optional, default None) -- Which axis to calculate F4 in. Can
            be 'Y'/'y', 'X'/'x' or None, which will calculate the F4 value for
            both axes and return the mean.

    Returns:
        float64: Calculated F4 value for y, x axis or both
    """
    # This calculation is prone to integer overflow if data is an integer type
    # so convert to float64 before doing anything else.
    data = data.astype(np.float64)

    def _vollath_F4_y() -> float:
        """Calculate Vollath F4 focus metric along Y axis.

        Returns:
            float: Focus metric value.
        """
        A1 = (data[1:] * data[:-1]).mean()
        A2 = (data[2:] * data[:-2]).mean()
        return A1 - A2

    def _vollath_F4_x() -> float:
        """Calculate Vollath F4 focus metric along X axis.

        Returns:
            float: Focus metric value.
        """
        A1 = (data[:, 1:] * data[:, :-1]).mean()
        A2 = (data[:, 2:] * data[:, :-2]).mean()
        return A1 - A2

    if str(axis).lower() == "y":
        return _vollath_F4_y()
    elif str(axis).lower() == "x":
        return _vollath_F4_x()
    elif not axis:
        return (_vollath_F4_y() + _vollath_F4_x()) / 2
    else:
        raise ValueError(f"axis must be one of 'Y', 'y', 'X', 'x' or None, got {axis}!")
