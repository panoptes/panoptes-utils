import pytest
from typer.testing import CliRunner

from panoptes.utils.cli.config import app


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_config_cli_get(runner, config_path, tmp_path):
    """get command reads from the config file."""
    result = runner.invoke(app, ["get", "name", "--config-file", str(config_path)])
    assert result.exit_code == 0, result.output
    assert "Testing PANOPTES Unit" in result.stdout


def test_config_cli_get_dotted_key(runner, config_path):
    """get command supports dotted-key notation."""
    result = runner.invoke(app, ["get", "location.horizon", "--config-file", str(config_path)])
    assert result.exit_code == 0, result.output
    assert "30" in result.stdout


def test_config_cli_get_missing_key_returns_default(runner, config_path):
    """get command returns the default when key is not found."""
    result = runner.invoke(
        app, ["get", "nonexistent.key", "--config-file", str(config_path), "--default", "42"]
    )
    assert result.exit_code == 0, result.output
    assert "42" in result.stdout


def test_config_cli_get_no_key_returns_full_config(runner, config_path):
    """get with no key returns the full config dict."""
    result = runner.invoke(app, ["get", "--config-file", str(config_path)])
    assert result.exit_code == 0, result.output
    assert "Testing PANOPTES Unit" in result.stdout


def test_config_cli_set_and_get(runner, tmp_path, config_path):
    """set command updates the value and saves it to a temp file."""
    from panoptes.utils.config.helpers import load_config
    from panoptes.utils.serializers import to_yaml

    # Make a mutable copy of the test config in tmp_path.
    original = load_config(config_path, load_local=False)
    temp_config = tmp_path / "config.yaml"
    with temp_config.open("w") as fh:
        to_yaml(original, stream=fh)

    result = runner.invoke(app, ["set", "name", "My Test Unit", "--config-file", str(temp_config)])
    assert result.exit_code == 0, result.output
    assert "My Test Unit" in result.stdout

    # Verify the file was updated.
    updated = load_config(temp_config, load_local=False)
    assert updated["name"] == "My Test Unit"


def test_config_cli_set_no_persist(runner, tmp_path, config_path):
    """set --no-persist updates in memory but does not touch the file."""
    from panoptes.utils.config.helpers import load_config
    from panoptes.utils.serializers import to_yaml

    original = load_config(config_path, load_local=False)
    temp_config = tmp_path / "config.yaml"
    with temp_config.open("w") as fh:
        to_yaml(original, stream=fh)

    result = runner.invoke(
        app, ["set", "name", "In Memory Only", "--config-file", str(temp_config), "--no-persist"]
    )
    assert result.exit_code == 0, result.output

    # File should be unchanged.
    on_disk = load_config(temp_config, load_local=False)
    assert on_disk["name"] == original["name"]
