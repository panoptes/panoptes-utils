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
    req_json = request.get_json()

    # If requesting specific key
    if request.is_json:
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

        app.config['POCS_cut'].update(req_data)

        # Config has been modified so save to file
        if app.config['auto_save'] and app.config['config_file'] is not None:
            save_config(app.config['config_file'], app.config['POCS_cut'].copy())

        return jsonify(req_data)

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'key': <config_entry>, 'value': <new_values>}"
    })
