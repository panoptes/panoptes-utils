import pytest
from astropy import units as u
from ruamel.yaml.parser import ParserError
from typer.testing import CliRunner

from panoptes.utils.cli.config import app as config_app
from panoptes.utils.config.helpers import load_config, save_config
from panoptes.utils.serializers import to_yaml


def test_load_config(config_path):
    """Test basic loading"""
    conf = load_config(config_files=config_path)
    assert conf["name"] == "Testing PANOPTES Unit"


def test_bad_config(bad_config_path):
    """Test bad config file"""
    with pytest.raises(ParserError):
        load_config(config_files=bad_config_path)


def test_load_config_custom_file(tmp_path):
    """Test with a custom file"""
    temp_conf_text = dict(name="Temporary Name", location=dict(elevation="1234.56 m"))

    temp_conf_file = tmp_path / "temp_conf.yaml"
    temp_conf_local_file = tmp_path / "temp_conf_local.yaml"

    temp_conf_file.write_text(to_yaml(temp_conf_text))

    temp_conf_text["name"] = "Local Name"
    temp_conf_local_file.write_text(to_yaml(temp_conf_text))

    # Ignore the local name
    temp_config = load_config(temp_conf_file.absolute(), load_local=False)
    assert len(temp_config) == 2
    assert temp_config["name"] == "Temporary Name"
    assert temp_config["location"]["elevation"] == 1234.56 * u.m
    assert isinstance(temp_config["location"], dict)

    # Load the local directly (not via _local.yaml auto-discovery)
    temp_config = load_config(temp_conf_local_file.absolute(), load_local=False)
    assert len(temp_config) == 2
    assert temp_config["name"] == "Local Name"
    assert temp_config["location"]["elevation"] == 1234.56 * u.m
    assert isinstance(temp_config["location"], dict)

    # Legacy: auto-discovering _local.yaml emits a DeprecationWarning
    with pytest.warns(DeprecationWarning, match="_local.yaml"):
        temp_config = load_config(temp_conf_file.absolute(), parse=False)
    assert len(temp_config) == 2
    assert temp_config["name"] == "Local Name"
    assert temp_config["location"]["elevation"] == "1234.56 m"
    assert isinstance(temp_config["location"], dict)


def test_save_config_custom_file(tmp_path):
    """Test saving with a custom file saves directly to the given path."""
    temp_conf_file = tmp_path / "temp_conf.yaml"

    save_config(temp_conf_file, dict(foo=1, bar=2), overwrite=False)

    # New behaviour: file is saved exactly at the given path, not _local.yaml
    assert temp_conf_file.exists()

    temp_config = load_config(temp_conf_file, load_local=False)
    assert temp_config["foo"] == 1

    with pytest.raises(FileExistsError):
        save_config(temp_conf_file, dict(foo=2, bar=2), overwrite=False)

    save_config(temp_conf_file, dict(foo=2, bar=2), overwrite=True)
    temp_config = load_config(temp_conf_file, load_local=False)
    assert temp_config["foo"] == 2


def test_save_config_local_file_deprecated(tmp_path):
    """Saving to a _local.yaml path emits a DeprecationWarning."""
    temp_conf_local_file = tmp_path / "temp_conf_local.yaml"

    assert temp_conf_local_file.exists() is False
    with pytest.warns(DeprecationWarning, match="_local.yaml"):
        save_config(temp_conf_local_file, dict(foo=1, bar=2), overwrite=False)
    assert temp_conf_local_file.exists()


def test_save_config_default_path(tmp_path, monkeypatch):
    """save_config(None, ...) writes to $PANOPTES_CONFIG_FILE when set."""
    dest = tmp_path / "config.yaml"
    monkeypatch.setenv("PANOPTES_CONFIG_FILE", str(dest))
    save_config(None, dict(foo=42))
    assert dest.exists()
    cfg = load_config(dest, load_local=False)
    assert cfg["foo"] == 42


# ---------------------------------------------------------------------------
# load_config default-resolution tests
# ---------------------------------------------------------------------------


def test_load_config_env_var(tmp_path, monkeypatch):
    """$PANOPTES_CONFIG_FILE is used when config_files=None."""
    dest = tmp_path / "config.yaml"
    dest.write_text("name: from_env\n")
    monkeypatch.setenv("PANOPTES_CONFIG_FILE", str(dest))
    cfg = load_config(load_local=False)
    assert cfg["name"] == "from_env"


def test_load_config_default_path(tmp_path, monkeypatch):
    """~/.panoptes/config.yaml is used when env var is not set and file exists."""
    monkeypatch.delenv("PANOPTES_CONFIG_FILE", raising=False)
    fake_default = tmp_path / "config.yaml"
    fake_default.write_text("name: from_default\n")
    monkeypatch.setattr("panoptes.utils.config.helpers.DEFAULT_CONFIG_PATH", fake_default)
    cfg = load_config(load_local=False)
    assert cfg["name"] == "from_default"


def test_load_config_no_file_warns(tmp_path, monkeypatch):
    """load_config(None) with no resolvable file returns empty dict and logs a warning."""
    monkeypatch.delenv("PANOPTES_CONFIG_FILE", raising=False)
    nonexistent = tmp_path / "nonexistent.yaml"
    monkeypatch.setattr("panoptes.utils.config.helpers.DEFAULT_CONFIG_PATH", nonexistent)
    cfg = load_config(load_local=False)
    assert cfg == {}


# ---------------------------------------------------------------------------
# config init CLI tests
# ---------------------------------------------------------------------------


def test_config_init_creates_file(tmp_path):
    runner = CliRunner()
    dest = tmp_path / "config.yaml"
    result = runner.invoke(config_app, ["init", "--output", str(dest)])
    assert result.exit_code == 0, result.output
    assert dest.exists()
    # Basic sanity: template contains pan_id key
    assert "pan_id" in dest.read_text()


def test_config_init_refuses_overwrite_without_force(tmp_path):
    runner = CliRunner()
    dest = tmp_path / "config.yaml"
    dest.write_text("existing: true\n")
    result = runner.invoke(config_app, ["init", "--output", str(dest)])
    assert result.exit_code != 0
    assert "existing: true" in dest.read_text()  # file unchanged


def test_config_init_force_overwrites(tmp_path):
    runner = CliRunner()
    dest = tmp_path / "config.yaml"
    dest.write_text("existing: true\n")
    result = runner.invoke(config_app, ["init", "--output", str(dest), "--force"])
    assert result.exit_code == 0, result.output
    assert "pan_id" in dest.read_text()
