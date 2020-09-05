import time
from multiprocessing import Process

import pytest
from click.testing import CliRunner
from panoptes.utils.config.cli import config_server_cli


@pytest.fixture(scope='module')
def runner():
    return CliRunner()


@pytest.fixture(scope='module')
def dummy_cli_port():
    # Start via the cli but on a different port.
    return 12345


@pytest.fixture(scope='module')
def server(runner, config_path, dummy_cli_port):
    def start_server():
        result = runner.invoke(config_server_cli,
                               [
                                   'run',
                                   '--config-file', f'{config_path}',
                                   '--port', dummy_cli_port,
                                   '--no-save',

                                   '--ignore-local'
                               ])
        assert result.exit_code == 0

    proc = Process(target=start_server)
    proc.start()
    yield proc
    proc.kill()


def test_config_server_cli(server, runner, dummy_cli_port):
    # Let the server start.
    time.sleep(2)
    assert server.is_alive()

    result = runner.invoke(config_server_cli,
                           ['get', '--key', f'name', '--port', f'{dummy_cli_port}'])
    assert result.exit_code == 0
    # Ugh. I hate this. Logger is interfering in annoying ways.
    assert result.stdout.endswith("Testing PANOPTES Unit\n")

    result = runner.invoke(config_server_cli, ['set', '--verbose', '--port', f'{dummy_cli_port}', f'name', f'foobar'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\n{'name': 'foobar'}\n")

    result = runner.invoke(config_server_cli, ['get', '--key', f'name', '--port', f'{dummy_cli_port}'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\nfoobar\n")
