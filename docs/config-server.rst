.. _config-server:

=============
Config Server
=============

The config server is a lightweight FastAPI/uvicorn web service that provides centralised
key/value configuration management.  It can run on a local machine or a remote server and
is the canonical way for PANOPTES components to share runtime configuration.

The configuration is a key/value system where keys and values must be serialisable as
valid YAML (or JSON).  Configuration can be seeded from an external YAML file; any values
updated while the server is running are, by default, saved back to a local copy of that
file.

.. note::

    The config server is an optional feature.  Install it with::

        pip install "panoptes-utils[config]"

The ``panoptes-utils config`` subcommand provides all interactions with the server:

.. code-block:: bash

    $ panoptes-utils config --help
    Usage: panoptes-utils config [OPTIONS] COMMAND [ARGS]...

      Manage the config server.

    Options:
      --help  Show this message and exit.

    Commands:
      get   Get a config value by dotted key name (e.g. 'location.elevation').
      run   Run the config server and block until it stops.
      set   Set a config value by dotted key name (e.g. 'location.elevation').
      stop  Stop the config server.

Each subcommand has its own ``--help`` option.  See below for specific usage.


Starting the config server
--------------------------

Command line
~~~~~~~~~~~~

To start the service from the command-line, use ``panoptes-utils config run``:

.. code-block:: bash

    $ panoptes-utils config run --help
    Usage: panoptes-utils config run [OPTIONS]

      Run the config server and block until it stops.

    Options:
      --host TEXT                       Host address to bind the config server to.
                                        [env var: PANOPTES_CONFIG_HOST]
      --port INTEGER                    Port number to bind the config server to.
                                        [default: 6563; env var: PANOPTES_CONFIG_PORT]
      --config-file TEXT                Path to the YAML config file to load.
                                        [env var: PANOPTES_CONFIG_FILE]
      --load-local / --no-load-local    Load local config files on startup.
                                        [default: load-local]
      --save-local / --no-save-local    Save config changes to the local file.
                                        [default: save-local]
      --heartbeat FLOAT                 Heartbeat interval in seconds.  [default: 2.0]
      --startup-timeout FLOAT           Seconds to wait for the server to become ready.
                                        [default: 30.0]
      --help                            Show this message and exit.

Example — start the server with a custom config file:

.. code-block:: bash

    $ panoptes-utils config run --config-file /path/to/config.yaml

Omitting ``--config-file`` starts the server with an empty configuration that can be
populated via ``panoptes-utils config set`` or the Python client.

Python
~~~~~~

Start the server from Python, for instance inside a Jupyter notebook:

.. code-block:: python

    from panoptes.utils.config.server import config_server

    # Returns a multiprocessing.Process; starts the server automatically.
    server_process = config_server("path/to/config.yaml")
    ...
    server_process.terminate()  # Or just exit the notebook/console

Options
-------

load\_local
~~~~~~~~~~~

By default, the server looks for a ``*_local.yaml`` companion alongside the primary config
file (e.g. ``pocs_local.yaml`` next to ``pocs.yaml``).  Any keys present in the local file
override the primary config.  This makes it easy to keep site-specific overrides separate
from version-controlled defaults.

Pass ``--no-load-local`` (or ``load_local=False`` in Python) to skip the local file
entirely.

save\_local
~~~~~~~~~~~

When ``--save-local`` is active (the default), any ``set`` operations that modify the
running config are automatically persisted back to the local file on disk.

Pass ``--no-save-local`` (or ``save_local=False`` in Python) to treat the server as purely
in-memory — useful for short-lived test sessions.

Stopping the config server
--------------------------

Command line
~~~~~~~~~~~~

Use ``panoptes-utils config stop`` to gracefully shut down a running server:

.. code-block:: bash

    $ panoptes-utils config stop
    # Custom host/port:
    $ panoptes-utils config stop --host myhost --port 7000

When the server was started with ``panoptes-utils config run`` (foreground), pressing
``Ctrl-c`` also cleanly stops it.

Using the config server
-----------------------

Python
~~~~~~

The server can be queried and updated via the Python client:

.. code-block:: python

    from panoptes.utils.config import client

    # Show the entire config.
    client.get_config('location')
    # {'elevation': 3400.0,
    #  'flat_horizon': -6.0,
    #  'focus_horizon': -12.0,
    #  'gmt_offset': -600.0,
    #  'horizon': 30,
    #  'latitude': 19.54,
    #  'longitude': -155.58,
    #  'name': 'Mauna Loa Observatory',
    #  'observe_horizon': -18.0,
    #  'timezone': 'US/Hawaii'}

    # Get just a specific value using dotted notation.
    client.get_config('location.horizon')
    # 30.0

    # Set a new value.
    client.set_config('location.horizon', 45)
    # {'location.horizon': 45.0}

    # Retrieve the updated value.
    client.get_config('location.horizon')
    # 45.0

    # Astropy Quantity values are supported.
    from astropy import units as u
    client.set_config('location.horizon', 45 * u.deg)
    # {'location.horizon': <Quantity 45. deg>}

    client.get_config('location.horizon')
    # <Quantity 45. deg>

    # Access nested list elements.
    client.get_config('cameras.devices[1].model')
    # 'canon_gphoto2'

Command-line
~~~~~~~~~~~~

``panoptes-utils config get`` fetches a key (or the entire config when no key is given)
and prints it to the console.

``panoptes-utils config set`` updates a key with a new value.

.. code-block:: bash

    $ panoptes-utils config get location
    {'elevation': 3400.0, 'flat_horizon': -6.0, ...}

    $ panoptes-utils config get location.horizon
    30.0

    $ panoptes-utils config set location.horizon '37 deg'
    {'location.horizon': <Quantity 37. deg>}

    # Return entire config (no key argument)
    $ panoptes-utils config get

See ``panoptes-utils config get --help`` and ``panoptes-utils config set --help`` for full
option details.

Environment variables
---------------------

The following environment variables are recognised by the CLI and the Python client:

========================= ======================================= ============
Variable                  Description                             Default
========================= ======================================= ============
``PANOPTES_CONFIG_HOST``  Config server host address              ``localhost``
``PANOPTES_CONFIG_PORT``  Config server port                      ``6563``
``PANOPTES_CONFIG_FILE``  YAML config file to load (CLI only)     —
========================= ======================================= ============
