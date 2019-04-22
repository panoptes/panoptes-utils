from flask import Flask
from flask import request
from flask import jsonify
from flask.json import JSONEncoder

from astropy import units as u

from panoptes_utils.config import save_config

app = Flask(__name__)


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, u.Quantity):
                return obj.value
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


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

        key = req_data.get('key', None)
        if key is not None:
            val = req_data['value']

            app.config['POCS_cut'].update({key: val})

            # Config has been modified so save to file
            save_config(app.config['config_file'], app.config['POCS'])

            return jsonify(app.config['POCS_cut'].get(key))

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'key': <config_entry>, 'value': <new_values>}"
    })

