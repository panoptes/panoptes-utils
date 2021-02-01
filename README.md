PANOPTES Utilities
==================

<p align="center">
<img src="https://projectpanoptes.org/uploads/2018/12/16/pan-logo.png" alt="PANOPTES logo" />
</p>
<br>

[![GHA Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fpanoptes%2Fpanoptes-utils%2Fbadge%3Fref%3Ddevelop&style=flat)](https://actions-badge.atrox.dev/panoptes/panoptes-utils/goto?ref=develop) [![Travis Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=develop)](https://travis-ci.com/panoptes/panoptes-utils) [![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/develop/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils) [![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/panoptes-utils.svg)](https://badge.fury.io/py/panoptes-utils)

Utility functions for use within the [Project PANOPTES](https://projectpanoptes.org) ecosystem and for general astronomical processing.

This library defines a number of modules that contain useful functions as well as a few services.

Dependencies
------------

There are a few system dependencies depending on what functionality you will be using.

In particular, the plate solving requires `astrometry.net` and the appropriate index files.

Use the following on a debian-based system (e.g. Ubuntu) to install all dependencies:

```bash
apt-get update

apt-get install --no-install-recommends --yes \
  wait-for-it \
  bzip2 ca-certificates gcc pkg-config \
  libffi-dev libssl-dev \
  astrometry.net astrometry-data-tycho2-08 astrometry-data-tycho2 \
  dcraw exiftool libcfitsio-dev libcfitsio-bin \
  libfreetype6-dev libpng-dev libjpeg-dev libffi-dev \
  git
```

Install
-------

To install type:

```bash
pip install panoptes-utils
```

Full options for install:

```bash
pip install -e ".[config,docs,images,testing,social]"
```

See the full documentation at: https://panoptes-utils.readthedocs.io

Docker Service
==============

The `docker` folder defines an image that can be used as the base for other  
PANOPTES services.

The `Dockerfile` is built by the `cloudbuild.yaml` and stored in Google  
Registry as `gcr.io/panoptes-exp/panoptes-utils:latest`.

You can pull the image like any other docker image:

```
docker pull gcr.io/panoptes-exp/panoptes-utils:latest
```

Config Server
-------------

There is also a service defined in `docker-compose.yaml` that will run the
`panoptes-config-server` cli tool.

```bash
PANOPTES_CONFIG_FILE=/path/to/config.yaml docker-compose \
    -f docker/docker-compose.yaml up
```
