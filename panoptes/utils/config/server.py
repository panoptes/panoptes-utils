import logging
from warnings import warn
from flask import Flask
from flask import request
from flask import jsonify
from flask.json import JSONEncoder

from multiprocessing import Process
from scalpl import Cut

from ..logger import logger
from . import load_config
from . import save_config
from ..serializers import _serialize_object

logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        return _serialize_object(obj)


app.json_encoder = CustomJSONEncoder


def config_server(host='localhost',
                  port=6563,
                  config_file=None,
                  ignore_local=False,
                  auto_save=False,
                  auto_start=True,
                  debug=False):
    """Start the config server in a separate process.

    A convenience function to start the config server.

    Args:
        host (str, optional): Name of host, default 'localhost'.
        port (int, optional): Port for server, default 6563.
        config_file (str|None, optional): The config file to load, defaults to
            `$PANDIR/conf_files/pocs.yaml`.
        ignore_local (bool, optional): If local config files should be ignored,
            default False.
        auto_save (bool, optional): If setting new values should auto-save to
            local file, default False.
        auto_start (bool, optional): If server process should be started
            automatically, default True.
        debug (bool, optional): Flask server debug mode, default False.

    Returns:
        `multiprocessing.Process`: The process running the config server.
    """
    app.config['auto_save'] = auto_save
    app.config['config_file'] = config_file
    app.config['ignore_local'] = ignore_local
    app.config['POCS'] = load_config(config_files=config_file, ignore_local=ignore_local)
    app.config['POCS_cut'] = Cut(app.config['POCS'])

    def start_server(**kwargs):
        try:
            app.run(**kwargs)
        except OSError:
            warn(f'Problem starting config server, is another config server already running?')
            return None

    server_process = Process(target=start_server,
                             kwargs=dict(host=host, port=port, debug=debug),
                             name='panoptes-config-server')

    if server_process is not None and auto_start:
        try:
            server_process.start()
        except KeyboardInterrupt:
            server_process.terminate()

    return server_process


@app.route('/get-config', methods=['GET', 'POST'])
def get_config_entry():
    """Get config entries from server.

    Endpoint that responds to GET and POST requests and returns
    configuration item corresponding to provided key or entire
    configuration. The key entries should be specified in dot-notation,
    with the names corresponding to the entries stored in the configuration
    file. See the [scalpl](https://pypi.org/project/scalpl/) documentation
    for details on the dot-notation.

    The endpoint should received a JSON document with a single key named "key"
    and a value that corresponds to the desired key within the configuration.

    For example, take the following configuration:

    ```
    { 
        'location': {
            'elevation': 3400.0,
        }
    }
    ```

    To get the corresponding value for the elevation, pass a JSON document similar to:

    ```
    '{"key": "location.elevation"}'
    ```
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
    if request.is_json:
        req_data = request.get_json()

        try:
            app.config['POCS_cut'].update(req_data)
        except KeyError:
            for k, v in req_data.items():
                app.config['POCS_cut'].setdefault(k, v)

        # Config has been modified so save to file
        if app.config['auto_save'] and app.config['config_file'] is not None:
            save_config(app.config['config_file'], app.config['POCS_cut'].copy())

        return jsonify(req_data)

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'key': <config_entry>, 'value': <new_values>}"
    })


@app.route('/reset-config', methods=['POST'])
def reset_config():
    if request.is_json:
        logger.warning(f'Resetting config server')
        req_data = request.get_json()

        if req_data['reset']:
            # Reload the config
            app.config['POCS'] = load_config(config_files=app.config['config_file'],
                                             ignore_local=app.config['ignore_local'])
            app.config['POCS_cut'] = Cut(app.config['POCS'])

        return jsonify(req_data)

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'reset': True}"
    })
