"""Fixtures for config tests."""

import pytest

import panoptes.utils.config.store as _store_mod


@pytest.fixture(autouse=True)
def reset_config_store(config_path):
    """Reset the in-memory config store to a clean state after each test.

    This prevents test pollution when a test calls set_config().
    """
    yield
    _store_mod.init_config(config_path)
