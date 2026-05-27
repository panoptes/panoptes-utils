"""Fixtures for config tests."""

import shutil

import pytest

import panoptes.utils.config.store as _store_mod


@pytest.fixture()
def config_path(tmp_path):
    """Return a per-test writable copy of tests/testing.yaml.

    Overrides the session-scoped fixture from the root conftest so that
    set_config(persist=True) writes don't contaminate other tests.
    """
    src = "tests/testing.yaml"
    dest = tmp_path / "testing.yaml"
    shutil.copy(src, dest)
    return dest


@pytest.fixture(autouse=True)
def reset_config_store(config_path):
    """Reset the in-memory config store to a clean state after each test."""
    yield
    _store_mod.init_config(config_path)
