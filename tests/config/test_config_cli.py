import pytest
from click.testing import CliRunner
from panoptes.utils.config.cli import config_server_cli


@pytest.fixture(scope='module')
def runner():
    return CliRunner()


@pytest.fixture(scope='module')
def server(runner, config_path):
    result = runner.invoke(config_server_cli,
                           [
                               '--verbose',
                               'run',
                               '--config-file', f'{config_path}',
                               '--port', 12345,
                               '--no-save',
                               '--ignore-local'
                           ])
    assert result.exit_code == 0


def test_config_server_cli(runner, config_port):
    result = runner.invoke(config_server_cli, ['get', '--key', f'name', '--port', f'{config_port}'])
    assert result.exit_code == 0
    # Ugh. I hate this. Logger is interfering in annoying ways.
    assert result.stdout.endswith("Testing PANOPTES Unit\n")

    # Set the name
    result = runner.invoke(config_server_cli, ['set', '--port', f'{config_port}', f'name', f'foobar'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\n{'name': 'foobar'}\n")

    # Test using --key
    result = runner.invoke(config_server_cli, ['get', '--key', f'name', '--port', f'{config_port}'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\nfoobar\n")

    # Set the name
    result = runner.invoke(config_server_cli, ['set', '--port', f'{config_port}', f'name', f'raboof'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\n{'name': 'raboof'}\n")

    # Test without key
    result = runner.invoke(config_server_cli, ['get', f'name', '--port', f'{config_port}'])
    assert result.exit_code == 0
    assert result.stdout.endswith("\nraboof\n")
