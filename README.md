[![PyPI version](https://badge.fury.io/py/panoptes-utils.svg)](https://badge.fury.io/py/panoptes-utils)
[![Build Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=master)](https://travis-ci.com/panoptes/panoptes-utils)
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/master/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils)
[![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest)

# PANOPTES Utils

Utility functions for use within the PANOPTES ecosystem and for general astronomical processing.

See the full documentation at: https://panoptes-utils.readthedocs.io

# Install
<a href="#" name='install'></a>

> See [Docker](#docker) for ways to run that `panoptes-utils` without installing
to your host computer.

To install type:

```bash
pip install panoptes-utils
```

There are also a number of optional dependencies, which can be installed as following:

```bash
pip install "panoptes-utils[google,mongo,social,test]"
# -or-
pip install "panoptes-utils[all]"
```

# Services
<a href="#" name='services'></a>

## Config Server
<a href="#" name='config-server'></a>

A simple config param server. Runs as a Flask microservice that delivers JSON documents
in response to requests for config key items.

For more details and usage examples, see the [config server README](panoptes/utils/config/README.md).

```python
>>> from panoptes.utils.config.server import config_server
>>> from panoptes.utils.config import client

>>> server_process=config_server()

>>> client.get_config('location.horizon')
30.0

>>> server_process.terminate()  # Or just exit notebook/console
```

## Messaging Hub
<a href="#" name='messaging-hub'></a>

The messaging hub is responsible for relaying zeromq messages between the various components of a
PANOPTES system. Running the Messaging Hub will set up a forwarding service that allows for an arbitrary
number of publishers and subscribers.

```bash
panoptes-messaging-hub --from-config
```

## Docker
<a name="docker"></a>

Docker containers are available for running the `panoptes - utils` module and associated services, which
also serve as the base container for all other PANOPTES related containers.

See our [Docker documentation](https://panoptes-utils.readthedocs.io/en/latest/docker.html) for details.
