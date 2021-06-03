import time
from multiprocessing import Process

import pytest
from click.testing import CliRunner
from panoptes.utils.config.cli import config_server_cli


@pytest.fixture(scope='module')
def runner():
    return CliRunner()


@pytest.fixture(scope='module')
def cli_config_port():
    return 12345


@pytest.mark.skip("Not working")
def test_cli_server(runner, config_path, cli_config_port):
    def run_cli():
        result = runner.invoke(config_server_cli,
                               [
                                   '--verbose',
                                   'run',
                                   '--config-file', f'{config_path}',
                                   '--port', cli_config_port,
                                   '--no-save-local',
                                   '--no-load-local'
                               ])
        assert result.exit_code == 0

    proc = Process(target=run_cli)
    proc.start()
    assert proc.pid

    # Let the serve start.
    time.sleep(5)

    result = runner.invoke(config_server_cli,
                           ['--verbose', '--port', f'{cli_config_port}', 'get', 'name', ])
    assert result.exit_code == 0
    # Ugh. I hate this. Logger is interfering in annoying ways.
    assert result.stdout.endswith("Testing PANOPTES Unit\n")

    proc.terminate()
    proc.join(30)


@pytest.mark.skip("Not working")
def test_config_server_cli(runner, cli_server, cli_config_port):
    result = runner.invoke(config_server_cli,
                           ['--verbose', '--port', f'{cli_config_port}', 'get', f'name'])
    assert result.exit_code == 0
    # Ugh. I hate this. Logger is interfering in annoying ways.
    assert result.stdout.endswith("Testing PANOPTES Unit\n")

    # Set the name.
    result = runner.invoke(config_server_cli,
                           ['--port', f'{cli_config_port}', 'set', 'name', 'foobar'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\n{'name': 'foobar'}\n")

    # Get the name.
    result = runner.invoke(config_server_cli, ['--port', f'{cli_config_port}', 'get', 'name'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\nfoobar\n")
