import pytest
from pathlib import Path
import tempfile

from panoptes.utils import error
from panoptes.utils.library import load_c_library
from panoptes.utils.library import load_module
from panoptes.utils.utils import listify, normalize_file_input


def test_bad_load_module():
    with pytest.raises(error.NotFound):
        load_module("FOOBAR")


def test_load_c_library():
    # Called without a `path` this will use find_library to locate libc.
    libc = load_c_library("c")
    assert libc._name[:4] == "libc"

    libc = load_c_library("c", mode=None)
    assert libc._name[:4] == "libc"


def test_load_c_library_fail():
    # Called without a `path` this will use find_library to locate libc.
    with pytest.raises(error.NotFound):
        load_c_library("foobar")


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


def test_normalize_file_input_string():
    """Test normalize_file_input with string input."""
    test_path = "/path/to/file.fits"
    result = normalize_file_input(test_path)
    assert result == test_path
    assert isinstance(result, str)


def test_normalize_file_input_pathlib():
    """Test normalize_file_input with pathlib.Path input."""
    test_path = "/path/to/file.fits"
    path_obj = Path(test_path)
    result = normalize_file_input(path_obj)
    assert result == test_path
    assert isinstance(result, str)


def test_normalize_file_input_filehandle():
    """Test normalize_file_input with file handle input."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        result = normalize_file_input(tmp_file)
        assert result == tmp_file.name
        assert isinstance(result, str)


def test_normalize_file_input_mock_filehandle():
    """Test normalize_file_input with mock file handle."""

    class MockFileHandle:
        def __init__(self, name):
            self.name = name

        def read(self):
            return b"mock data"

    mock_file = MockFileHandle("/path/to/mock.fits")
    result = normalize_file_input(mock_file)
    assert result == "/path/to/mock.fits"
    assert isinstance(result, str)


def test_normalize_file_input_text_filehandle():
    """Test normalize_file_input with text file handle."""

    class MockTextFile:
        def __init__(self, name):
            self.name = name

        def write(self, data):
            pass

    mock_file = MockTextFile("/path/to/text.json")
    result = normalize_file_input(mock_file)
    assert result == "/path/to/text.json"
    assert isinstance(result, str)


def test_normalize_file_input_unsupported_type():
    """Test normalize_file_input with unsupported input type."""
    with pytest.raises(ValueError) as exc_info:
        normalize_file_input(123)

    assert "Unsupported file input type" in str(exc_info.value)
    assert "Expected str, pathlib.Path, or file-like object" in str(exc_info.value)


def test_normalize_file_input_object_without_name():
    """Test normalize_file_input with object that has read/write but no name."""

    class MockFileWithoutName:
        def read(self):
            return b"data"

    mock_file = MockFileWithoutName()
    with pytest.raises(ValueError) as exc_info:
        normalize_file_input(mock_file)

    assert "Unsupported file input type" in str(exc_info.value)
