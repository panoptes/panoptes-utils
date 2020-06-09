import click

from ..logging import logger
from .server import config_server
from .client import get_config, set_config


@click.group()
@click.option('--verbose/--no-verbose', help='Turn on panoptes logger for utils, default False')
def config_server_cli(verbose=False):
    if verbose:
        logger.enable('panoptes')


@click.command('run')
@click.argument('config-file')
@click.option('--host', default='localhost', help='The config server IP address or host name, default 0.0.0.0')
@click.option('--port', default='6563', help='The config server port, default 6563')
@click.option('--save/--no-save', default=True, help='If the set values should be saved permanently, default True')
@click.option('--ignore-local/--no-ignore-local', default=False,
              help='Ignore the local config files, default False. Mostly for testing.')
@click.option('--debug/--no-debug', default=False)
def run(config_file, host='localhost', port='6563', save=True, ignore_local=False, debug=False):
    """Runs the config server with command line options.

    This function is installed as an entry_point for the module, accessible
    at `panoptes-config-server`.
    """
    server_process = config_server(
        config_file,
        host=host,
        port=port,
        ignore_local=ignore_local,
        auto_save=save,
        debug=debug,
        auto_start=False
    )

    try:
        print(f'Starting config server. Ctrl-c to stop')
        server_process.start()
    except KeyboardInterrupt:
        logger.info(f'Config server interrupted, shutting down {server_process.pid}')
        server_process.terminate()


@click.command('get')
@click.option('--key', default=None, help='The config key. Use dotted notation for nested entries.')
@click.option('--host', default='localhost', help='The config server IP address or host name, default localhost')
@click.option('--port', default='6563', help='The config server port, default 6563')
@click.option('--parse/--no-parse', default=True, help='If results should be parsed into object')
@click.option('--default', help='The default to return if not key is found, default None')
def config_getter(key=None, host='localhost', port='6563', parse=True, default=None):
    logger.debug(f'Getting config {key=}')
    config_entry = get_config(key=key, host=host, port=port, parse=parse, default=default)
    click.echo(config_entry)


@click.command('set')
@click.argument('key')
@click.argument('new_value')
@click.option('--host', default='localhost', help='The config server IP address or host name, default localhost')
@click.option('--port', default='6563', help='The config server port, default 6563')
@click.option('--parse/--no-parse', default=True, help='If results should be parsed into object.')
def config_setter(key, new_value, host='localhost', port='6563', parse=True):
    logger.debug(f'Setting config {key=} {new_value=}')
    config_entry = set_config(key, new_value, host=host, port=port, parse=parse)
    click.echo(config_entry)


config_server_cli.add_command(run)
config_server_cli.add_command(config_setter)
config_server_cli.add_command(config_getter)
