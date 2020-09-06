import click

from .client import get_config, set_config
from .server import config_server
from ..logging import logger


@click.group()
@click.option('--verbose/--no-verbose',
              envvar='PANOPTES_DEBUG',
              help='Turn on panoptes logger for utils, default False')
def config_server_cli(verbose=False):
    if verbose:
        logger.enable('panoptes')


@click.command('run')
@click.option('--config-file',
              default=None,
              envvar='PANOPTES_CONFIG_FILE',
              help='The yaml config file to load.'
              )
@click.option('--host',
              default=None,
              envvar='PANOPTES_CONFIG_HOST',
              help='The config server IP address or host name. First'
                   'checks cli argument, then PANOPTES_CONFIG_HOST, then localhost.')
@click.option('--port',
              default=None,
              envvar='PANOPTES_CONFIG_PORT',
              help='The config server port. First checks cli argument, '
                   'then PANOPTES_CONFIG_PORT, then 6563')
@click.option('--save/--no-save',
              default=True,
              help='If the set values should be saved permanently, default True.')
@click.option('--ignore-local/--no-ignore-local',
              default=False,
              help='Ignore the local config files, default False. Mostly for testing.')
@click.option('--debug/--no-debug',
              default=False)
def run(config_file=None, host=None, port=None, save=True, ignore_local=False, debug=False):
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
        server_process.join()
    except KeyboardInterrupt:
        logger.info(f'Config server interrupted, shutting down {server_process.pid}')
        server_process.terminate()
    except Exception as e:  # pragma: no cover
        logger.error(f'Unable to start config server {e!r}')


@click.command('get')
@click.argument('key', nargs=-1)
@click.option('--host',
              default=None,
              envvar='PANOPTES_CONFIG_HOST',
              help='The config server IP address or host name. First'
                   'checks cli argument, then PANOPTES_CONFIG_HOST, then localhost.')
@click.option('--port',
              default=None,
              envvar='PANOPTES_CONFIG_PORT',
              help='The config server port. First checks cli argument, '
                   'then PANOPTES_CONFIG_PORT, then 6563')
@click.option('--parse/--no-parse',
              default=False,
              help='If results should be parsed into object, default False. '
                   'Not that since this is returning to stdout you usually do not want to parse.')
@click.option('--default',
              help='The default to return if not key is found, default None')
def config_getter(key, host='localhost', port='6563', parse=True, default=None):
    """Get an item from the config server by key name, using dotted notation (e.g. 'location.elevation')

    If no key is given, returns the entire config.
    """
    try:
        # The nargs=-1 makes this a tuple.
        key = key[0]
    except IndexError:
        key = None
    logger.debug(f'Getting config {key=}')
    try:
        config_entry = get_config(key=key, host=host, port=port, parse=parse, default=default)
    except Exception as e:
        logger.error(f'Error while trying to get config: {e!r}')
        click.secho(f'Error while trying to get config: {e!r}', fg='red')
    else:
        logger.debug(f'Config server response: {config_entry=}')
        click.echo(config_entry)

    # logger.warning(f'No entry received, is the config server running?')


@click.command('set')
@click.argument('key')
@click.argument('new_value')
@click.option('--host',
              default=None,
              envvar='PANOPTES_CONFIG_HOST',
              help='The config server IP address or host name. First'
                   'checks cli argument, then PANOPTES_CONFIG_HOST, then localhost.')
@click.option('--port',
              default=None,
              envvar='PANOPTES_CONFIG_PORT',
              help='The config server port. First checks cli argument, '
                   'then PANOPTES_CONFIG_PORT, then 6563')
@click.option('--parse/--no-parse',
              default=True,
              help='If results should be parsed into object.')
def config_setter(key, new_value, host=None, port=None, parse=True):
    """Set an item in the config server. """
    logger.debug(f'Setting config {key=} {new_value=} on {host}:{port}')
    config_entry = set_config(key, new_value, host=host, port=port, parse=parse)
    click.echo(config_entry)


config_server_cli.add_command(run)
config_server_cli.add_command(config_setter)
config_server_cli.add_command(config_getter)
