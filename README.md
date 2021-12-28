PANOPTES Utilities
==================

<p align="center">
<img src="https://projectpanoptes.org/uploads/2018/12/16/pan-logo.png" alt="PANOPTES logo" />
</p>
<br>

[![GHA Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fpanoptes%2Fpanoptes-utils%2Fbadge%3Fref%3Ddevelop&style=flat)](https://actions-badge.atrox.dev/panoptes/panoptes-utils/goto?ref=develop) [![Travis Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=develop)](https://travis-ci.com/panoptes/panoptes-utils) [![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/develop/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils) [![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/panoptes-utils.svg)](https://badge.fury.io/py/panoptes-utils)

Utility functions for use within the [Project PANOPTES](https://projectpanoptes.org) ecosystem and for general astronomical processing.

This library defines a number of modules that contain useful functions as well as a few services.

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

Config Server
-------------

There is a simple key-value configuration server available as part of the module.

After installing with the `config` option as above, type:

```bash
panoptes-config-server run --config-file <path-to-file.yaml>
```

Dependencies
------------

There are a few system dependencies depending on what functionality you will be using.

In particular, the plate solving requires `astrometry.net` and the appropriate index files.

Use the following on a debian-based system (e.g. Ubuntu) to install all dependencies:

```bash
apt-get update && apt-get install --no-install-recommends --yes \
  libffi-dev libssl-dev \
  astrometry.net astrometry-data-tycho2 \
  dcraw exiftool libcfitsio-dev libcfitsio-bin \
  libfreetype6-dev libpng-dev libjpeg-dev libffi-dev
```
