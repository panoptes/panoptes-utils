import warnings
from unittest.mock import MagicMock, patch

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


def test_config_cli_get_error_path(runner, config_path):
    """get command exits with code 1 when get_config raises."""
    with patch("panoptes.utils.cli.config.get_config", side_effect=RuntimeError("boom")):
        result = runner.invoke(app, ["get", "any.key", "--config-file", str(config_path)])
    assert result.exit_code == 1
    assert "Error" in result.stdout


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


# --- deprecated run / stop commands ---


def test_run_emits_deprecation_and_exits_on_server_error(runner, config_path):
    """run command emits a DeprecationWarning and exits cleanly when server fails to start."""
    import sys

    mock_server = MagicMock()
    mock_server.config_server.side_effect = RuntimeError("no server")

    with patch.dict(sys.modules, {"panoptes.utils.config.server": mock_server}):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = runner.invoke(app, ["run", "--config-file", str(config_path)])

    assert result.exit_code == 1
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_run_exits_when_server_import_fails(runner, config_path):
    """run command exits with code 1 when server dependencies are not installed."""
    import sys

    with patch.dict(sys.modules, {"panoptes.utils.config.server": None}):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = runner.invoke(app, ["run", "--config-file", str(config_path)])

    assert result.exit_code == 1


def test_run_server_starts_and_exits_when_process_dies(runner, config_path):
    """run command exits normally once the server process stops running."""
    import sys

    mock_process = MagicMock()
    mock_process.pid = 99999
    # Calls: [main-loop-iter1, main-loop-exit, finally-check]
    mock_process.is_alive.side_effect = [True, False, False]

    mock_server = MagicMock()
    mock_server.config_server.return_value = mock_process

    mock_client = MagicMock()
    mock_client.server_is_running.return_value = True

    with patch.dict(
        sys.modules,
        {
            "panoptes.utils.config.server": mock_server,
            "panoptes.utils.config.client": mock_client,
        },
    ):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = runner.invoke(app, ["run", "--config-file", str(config_path), "--heartbeat", "0.001"])

    assert result.exit_code == 0


def test_stop_emits_deprecation(runner):
    """stop command emits a DeprecationWarning."""
    with patch("panoptes.utils.config.client.set_config"):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = runner.invoke(app, ["stop"])

    assert result.exit_code == 0
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


# --- config init command ---


def test_config_init_auto_detects_single_local_yaml(runner, tmp_path, monkeypatch):
    """init command auto-detects a single *_local.yaml in cwd."""
    monkeypatch.chdir(tmp_path)
    local_yaml = tmp_path / "pocs_local.yaml"
    local_yaml.write_text("name: My Unit\n")
    dest = tmp_path / "config_out.yaml"

    result = runner.invoke(app, ["init", "--output", str(dest)])

    assert result.exit_code == 0, result.output
    assert "Auto-detected" in result.stdout
    assert dest.exists()


def test_config_init_multiple_local_yaml_exits(runner, tmp_path, monkeypatch):
    """init command exits with code 1 when multiple *_local.yaml files are found."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a_local.yaml").write_text("x: 1\n")
    (tmp_path / "b_local.yaml").write_text("y: 2\n")
    dest = tmp_path / "config_out.yaml"

    result = runner.invoke(app, ["init", "--output", str(dest)])

    assert result.exit_code == 1
    assert "Multiple" in result.stdout
