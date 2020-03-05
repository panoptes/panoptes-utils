[![PyPI version](https://badge.fury.io/py/panoptes-utils.svg)](https://badge.fury.io/py/panoptes-utils)
[![Build Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=develop)](https://travis-ci.com/panoptes/panoptes-utils)
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/develop/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils)
[![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest)

PANOPTES Utils
--------------

- [PANOPTES Utils](#panoptes-utils)
- [Getting](#getting)
  - [pip](#pip)
  - [Docker](#docker)
- [Using](#using)
  - [Modules](#modules)
  - [Services](#services)
    - [Config Server](#config-server)
    - [Messaging Hub](#messaging-hub)
    - [Logger](#logger)
- [Development](#development)
  - [Logging](#logging)
  - [Releasing](#releasing)

Utility functions for use within the PANOPTES ecosystem and for general astronomical processing.

This library defines a number of modules that contain useful functions as well as a few
[services](#services).

See the full documentation at: https://panoptes-utils.readthedocs.io

## Getting

See [Docker](#docker) for ways to run `panoptes-utils` services without installing to your host computer.

### pip

To install type:

```bash
pip install panoptes-utils
```

There are also a number of optional dependencies, which can be installed as following:

```bash
pip install "panoptes-utils[social,testing]"
# -or-
pip install "panoptes-utils[all]"
```

### Docker

Docker containers are available for running the `panoptes-utils` module and associated services, which also serve as the base container for all other PANOPTES related containers.

See our [Docker documentation](https://panoptes-utils.readthedocs.io/en/latest/docker.html) for details.

## Using
### Modules

The modules can be used as helper utilities anywhere you would like. See the complete documentation for details: [https://panoptes-utils.readthedocs.io/en/latest/](https://panoptes-utils.readthedocs.io/en/latest/).

### Services

The services can be run either from a [docker](#docker) image or from the installed script, as described below.

#### Config Server

A simple config param server. Runs as a Flask microservice that delivers JSON documents
in response to requests for config key items.


Can be run from the installed script (defaults to `http://localhost:6563/get-config`):

```bash
$ bin/panoptes-config-server
 * Serving Flask app "panoptes.utils.config.server" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
```

Or inside a python process:

```python
>>> from panoptes.utils.config.server import config_server
>>> from panoptes.utils.config import client

>>> server_process=config_server()

>>> client.get_config('location.horizon')
30.0

>>> server_process.terminate()  # Or just exit notebook/console
```

For more details and usage examples, see the [config server README](panoptes/utils/config/README.md).

#### Messaging Hub

The messaging hub is responsible for relaying zeromq messages between the various components of a PANOPTES system. Running the Messaging Hub will set up a forwarding service that allows for an arbitrary number of publishers and subscribers.

```bash
panoptes-messaging-hub --from-config
```

#### Logger

A basic logger is defined in `panoptes.utils.logger.get_root_logger()`, which configures a [loguru](https://github.com/Delgan/loguru) logger with some defaults that are suitable to [POCS](https://github.com/panoptes/POCS).

For now this will remain part of this repository but may move directly to POCS in the future as it is likely to be unused by others.

## Development

### Logging

The `panoptes-utils` module uses [`loguru`](https://github.com/Delgan/loguru) for logging, which also serves as the basis for the POCS logger (see [Logger](#logger)).

To access the logs for the module, you can import directly from the `logger` module, i.e., `from panoptes.utils.logger import logger`. This is a simple wrapper around `luguru` with no extra configuration:

```python
>>> from panoptes.utils import CountdownTimer
>>> # No logs by default
>>> t0 = CountdownTimer(5)
>>> t0.sleep()
False

>>> # Enable the logs
>>> from panoptes.utils.logger import logger
>>> logger.enable('panoptes')

>>> t1 = CountdownTimer(5)
2020-03-04 06:42:50 | DEBUG | panoptes.utils.time:restart:162 - Restarting Timer (blocking) 5.00/5.00
>>> t1.sleep()
2020-03-04 06:42:53 | DEBUG | panoptes.utils.time:sleep:183 - Sleeping for 2.43 seconds
False
```


### Releasing

Instructions for making a new release of this module.

> Note: This should be done with the `panoptes` repo as the `origin`, **not** from a fork.

1. Make sure all relevant branches are merged into `develop`.
2. Create a release branch:
   1. `git checkout -b release-vX.X.X develop`
   2. Update the [CHANGELOG](CHANGELOG.md) as necessary.
3. Push to github and open a pull request comparing to `master`.
   1. Resolve any conflicts as necessary. These should be minimal and can hopefully be done via github.
   2. Merge PR into `master` via github, squashing the commits.
   3. From the `master` branch, tag the release `git tag vX.X.X`.
   4. Push the tags to github `git push --tags`.
5. Create a dist release and push to [PyPi](https://www.pypi.org/) (NB: you will need credentials):
   1. `python setup.py sdist bdist_wheel`
   2. `python -m twine upload dist/*`
   3. Merge the release branch into `develop` via a PR.
6. From the `master` branch, create a new docker image.
   1. `docker/build-image.sh amd64`