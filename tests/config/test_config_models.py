"""Tests for ConfigWatcher and config models."""

import time

import pytest

from panoptes.utils.config import ConfigWatcher, UnitConfig, load_config
from panoptes.utils.config.models import DatabaseConfig, DirectoriesConfig, LocationConfig

# ---------------------------------------------------------------------------
# UnitConfig / model tests
# ---------------------------------------------------------------------------


def test_load_config_returns_dict_by_default(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("name: test\npan_id: PAN001\n")
    result = load_config(cfg_file)
    assert isinstance(result, dict)
    assert result["name"] == "test"


def test_load_config_with_model(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("name: test\npan_id: PAN001\n")
    result = load_config(cfg_file, model=UnitConfig)
    assert isinstance(result, UnitConfig)
    assert result.name == "test"
    assert result.pan_id == "PAN001"


def test_unit_config_from_testing_yaml():
    cfg = load_config("tests/testing.yaml", model=UnitConfig)
    assert cfg.pan_id == "PAN000"
    assert cfg.location is not None
    assert cfg.location.timezone == "US/Hawaii"


def test_location_config_accepts_strings():
    loc = LocationConfig(
        latitude="19.54 deg",
        longitude="-155.58 deg",
        elevation="3400 m",
    )
    import astropy.units as u

    assert loc.latitude.to(u.deg).value == pytest.approx(19.54)
    assert loc.elevation.to(u.m).value == pytest.approx(3400.0)


def test_location_config_rejects_wrong_units_for_angle():
    import astropy.units as u
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="degrees"):
        LocationConfig(latitude=3400 * u.m, longitude="-155.58 deg", elevation="3400 m")


def test_location_config_rejects_wrong_units_for_elevation():
    import astropy.units as u
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="meters"):
        LocationConfig(latitude="19.54 deg", longitude="-155.58 deg", elevation=19.54 * u.deg)

    import astropy.units as u

    loc = LocationConfig(
        latitude=19.54 * u.deg,
        longitude=-155.58 * u.deg,
        elevation=3400.0 * u.m,
    )
    assert loc.latitude.value == pytest.approx(19.54)


def test_unit_config_earth_location():
    cfg = load_config("tests/testing.yaml", model=UnitConfig)
    el = cfg.earth_location
    assert el is not None
    # Rough sanity check: Hawaii is at negative longitude
    assert el.lon.deg == pytest.approx(-155.58, abs=0.1)


def test_unit_config_no_location():
    cfg = UnitConfig(name="bare")
    assert cfg.earth_location is None


def test_directories_config_defaults():
    dirs = DirectoriesConfig()
    assert dirs.images == "images"
    assert dirs.data == "data"


def test_database_config_defaults():
    db = DatabaseConfig()
    assert db.type == "file"
    assert db.name == "panoptes"


def test_unit_config_extra_keys_allowed():
    """POCS-specific keys should not cause validation errors."""
    cfg = UnitConfig(name="test", mount={"brand": "ioptron"}, cameras={"auto_detect": True})
    assert cfg.name == "test"


# ---------------------------------------------------------------------------
# ConfigWatcher tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def config_file(tmp_path):
    """A temporary YAML config file."""
    f = tmp_path / "config.yaml"
    f.write_text("name: initial\n")
    return f


def test_watcher_fires_callback_on_change(config_file):
    received = []

    with ConfigWatcher(config_file, load_local=False) as watcher:
        watcher.register(None, received.append)
        config_file.write_text("name: changed\n")
        _wait_for(lambda: len(received) > 0)

    assert received[-1]["name"] == "changed"


def test_watcher_fires_per_key_callback(config_file):
    received = []

    with ConfigWatcher(config_file, load_local=False) as watcher:
        watcher.register("name", received.append)
        config_file.write_text("name: updated\n")
        _wait_for(lambda: len(received) > 0)

    assert received[-1]["name"] == "updated"


def test_watcher_does_not_fire_for_unrelated_key(config_file):
    """Callback registered for 'location' should not fire when only 'name' changes."""
    received = []

    with ConfigWatcher(config_file, load_local=False) as watcher:
        watcher.register("location", received.append)
        config_file.write_text("name: changed\n")
        time.sleep(0.4)

    assert len(received) == 0


def test_watcher_callback_exception_does_not_break_watcher(config_file):
    """A raising callback should not prevent subsequent callbacks from firing."""
    good_received = []

    def bad_callback(cfg):
        raise RuntimeError("intentional error")

    with ConfigWatcher(config_file, load_local=False) as watcher:
        watcher.register(None, bad_callback)
        watcher.register(None, good_received.append)
        config_file.write_text("name: changed\n")
        _wait_for(lambda: len(good_received) > 0)

    assert len(good_received) > 0


def test_watcher_context_manager_stops_on_exit(config_file):
    with ConfigWatcher(config_file, load_local=False) as watcher:
        assert watcher._observer is not None
    assert watcher._observer is None


def test_watcher_missing_watchdog(config_file, monkeypatch):
    """ConfigWatcher raises a clear ImportError when watchdog is missing."""
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name.startswith("watchdog"):
            raise ImportError("No module named 'watchdog'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    watcher = ConfigWatcher(config_file)
    with pytest.raises(ImportError, match="watchdog is required"):
        watcher.start()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wait_for(condition, timeout: float = 2.0, interval: float = 0.05) -> None:
    """Poll until condition() is True or timeout is reached."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(interval)
    raise TimeoutError("Condition not met within timeout")
