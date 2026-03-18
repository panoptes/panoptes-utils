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


@pytest.mark.skip("Not working")
def test_cli_server(runner, config_path, cli_config_port):
    def run_cli():
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

    proc.terminate()
    proc.join(30)


@pytest.mark.skip("Not working")
def test_config_server_cli(runner, cli_server, cli_config_port):
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
