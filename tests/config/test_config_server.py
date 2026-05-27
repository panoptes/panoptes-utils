"""Tests for panoptes.utils.config.store (in-memory config store)."""

from astropy import units as u

from panoptes.utils.config.store import get_config, init_config, reload_config, set_config


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
    set_config("location.horizon", 99 * u.degree)
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
