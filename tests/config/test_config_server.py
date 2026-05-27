"""Tests for panoptes.utils.config.store (in-memory config store)."""

from astropy import units as u

import panoptes.utils.config.store as _store_mod
from panoptes.utils.config.store import (
    _get_nested,
    _set_nested,
    get_config,
    init_config,
    reload_config,
    set_config,
)


def test_get_config_returns_dict(config_path):
    init_config(config_path)
    assert isinstance(get_config(), dict)


def test_get_config_dotted_key(config_path):
    init_config(config_path)
    assert get_config("location.horizon") == 30 * u.degree


def test_set_config_updates_value(config_path):
    init_config(config_path)
    set_config("location.horizon", 47 * u.degree)
    assert get_config("location.horizon") == 47 * u.degree


def test_set_config_returns_value(config_path):
    init_config(config_path)
    result = set_config("location.horizon", 42 * u.degree)
    assert result == 42 * u.degree


def test_get_config_default(config_path):
    init_config(config_path)
    assert get_config("nonexistent.key", default="fallback") == "fallback"
    assert get_config("nonexistent.key") is None


def test_reload_config_restores_value(config_path):
    init_config(config_path)
    original = get_config("location.horizon")
    set_config("location.horizon", 99 * u.degree, persist=False)
    assert get_config("location.horizon") == 99 * u.degree

    reload_config()
    assert get_config("location.horizon") == original


def test_get_config_list_index(config_path):
    init_config(config_path)
    assert get_config("cameras.devices[1].model") == "canon_gphoto2"


def test_get_config_none_key_returns_full_dict(config_path):
    init_config(config_path)
    cfg = get_config(None)
    assert isinstance(cfg, dict)
    assert "name" in cfg


def test_get_name(config_path):
    init_config(config_path)
    assert get_config("name") == "Testing PANOPTES Unit"


# --- _get_nested edge cases ---


def test_get_nested_empty_key_returns_dict():
    d = {"a": 1}
    assert _get_nested(d, "") is d


def test_get_nested_non_dict_intermediate():
    # "name" is a string, not a dict — navigating further returns default.
    d = {"name": "Test"}
    assert _get_nested(d, "name.sub", default="x") == "x"


def test_get_nested_list_index_out_of_bounds(config_path):
    init_config(config_path)
    assert get_config("cameras.devices[99]", default="missing") == "missing"


def test_get_nested_list_on_non_list():
    # Index accessor on a non-list value returns default.
    d = {"a": {"b": "not-a-list"}}
    assert _get_nested(d, "a.b[0]", default="nope") == "nope"


# --- _set_nested ---


def test_set_nested_creates_intermediate_dicts():
    d: dict = {}
    _set_nested(d, ["new", "deeply", "nested"], "value")
    assert d == {"new": {"deeply": {"nested": "value"}}}


def test_set_config_creates_new_nested_key(config_path):
    init_config(config_path)
    set_config("brand.new.key", "hello")
    assert get_config("brand.new.key") == "hello"


# --- auto-init behaviour ---


def test_get_config_auto_inits_when_empty(config_path, monkeypatch):
    """get_config should call init_config() automatically when the store is empty."""
    monkeypatch.setattr(_store_mod, "_CONFIG", {})
    monkeypatch.setattr(_store_mod, "_CONFIG_FILE", config_path)
    result = get_config("name")
    assert result == "Testing PANOPTES Unit"


def test_set_config_auto_inits_when_empty(config_path, monkeypatch):
    """set_config should call init_config() automatically when the store is empty."""
    monkeypatch.setattr(_store_mod, "_CONFIG", {})
    monkeypatch.setattr(_store_mod, "_CONFIG_FILE", config_path)
    set_config("name", "Auto Init Test")
    assert get_config("name") == "Auto Init Test"


# --- persist behaviour ---


def test_set_config_persists_to_file_by_default(config_path):
    """set_config should write to disk when persist=True (the default)."""
    init_config(config_path)

    set_config("name", "Persisted Name")

    # Reload from disk to confirm the write happened.
    reload_config()
    assert get_config("name") == "Persisted Name"


def test_set_config_no_persist_skips_file(config_path):
    """set_config with persist=False should NOT write to disk."""
    init_config(config_path)

    original_name = get_config("name")
    set_config("name", "In Memory Only", persist=False)
    assert get_config("name") == "In Memory Only"

    # Reload from disk — original value should be restored.
    reload_config()
    assert get_config("name") == original_name
