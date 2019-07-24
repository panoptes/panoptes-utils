# Config Server

## Starting the config server

To start the service from the command-line, use `bin/panoptes-config-server`:

```bash
➜ bin/panoptes-config-server --help
usage: panoptes-config-server [-h] [--host HOST] [--port PORT] [--public]
                              [--config-file CONFIG_FILE] [--no-save]
                              [--ignore-local] [--debug]

Start the config server for PANOPTES

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Host name, defaults to local interface.
  --port PORT           Local port, default 6563
  --public              If server should be public, default False. Note:
                        inside a docker container set this to True to expose
                        to host.
  --config-file CONFIG_FILE
                        Config file, default $PANDIR/conf_files/pocs.yaml
  --no-save             Prevent auto saving of any new values.
  --ignore-local        Ignore the local config files, default False. Mostly
                        for testing.
  --debug               Debug
```

From python, for instance when running in a jupyter notebook, you can use:

```python
>>> from panoptes.utils.config.server import config_server

>>> server_process = config_server()
...
>>> server_process.terminate()  # Or just exit notebook/console
```

## Options

### ignore_local

By default, local versions of the config files are parsed and replace any default
values. For instance, the default config file is `$PANDIR/conf_files/pocs.yaml` but
the config server will also look for and parse `$PANDIR/conf_files/pocs_local.yaml`.

This allows for overriding of default entries while still maintaing the originals.

This option can be disabled with the `ignore_local` setting.

> **Note:** Automatic tests run via `pytest` will always ignore local config files
unless they are being run with the `--hardware` options.

### auto_save

By default, changes to the config values (via `set_config`, set below) are not
preserved across restarts. Use the `auto_save` option to enable saving. When
enabled, this will write to the "local" version of the file (i.e. `pocs_local.yaml`
for the `pocs.yaml` config file).

The following are options are available for the server:

```
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
```

## Using the config server

### Python

The server can be queried/set in python:

```python
>>> from panoptes.utils.config import client

# Show the entire config item.
>>> client.get_config('location')
{'elevation': 3400.0,
 'flat_horizon': -6.0,
 'focus_horizon': -12.0,
 'gmt_offset': -600.0,
 'horizon': 30,
 'latitude': 19.54,
 'longitude': -155.58,
 'name': 'Mauna Loa Observatory',
 'observe_horizon': -18.0,
 'timezone': 'US/Hawaii'}

# Get just a specific value.
>>> client.get_config('location.horizon')
30.0

# Set to a new value.
>>> client.set_config('location.horizon', 45)
{'location.horizon': 45.0}

# Retrieve new value.
>>> client.get_config('location.horizon')
45.0

# Work with units.
>>> from astropy import units as u
>>> client.set_config('location.horizon', 45 * u.deg)
{'location.horizon': <Quantity 45. deg>}

>>> client.get_config('location.horizon')
<Quantity 45. deg>

>>> client.get_config('location')
{'elevation': 3400.0,
 'flat_horizon': -6.0,
 'focus_horizon': -12.0,
 'gmt_offset': -600.0,
 'horizon': <Quantity 45. deg>,
 'latitude': 19.54,
 'longitude': -155.58,
 'name': 'Mauna Loa Observatory',
 'observe_horizon': -18.0,
 'timezone': 'US/Hawaii'}

# Get the second camera model
>>> client.get_config('cameras.devices[1].model')
'canon_gphoto2'
```

### Command-line

Since the Flask microservice just deals with JSON documents, you can also use
[httpie](https://httpie.org/) and [jq](https://stedolan.github.io/jq/) from the command line to view
or manipulate the configuration:

Get entire config, pipe through jq and select just location.

```bash
http :6563/get-config | jq '.location'
{
  "elevation": 3400,
  "flat_horizon": -6,
  "focus_horizon": -12,
  "gmt_offset": -600,
  "horizon": "45.0 deg",
  "latitude": 19.54,
  "longitude": -155.58,
  "name": "Mauna Loa Observatory",
  "observe_horizon": -18,
  "timezone": "US/Hawaii"
}
```

`jq` can easily manipulate the json documents. Here we pipe the original output into `jq`, change two of the values, then pipe
the output back into the `set-config` endpoint provided by our Flask microservice. This will update the configuration on the server
and return the updated configuration back to the user. We simply pipe this through `jq` yet again for an easy display of the new values.
(Note the `jq` pipe `|` inside the single quotes see [jq](https://stedolan.github.io/jg/) for details.)

```bash
http :6563/get-config | jq '.location.horizon="37 deg" | .location.name="New Location"' | http :6563/set-config | jq '.location'
{
  "elevation": 3400,
  "flat_horizon": -6,
  "focus_horizon": -12,
  "gmt_offset": -600,
  "horizon": "37 deg",
  "latitude": 19.54,
  "longitude": -155.58,
  "name": "New Location",
  "observe_horizon": -18,
  "timezone": "US/Hawaii"
}
```
