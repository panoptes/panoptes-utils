import logging
import os
from multiprocessing import Process

from flask import Flask
from flask import jsonify
from flask import request
from flask.json import JSONEncoder
from gevent.pywsgi import WSGIServer
from scalpl import Cut

from .helpers import load_config
from .helpers import save_config
from ..logging import logger
from ..serializers import serialize_object

# Turn off noisy logging for Flask wsgi server.
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        """Custom serialization of each object.

        This method will call :func:`panoptes.utils.serializers.serialize_object` for
        each object.

        Args:
            obj (`any`): The object to serialize.

        """
        return serialize_object(obj)


app.json_encoder = CustomJSONEncoder


def config_server(config_file,
                  host=None,
                  port=None,
                  load_local=True,
                  save_local=False,
                  auto_start=True):
    """Start the config server in a separate process.

    A convenience function to start the config server.

    Args:
        config_file (str or None): The absolute path to the config file to load. Checks for
            PANOPTES_CONFIG_FILE env var and fails if not provided.
        host (str, optional): The config server host. First checks for PANOPTES_CONFIG_HOST
            env var, defaults to 'localhost'.
        port (str or int, optional): The config server port. First checks for PANOPTES_CONFIG_HOST
            env var, defaults to 6563.
        load_local (bool, optional): If local config files should be used when loading, default True.
        save_local (bool, optional): If setting new values should auto-save to local file, default False.
        auto_start (bool, optional): If server process should be started automatically, default True.

    Returns:
        multiprocessing.Process: The process running the config server.
    """
    config_file = config_file or os.environ['PANOPTES_CONFIG_FILE']
    logger.info(f'Starting panoptes-config-server with {config_file=}')
    config = load_config(config_files=config_file, load_local=load_local)
    logger.success(f'Config server Loaded {len(config)} top-level items')

    # Add an entry to control running of the server.
    config['config_server'] = dict(running=True)

    logger.success(f'{config!r}')
    cut_config = Cut(config)

    app.config['config_file'] = config_file
    app.config['save_local'] = save_local
    app.config['load_local'] = load_local
    app.config['POCS'] = config
    app.config['POCS_cut'] = cut_config
    logger.info(f'Config items saved to flask config-server')

    def start_server(host='localhost', port=6563):
        try:
            logger.info(f'Starting panoptes config server with {host}:{port}')
            http_server = WSGIServer((host, int(port)), app)
            http_server.serve_forever()
        except OSError:
            logger.warning(f'Problem starting config server, is another config server already running?')
            return None
        except Exception as e:
            logger.warning(f'Problem starting config server: {e!r}')
            return None

    host = host or os.getenv('PANOPTES_CONFIG_HOST', 'localhost')
    port = port or os.getenv('PANOPTES_CONFIG_PORT', 6563)
    cmd_kwargs = dict(host=host, port=port)
    logger.debug(f'Setting up config server process with {cmd_kwargs=}')
    server_process = Process(target=start_server,
                             daemon=True,
                             kwargs=cmd_kwargs)

    if auto_start:
        server_process.start()

    return server_process


