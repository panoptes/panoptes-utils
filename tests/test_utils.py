import pytest

from panoptes.utils import error
from panoptes.utils.library import load_c_library
from panoptes.utils.library import load_module
from panoptes.utils.utils import listify


def test_bad_load_module():
    with pytest.raises(error.NotFound):
        load_module('FOOBAR')


def test_load_c_library():
    # Called without a `path` this will use find_library to locate libc.
    libc = load_c_library('c')
    assert libc._name[:4] == 'libc'

    libc = load_c_library('c', mode=None)
    assert libc._name[:4] == 'libc'


def test_load_c_library_fail():
    # Called without a `path` this will use find_library to locate libc.
    with pytest.raises(error.NotFound):
        load_c_library('foobar')


def test_listify():
    assert listify(12) == [12]
    assert listify([1, 2, 3]) == [1, 2, 3]


def test_empty_listify():
    assert listify(None) == []


def test_listfy_dicts():
    d = dict(a=42)

    d_vals = d.values()
    d_keys = d.keys()

    assert isinstance(listify(d_vals), list)
    assert listify(d_vals) == list(d_vals)

    assert isinstance(listify(d_keys), list)
    assert listify(d_keys) == list(d_keys)

    assert isinstance(listify(d), list)
    assert listify(d) == list(d_vals)
