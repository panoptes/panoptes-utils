PANOPTES Utilities
==================

<p align="center">
<img src="https://www.gitbook.com/cdn-cgi/image/width=256,dpr=2,height=40,fit=contain,format=auto/https%3A%2F%2F1730110767-files.gitbook.io%2F~%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252FDWxHUx4DyP5m2IEPanYp%252Flogo%252FKkSF3LQc9Zy10M3n5SQa%252F271B3C3C-4A2D-4679-884D-9892825C87E7.png%3Falt%3Dmedia%26token%3D6e7b448f-6f22-4afa-9c1c-2b3449b5f411" alt="PANOPTES Logo" />
</p>
<br>

[![GHA Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fpanoptes%2Fpanoptes-utils%2Fbadge%3Fref%3Ddevelop&style=flat)](https://actions-badge.atrox.dev/panoptes/panoptes-utils/goto?ref=develop) [![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/develop/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils) [![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/panoptes-utils.svg)](https://badge.fury.io/py/panoptes-utils)

Utility functions for use within the [Project PANOPTES](https://projectpanoptes.org) ecosystem and for general
astronomical processing.

This library defines a number of modules that contain useful functions as well as a few services.

Install
-------

To install type:

```bash
pip install panoptes-utils
```

Full options for install:

```bash
pip install "panoptes-utils[config,docs,images,testing,social]"
```

See the full documentation at: https://panoptes-utils.readthedocs.io

Dependencies
------------

There are a few system dependencies depending on what functionality you will be using.

In particular, the plate solving requires `astrometry.net` and the appropriate index files.

Use the following on a debian-based system (e.g. Ubuntu) to easily install all dependencies:

```bash
apt-get update && apt-get install --no-install-recommends --yes \
  libffi-dev libssl-dev \
  astrometry.net astrometry-data-tycho2 \
  dcraw exiftool libcfitsio-dev libcfitsio-bin \
  libfreetype6-dev libpng-dev libjpeg-dev libffi-dev
```

Command Line
------------

The `panoptes-utils` command line tool is available for use with subcommands
corresponding to the modules in this library. Currently, the only implemented
subcommand is `image`, which includes commands for converting `cr2` files into
`jpg` and/or `fits` files as well as for plate-solving `fits` images.

The `panoptes-utils image watch <path>` command will watch the given path for
new files and convert them to `jpg` and/or `fits` files as they are added.

See `panoptes-utils --help` and `panoptes-utils image --help` for details.


Config Server
-------------

There is a simple key-value configuration server available as part of the module.

After installing with the `config` option as above, type:

```bash
panoptes-config-server run --config-file <path-to-file.yaml>
```

Developing
----------

`panoptes-utils` uses [`pyscaffold`](https://pyscaffold.org/en/stable/usage.html) for project setup,
which then uses the standard `tox` and `pyproject.toml` tools to manage the project. Tests can
be run with `tox`, e.g.

```bash
# Clean repository.
tox -e clean

# Run tests.
tox

# Build project.
tox -e build
```