@app.route('/get-config', methods=['GET', 'POST'])
def get_config_entry():
    """Get config entries from server.

    Endpoint that responds to GET and POST requests and returns
    configuration item corresponding to provided key or entire
    configuration. The key entries should be specified in dot-notation,
    with the names corresponding to the entries stored in the configuration
    file. See the `scalpl <https://pypi.org/project/scalpl/>`_ documentation
    for details on the dot-notation.

    The endpoint should receive a JSON document with a single key named ``"key"``
    and a value that corresponds to the desired key within the configuration.

    For example, take the following configuration:

    .. code:: javascript

        {
            'location': {
                'elevation': 3400.0,
                'latitude': 19.55,
                'longitude': 155.12,
            }
        }

    To get the corresponding value for the elevation, pass a JSON document similar to:

    .. code:: javascript

        '{"key": "location.elevation"}'

    Returns:
        str: The json string for the requested object if object is found in config.
        Otherwise a json string with ``status`` and ``msg`` keys will be returned.
    """
    req_json = request.get_json()
    verbose = req_json.get('verbose', True)
    log_level = 'DEBUG' if verbose else 'TRACE'

    # If requesting specific key
    logger.log(log_level, f'Received {req_json=}')

    if request.is_json:
        try:
            key = req_json['key']
            logger.log(log_level, f'Request contains {key=}')
        except KeyError:
            return jsonify({
                'success': False,
                'msg': "No valid key found. Need json request: {'key': <config_entry>}"
            })

        if key is None:
            # Return all
            logger.log(log_level, 'No valid key given, returning entire config')
            show_config = app.config['POCS']
        else:
            try:
                logger.log(log_level, f'Looking for {key=} in config')
                show_config = app.config['POCS_cut'].get(key, None)
            except Exception as e:
                logger.error(f'Error while getting config item: {e!r}')
                show_config = None
    else:
        # Return entire config
        logger.log(log_level, 'No valid key given, returning entire config')
        show_config = app.config['POCS']

    logger.log(log_level, f'Returning {show_config=}')
    logger.log(log_level, f'Returning {show_config!r}')
    return jsonify(show_config)


@app.route('/set-config', methods=['GET', 'POST'])
def set_config_entry():
    """Sets an item in the config.

    Endpoint that responds to GET and POST requests and sets a
    configuration item corresponding to the provided key.

    The key entries should be specified in dot-notation, with the names
    corresponding to the entries stored in the configuration file. See
    the `scalpl <https://pypi.org/project/scalpl/>`_ documentation for details
    on the dot-notation.

    The endpoint should receive a JSON document with a single key named ``"key"``
    and a value that corresponds to the desired key within the configuration.

    For example, take the following configuration:

    .. code:: javascript

        {
            'location': {
                'elevation': 3400.0,
                'latitude': 19.55,
                'longitude': 155.12,
            }
        }

    To set the corresponding value for the elevation, pass a JSON document similar to:

    .. code:: javascript

        '{"location.elevation": "1000 m"}'


    Returns:
        str: If method is successful, returned json string will be a copy of the set values.
        On failure, a json string with ``status`` and ``msg`` keys will be returned.
    """
    if request.is_json:
        req_data = request.get_json()

        try:
            app.config['POCS_cut'].update(req_data)
        except KeyError:
            for k, v in req_data.items():
                app.config['POCS_cut'].setdefault(k, v)

        # Config has been modified so save to file.
        save_local = app.config['save_local']
        logger.info(f'Setting config {save_local=}')
        if save_local and app.config['config_file'] is not None:
            save_config(app.config['config_file'], app.config['POCS_cut'].copy())

        return jsonify(req_data)

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'key': <config_entry>, 'value': <new_values>}"
    })


@app.route('/reset-config', methods=['POST'])
def reset_config():
    """Reset the configuration.

    An endpoint that accepts a POST method. The json request object
    must contain the key ``reset`` (with any value).

    The method will reset the configuration to the original configuration files that were
    used, skipping the local (and saved file).

    .. note::

        If the server was originally started with a local version of the file, those will
        be skipped upon reload. This is not ideal but hopefully this method is not used too
        much.

    Returns:
        str: A json string object containing the keys ``success`` and ``msg`` that indicate
        success or failure.
    """
    if request.is_json:
        logger.warning(f'Resetting config server')
        req_data = request.get_json()

        if req_data['reset']:
            # Reload the config
            config = load_config(config_files=app.config['config_file'],
                                 load_local=app.config['load_local'])
            # Add an entry to control running of the server.
            config['config_server'] = dict(running=True)
            app.config['POCS'] = config
            app.config['POCS_cut'] = Cut(config)

        return jsonify({
            'success': True,
            'msg': f'Configuration reset'
        })

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'reset': True}"
    })
