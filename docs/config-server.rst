.. _config-server:

=============
Config Server
=============

The config server is a simple web service that runs either on a local machine or a
remote server.

The configuration is a key/value system where the keys and values must be serializable as
valid yaml (or json). Configuration can be initially defined in an external yaml file and
any values saved to the active server will by default be saved back to a copy of the yaml
file.

The module will install the ``panoptes-config-server`` for command line usage, which defines
a number of subcommands for interacting with (and starting) the server.

.. code-block::
    bash

    $ panoptes-config-server --help                                                                                                                                                                                                    ─╯
    Usage: panoptes-config-server [OPTIONS] COMMAND [ARGS]...

    Options:
      --verbose / --no-verbose  Turn on panoptes logger for utils, default False
      --help                    Show this message and exit.

    Commands:
      get  Get an item from the config server.
      run  Runs the config server with command line options.
      set  Set an item in the config server.



Each subcommand has its own ``--help`` command. See below for specific usage.


Starting the config server
--------------------------

Command line
~~~~~~~~~~~~

To start the service from the command-line, use ``panoptes-config-server run``:

.. code-block::
    bash

    $ panoptes-config-server run --help                                                                                                                                                                                                ─╯
    Usage: panoptes-config-server run [OPTIONS] CONFIG_FILE

      Runs the config server with command line options.

      This function is installed as an entry_point for the module, accessible at
      `panoptes-config-server`.

    Options:
      --host TEXT                     The config server IP address or host name,
                                      default 0.0.0.0
      --port TEXT                     The config server port, default 6563
      --save / --no-save              If the set values should be saved
                                      permanently, default True
      --ignore-local / --no-ignore-local
                                      Ignore the local config files, default
                                      False. Mostly for testing.
      --debug / --no-debug
      --help                          Show this message and exit.

Python
~~~~~~

From python, for instance when running in a jupyter notebook, you can
use:

.. code-block::
    python

    >>> from panoptes.utils.config.server import config_server

    >>> server_process = config_server()
    ...
    >>> server_process.terminate()  # Or just exit notebook/console

Options
-------

ignore\_local
~~~~~~~~~~~~~

By default, local versions of the config files are parsed and replace
any default values. For instance, the default config file is
``$PANDIR/conf_files/pocs.yaml`` but the config server will also look
for and parse ``$PANDIR/conf_files/pocs_local.yaml``.

This allows for overriding of default entries while still maintaing the
originals.

This option can be disabled with the ``ignore_local`` setting.

.. note::

    Automatic tests run via ``pytest`` will always ignore
    local config files unless they are being run with the ``--hardware``
    options.


Using the config server
-----------------------

Python
~~~~~~

The server can be queried/set in python:

.. code-block::
    python

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

Command-line
~~~~~~~~~~~~

The ``panoptes-config-server get`` command will fetch the requested key (or the entire
config if no is provided) and print it out to the console as JSON string.

The ``panoptes-config-server set`` command will set the value for the given key.

.. code-block:: bash

    $ panoptes-config-server get --key location
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

.. code-block:: bash

    $ panoptes-config-server set 'location.horizon' '37 deg'
    {'location.horizon': <Quantity 37. deg>}

See ``panoptes-config-server get --help`` and ``panoptes-config-server set --help`` for more details.
