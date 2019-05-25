from flask import Flask
from flask import request
from flask import jsonify
from flask.json import JSONEncoder

from panoptes_utils.config import save_config
from panoptes_utils.serializers import _serialize_object

app = Flask(__name__)


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        return _serialize_object(obj)


app.json_encoder = CustomJSONEncoder


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
            show_config = app.config['POCS_cut'].get(key, None)
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
