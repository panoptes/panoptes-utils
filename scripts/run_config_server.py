#!/usr/bin/env python

import os
from scalpl import Cut

from panoptes.utils.config import load_config
from panoptes.utils.config.server import app


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(
        description='Start the config server for PANOPTES')
    parser.add_argument('--host', default='127.0.0.1', type=str,
                        help='Host name, defaults to local interface.')
    parser.add_argument('--port', default=6563, type=int, help='Local port, default 6563')
    parser.add_argument('--public', default=False, action='store_true',
                        help='If server should be public, default False. '
                        'Note: inside a docker container set this to True to expose to host.')
    parser.add_argument('--config-file', dest='config_file', type=str,
                        default=os.path.join(os.environ['PANDIR'], 'conf_files', 'pocs.yaml'),
                        help="Config file, default $PANDIR/conf_files/pocs.yaml")
    parser.add_argument('--no-save', default=False, action='store_true',
                        help='Config entries are saved automatically by default.')
    parser.add_argument('--debug', default=False, action='store_true', help='Debug')
    args = parser.parse_args()

    # Set public
    if args.public and args.host == '127.0.0.1':
        args.host = '0.0.0.0'

    if not args.config_file:
        # Look for $PANDIR/conf_files/.
        conf_dir = os.path.join(os.getenv('PANDIR'), 'conf_files')

        if os.path.isdir(conf_dir):
            print(f'Using default config files from {conf_dir}/pocs.yaml')
            args.config_file = os.path.join(conf_dir, 'pocs')
        else:
            print('No config files given')

    app.config['auto_save'] = not args.no_save
    app.config['config_file'] = args.config_file
    app.config['POCS'] = load_config(config_files=args.config_file)
    app.config['POCS_cut'] = Cut(app.config['POCS'])

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
    )
