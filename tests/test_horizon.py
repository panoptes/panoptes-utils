import pytest
import numpy as np
import random

from panoptes.utils.horizon import Horizon


def test_normal():
    hp = Horizon(obstructions=[
        [[20, 10], [40, 70]]
    ])
    assert isinstance(hp, Horizon)

    hp2 = Horizon(obstructions=[
        [[40, 45], [50, 50], [60, 45]]
    ])
    assert isinstance(hp2, Horizon)

    hp3 = Horizon()
    assert isinstance(hp3, Horizon)


def test_bad_length_tuple():
    with pytest.raises(ValueError):
        Horizon(obstructions=[
            [[20], [40, 70]]
        ])


def test_bad_length_list():
    with pytest.raises(ValueError):
        Horizon(obstructions=[
            [[40, 70]]
        ])


def test_bad_string():
    with pytest.raises(TypeError):
        Horizon(obstructions=[
            [["x", 10], [40, 70]]
        ])


def test_too_many_points():
    with pytest.raises(ValueError):
        Horizon(obstructions=[[[120, 60, 300]]])


def test_numpy_ints():
    range_length = 360
    points = [list(list(a) for a in zip(
        [random.randrange(15, 50) for _ in range(range_length)],  # Random height
        np.arange(1, range_length, 25)  # Set azimuth
    ))]
    points
    assert isinstance(Horizon(points), Horizon)


def test_good_negative_az():
    hp = Horizon(obstructions=[
        [[50, -10], [45, -20]]
    ])
    assert isinstance(hp, Horizon)

    hp2 = Horizon(obstructions=[
        [[10, -181], [20, -190]]
    ])
    assert isinstance(hp2, Horizon)
