import time
from multiprocessing import Process
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from panoptes.utils.cli.main import app


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def cli_config_port():
    return 12345


# ---------------------------------------------------------------------------
# config get / set — use the session-scoped config server started by conftest
# ---------------------------------------------------------------------------


def test_config_get_name(runner):
    """config get name should return the observatory name."""
    result = runner.invoke(app, ["config", "get", "name"])
    assert result.exit_code == 0
    assert "Testing PANOPTES Unit" in result.stdout


def test_config_get_all(runner):
    """config get with no key returns the entire config as a dict."""
    result = runner.invoke(app, ["config", "get"])
    assert result.exit_code == 0
    # The result is a dict repr - check for a known top-level key.
    assert "name" in result.stdout


def test_config_get_with_default(runner):
    """config get with a missing key returns the supplied default."""
    result = runner.invoke(app, ["config", "get", "nonexistent_key_xyz", "--default", "fallback"])
    assert result.exit_code == 0
    assert "fallback" in result.stdout


def test_config_get_no_parse(runner):
    """config get --no-parse returns the raw JSON string, not a Python object."""
    result = runner.invoke(app, ["config", "get", "name", "--no-parse"])
    assert result.exit_code == 0
    # raw response wraps strings in double-quotes
    assert "Testing PANOPTES Unit" in result.stdout


def test_config_get_error(runner):
    """config get should handle a connection error from get_config gracefully."""
    with patch("panoptes.utils.cli.config.get_config", side_effect=ConnectionError("refused")):
        result = runner.invoke(app, ["config", "get", "name"])
    assert result.exit_code == 0
    # Error is printed to stderr via err_console, stdout should be empty.
    assert result.stdout == ""


def test_config_set_and_get(runner):
    """config set followed by config get should reflect the new value."""
    result = runner.invoke(app, ["config", "set", "name", "TemporaryTestName"])
    assert result.exit_code == 0
    assert "TemporaryTestName" in result.stdout

    result = runner.invoke(app, ["config", "get", "name"])
    assert result.exit_code == 0
    assert "TemporaryTestName" in result.stdout

    # Restore original value so other tests are not affected.
    runner.invoke(app, ["config", "set", "name", "Testing PANOPTES Unit"])


# ---------------------------------------------------------------------------
# config_callback — host normalisation
# ---------------------------------------------------------------------------


def test_config_callback_host_none(runner):
    """When no host is given, the client should connect to localhost."""
    with patch("panoptes.utils.cli.config.get_config", return_value="ok") as mock_get:
        result = runner.invoke(app, ["config", "get", "name"])
    assert result.exit_code == 0
    # Typer picks up PANOPTES_CONFIG_HOST from the environment (set by conftest to "localhost").
    assert mock_get.call_args.kwargs["host"] == "localhost"


def test_config_callback_host_wildcard(runner):
    """Binding to 0.0.0.0 should normalise the client host to localhost."""
    with patch("panoptes.utils.cli.config.get_config", return_value="ok") as mock_get:
        result = runner.invoke(app, ["config", "--host", "0.0.0.0", "get", "name"])
    assert result.exit_code == 0
    assert mock_get.call_args.kwargs["host"] == "localhost"


def test_config_callback_host_custom(runner):
    """An explicit host other than 0.0.0.0 should be passed through unchanged."""
    with patch("panoptes.utils.cli.config.get_config", return_value="ok") as mock_get:
        result = runner.invoke(app, ["config", "--host", "192.168.1.5", "get", "name"])
    assert result.exit_code == 0
    assert mock_get.call_args.kwargs["host"] == "192.168.1.5"


# ---------------------------------------------------------------------------
# config stop
# ---------------------------------------------------------------------------


def test_config_stop(runner):
    """config stop should call set_config to mark the server as not running."""
    with patch("panoptes.utils.cli.config.set_config") as mock_set:
        result = runner.invoke(app, ["config", "--port", "9999", "stop"])
    assert result.exit_code == 0
    mock_set.assert_called_once_with("config_server.running", False, host="localhost", port=9999)


# ---------------------------------------------------------------------------
# config run — error and timeout paths (fully mocked)
# ---------------------------------------------------------------------------


def test_config_run_server_start_error(runner, config_path):
    """config run should exit cleanly when config_server() raises an exception."""
    with patch("panoptes.utils.cli.config.server.config_server", side_effect=RuntimeError("boom")):
        result = runner.invoke(app, ["config", "run", "--config-file", f"{config_path}"])
    assert result.exit_code == 0
    assert result.exception is None


