[![Build Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=master)](https://travis-ci.com/panoptes/panoptes-utils)
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/master/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils)
[![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest)

# PANOPTES Utils

Utility functions for use within the PANOPTES ecosystem and for general astronomical processing.

See the full documentation at: https://panoptes-utils.readthedocs.io

## Install
<a href="#" name='install'></a>

> :bulb: See [Docker](#docker) for ways to run that `panoptes-utils` without install.

To install type:

```bash
pip install panoptes-utils
```

There are also a number of optional dependencies, which can be installed as following:

```bash
pip install "panoptes-utils[google,mongo,social,test]"
-or-
pip install "panoptes-utils[all]"
```

## Services
<a href="#" name='services'></a>

### Config Server
<a href="#" name='config-server'></a>

A simple config param server. Runs as a Flask microservice that delivers JSON documents
in response to requests for config key items. To start the service run:

```bash
scripts/run_config_server.py
```

The server can be queried/set in python:

```python
>>> from panoptes_utils.config import client

>>> client.get_config('location.horizon')
30.0

>>> client.set_config('location.horizon', 45)
{'location.horizon': 45.0}

>>> client.get_config('location.horizon')
45.0

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

### Messaging Hub
<a href="#" name='messaging-hub'></a>

The messaging hub is responsible for relaying zeromq messages between the various components of a
PANOPTES system. Running the Messaging Hub will set up a forwarding service that allows for an arbitrary
number of publishers and subscribers.

```bash
scripts/run_messaging_hub.py --from-config
```

## Docker
<a name="docker"></a>

Docker containers are available for running the `panoptes-utils` module and associated services, which
also serve as the base container for all other PANOPTES related containers.

See our [Docker documentation](https://panoptes-utils.readthedocs.io/en/latest/docker.html) for details.
