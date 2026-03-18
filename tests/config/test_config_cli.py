import time
from multiprocessing import Process

import pytest
from typer.testing import CliRunner

from panoptes.utils.cli.config import app


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def cli_config_port():
    return 12345


def test_cli_server(runner, config_path, cli_config_port):
    def run_cli():
        # Typer/Click runner handles some of the sys.argv but for a full server 
        # subprocess we use the runner.invoke which is usually synchronous.
        # Here we are running it in a Process, which can be tricky with CliRunner.
        result = runner.invoke(
            app,
            [
                "run",
                "--config-file",
                f"{config_path}",
                "--port",
                str(cli_config_port),
                "--no-save-local",
                "--no-load-local",
            ],
        )
        assert result.exit_code == 0

    proc = Process(target=run_cli)
    proc.start()
    assert proc.pid

    # Let the server start.
    time.sleep(5)

    try:
        result = runner.invoke(
            app,
            [
                "get",
                "name",
                "--port",
                str(cli_config_port),
            ],
        )
        assert result.exit_code == 0
        assert "Testing PANOPTES Unit" in result.stdout
    finally:
        proc.terminate()
        proc.join(30)


def test_config_server_cli(runner):
    # Use the default port (8765) from conftest.py
    cli_config_port = 8765
    result = runner.invoke(app, ["get", "name", "--port", str(cli_config_port)])
    assert result.exit_code == 0
    assert "Testing PANOPTES Unit" in result.stdout

    # Set the name.
    result = runner.invoke(app, ["set", "name", "foobar", "--port", str(cli_config_port)])
    assert result.exit_code == 0
    assert "foobar" in result.stdout

    # Get the name back.
    result = runner.invoke(app, ["get", "name", "--port", str(cli_config_port)])
    assert result.exit_code == 0
    assert "foobar" in result.stdout
