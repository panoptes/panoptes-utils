[![Build Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=master)](https://travis-ci.com/panoptes/panoptes-utils)
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/master/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils)

# PANOPTES Utils

Utility functions for use within the PANOPTES ecosystem and for general astronomical processing.

## Install
<a href="#" name='install'></a>

To install type:

```
pip install panoptes-utils
```

There are also a number of optional dependencies, which can be installed as following:

```
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
scripts/start_docker_config_server.sh
```

The server can be queried/set in python:

```python
from panopes_utils.config.client import get_config, set_config

# Set new horizon limit
set_config('location.horizon', 45)

# Get the second camera model
get_config('cameras.devices[1].model')
```