def test_config_run_startup_timeout(runner, config_path):
    """config run should terminate the process when the server never becomes ready."""
    mock_proc = MagicMock()
    mock_proc.pid = 9999

    with (
        patch("panoptes.utils.cli.config.server.config_server", return_value=mock_proc),
        patch("panoptes.utils.cli.config.server_is_running", return_value=False),
        patch("panoptes.utils.cli.config.time.sleep"),
    ):
        result = runner.invoke(
            app,
            ["config", "run", "--config-file", f"{config_path}", "--startup-timeout", "1"],
        )

    assert result.exit_code == 0
    mock_proc.terminate.assert_called()
    mock_proc.join.assert_called()


def test_config_run_normal(runner, config_path):
    """config run should start the server, wait until ready, monitor it, then stop it."""
    mock_proc = MagicMock()
    mock_proc.pid = 9999

    # Sequence: not ready → ready → still running → stopped (exits monitor loop)
    is_running_side_effects = [False, True, True, False]
    call_index = 0

    def fake_is_running(**kwargs):
        nonlocal call_index
        result = is_running_side_effects[min(call_index, len(is_running_side_effects) - 1)]
        call_index += 1
        return result

    with (
        patch("panoptes.utils.cli.config.server.config_server", return_value=mock_proc),
        patch("panoptes.utils.cli.config.server_is_running", side_effect=fake_is_running),
        patch("panoptes.utils.cli.config.time.sleep"),
    ):
        result = runner.invoke(app, ["config", "run", "--config-file", f"{config_path}"])

    assert result.exit_code == 0
    mock_proc.start.assert_called_once()
    mock_proc.terminate.assert_called()


def test_config_run_monitor_exception(runner, config_path):
    """config run should catch unexpected exceptions during monitoring gracefully."""
    mock_proc = MagicMock()
    mock_proc.pid = 9999

    # First call (startup wait): return True so we pass the readiness check.
    # Second call (monitor loop): raise an unexpected error.
    is_running_side_effects = [True, RuntimeError("unexpected")]
    call_index = 0

    def fake_is_running(**kwargs):
        nonlocal call_index
        value = is_running_side_effects[min(call_index, len(is_running_side_effects) - 1)]
        call_index += 1
        if isinstance(value, Exception):
            raise value
        return value

    with (
        patch("panoptes.utils.cli.config.server.config_server", return_value=mock_proc),
        patch("panoptes.utils.cli.config.server_is_running", side_effect=fake_is_running),
        patch("panoptes.utils.cli.config.time.sleep"),
    ):
        result = runner.invoke(app, ["config", "run", "--config-file", f"{config_path}"])

    assert result.exit_code == 0
    assert result.exception is None


@pytest.mark.skip("Not working")
def test_cli_server(runner, config_path, cli_config_port):
    def run_cli():
        result = runner.invoke(
            app,
            [
                "--verbose",
                "config",
                "run",
                "--config-file",
                f"{config_path}",
                "--port",
                cli_config_port,
                "--no-save-local",
                "--no-load-local",
            ],
        )
        assert result.exit_code == 0

    proc = Process(target=run_cli)
    proc.start()
    assert proc.pid

    # Let the serve start.
    time.sleep(5)

    result = runner.invoke(
        app,
        [
            "--verbose",
            "config",
            "--port",
            f"{cli_config_port}",
            "get",
            "name",
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.endswith("Testing PANOPTES Unit\n")

    proc.terminate()
    proc.join(30)


@pytest.mark.skip("Not working")
def test_config_server_cli(runner, cli_server, cli_config_port):
    result = runner.invoke(app, ["--verbose", "config", "--port", f"{cli_config_port}", "get", "name"])
    assert result.exit_code == 0
    assert result.stdout.endswith("Testing PANOPTES Unit\n")

    # Set the name.
    result = runner.invoke(app, ["config", "--port", f"{cli_config_port}", "set", "name", "foobar"])
    assert result.exit_code == 0
    assert result.stdout.endswith("\n{'name': 'foobar'}\n")

    # Get the name.
    result = runner.invoke(app, ["config", "--port", f"{cli_config_port}", "get", "name"])
    assert result.exit_code == 0
    assert result.stdout.endswith("\nfoobar\n")
