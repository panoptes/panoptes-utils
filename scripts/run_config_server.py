import os
from flask import Flask
from flask import request
from flask import jsonify
from flask.json import JSONEncoder

from scalpl import Cut
from astropy import units as u

from panoptes_utils.config import load_config

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
    # If requesting specific key
    if request.is_json:
        try:
            key = request.get_json()['key']
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

            return jsonify(app.config['POCS_cut'].get(key))

    return jsonify({
        'success': False,
        'msg': "Invalid. Need json request: {'key': <config_entry>, 'value': <new_values>}"
    })


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Start the config server for PANOPTES')
    parser.add_argument('--host', default='127.0.0.1', type=str,
                        help='Host name, defaults to local interface.')
    parser.add_argument('--port', default=8888, type=int, help='Local port.')
    parser.add_argument('--public', default=False, action='store_true',
                        help='If server should be public, default False.')
    parser.add_argument('--config-file', dest='config_files', type=str, action='append')
    parser.add_argument('--debug', default=False, action='store_true', help='Debug')
    args = parser.parse_args()

    # Set public
    if args.public and args.host == '127.0.0.1':
        args.host = '0.0.0.0'

    if not args.config_files:
        # Look for main pocs file
        pocs_conf_dir = os.path.join(os.getenv('PANDIR'), 'POCS', 'conf_files')

        if os.path.isdir(pocs_conf_dir):
            print('Using default POCS config files')
            args.config_files = os.path.join(pocs_conf_dir, 'pocs')
        else:
            print('No config files given')

    app.config['POCS'] = load_config(config_files=args.config_files)
    app.config['POCS_cut'] = Cut(app.config['POCS'])

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
    )
