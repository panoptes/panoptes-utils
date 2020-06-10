import logging
from flask import Flask
from flask import request
from flask import jsonify
from flask.json import JSONEncoder

from multiprocessing import Process
from scalpl import Cut

from .helpers import load_config
from .helpers import save_config
from ..logging import logger
from ..serializers import serialize_object

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
                  host='localhost',
                  port=6563,
                  ignore_local=False,
                  auto_save=False,
                  auto_start=True,
                  debug=False):
    """Start the config server in a separate process.

    A convenience function to start the config server.

    Args:
        config_file (str): The absolute path to the config file to load.
        host (str, optional): Name of host, default 'localhost'.
        port (int, optional): Port for server, default 6563.
        ignore_local (bool, optional): If local config files should be ignored, default False.
        auto_save (bool, optional): If setting new values should auto-save to local file, default False.
        auto_start (bool, optional): If server process should be started automatically, default True.
        debug (bool, optional): Flask server debug mode, default False.

    Returns:
        multiprocessing.Process: The process running the config server.
    """
    app.config['auto_save'] = auto_save
    app.config['config_file'] = config_file
    app.config['ignore_local'] = ignore_local
    app.config['POCS'] = load_config(config_files=config_file, ignore_local=ignore_local)
    logger.trace(f'Cutting the config with scalpl')
    app.config['POCS_cut'] = Cut(app.config['POCS'])
    logger.trace(f'Config cut and POCS_cut item saved')

    def start_server(**kwargs):
        try:
            logger.info(f'Starting flask config server with {kwargs=}')
            app.run(**kwargs)
        except OSError:
            logger.warning(f'Problem starting config server, is another config server already running?')
            return None

    cmd_kwargs = dict(host=host, port=port, debug=debug)
    logger.debug(f'Setting up config server process with {cmd_kwargs=}')
    server_process = Process(target=start_server,
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

    if request.is_json:
        # If requesting specific key
        try:
            key = req_json['key']
        except KeyError:
            return jsonify({
                'success': False,
                'msg': "No valid key found. Need json request: {'key': <config_entry>}"
            })

        if key is None:
            # Return all
            show_config = app.config['POCS']
        else:
            try:
                show_config = app.config['POCS_cut'].get(key, None)
            except KeyError:
                show_config = None
    else:
        # Return entire config
        show_config = app.config['POCS']

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

        # Config has been modified so save to file
        auto_save = app.config['auto_save']
        logger.info(f'Setting config {auto_save=}')
        if auto_save and app.config['config_file'] is not None:
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
            app.config['POCS'] = load_config(config_files=app.config['config_file'],
                                             ignore_local=app.config['ignore_local'])
            app.config['POCS_cut'] = Cut(app.config['POCS'])

        return jsonify({
            'success': True,
            'msg': f'Configuration reset'
        })

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'reset': True}"
    })
