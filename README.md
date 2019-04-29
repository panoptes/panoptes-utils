[![Build Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=master)](https://travis-ci.com/panoptes/panoptes-utils)
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/master/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils)
[![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest)

# PANOPTES Utils

Utility functions for use within the PANOPTES ecosystem and for general astronomical processing.

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
in response to requests for config key items. To start the service (in a Docker container), run:

```bash
scripts/run_config_server.py
```

The server can be queried/set in python:

```python
from panoptes_utils.config.client import get_config, set_config
from astropy import units as u

# Set new horizon limit
set_config('location.horizon', 45 * u.deg)

# Get the second camera model
get_config('cameras.devices[1].model')
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
