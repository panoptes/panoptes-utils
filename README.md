[![Build Status](https://travis-ci.com/panoptes/panoptes-utils.svg?branch=master)](https://travis-ci.com/panoptes/panoptes-utils)
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/branch/master/graph/badge.svg)](https://codecov.io/gh/panoptes/panoptes-utils)

# PANOPTES Utils

Utility functions for use within the PANOPTES ecosystem and for general astronomical processing.

## Install
<a href="#" name='install'></a>

To install type:

```bash
pip install panoptes-utils
```

There are also a number of optional dependencies, which can be installed as following:

```bash
pip install "panoptes-utils[google,mongo,social,test]"
```

Or, simply:

```bash
pip install "panoptes-utils[all]"
```

## Docker

This repository creates two seaparate Docker images which act as the base for the other PANOPTES
images.  The first image (`panoptes-base`) is just the base operating system and system utilities but none of the
PANOPTES software. The second image (`panoptes-utils`) builds off the first image but adds the contents
of this repository.

There are two flavors for each image, `amd64` and `arm32v7` (Raspberry Pi).

##### panoptes-base

Included in the image:

* astrometry.net (including wide- and narrow-field index files)
* sextractor
* dcraw, exiftool
* `zsh` (and `oh-my-zsh`) by default :)

Additionally, the `amd64` image is built off of the [`continuumio/miniconda3`](https://hub.docker.com/r/continuumio/miniconda3) image so is *not* running the system python. The `arm32v7` builds the anaconda environment as part of the `panoptes-utils`.

##### panoptes-utils

Included in the image:

* `panoptes-utils` module

Additionally, the `arm32v7` image builds and installs a modified Anconda environment called [Berryconda](https://github.com/jjhelmus/berryconda).

Both the `arm32v7` and the `amd64` create a specific conda environment called `panoptes-env` that is
the base for all other environments in all PANOPTES images.

### Getting Docker Images

The `panoptes-utils` repository provides the base for the PANOPTES Docker images. The image
is public and can be obtained via `docker`:

```bash
docker pull gcr.io/panoptes-survey/panoptes-utils:latest
```

### Running Docker Containers

To run a docker image inside a container:

```bash
docker run --rm -it \
	--network host \
	gcr.io/panoptes-survey/panoptes-utils
```

> :warning: Note that we are running this with `network=host`, which opens up all network ports on
the host to the running container. As of April 2019 this still presents problems on the Mac.

### Running Docker Containers for Development

The Docker images are designed to get the correct environment working and contain a working copy of
the software repositories, however it is just as easy to map the local directories into the container
so that you can use your latest code.

```bash
docker run --rm -it \
	--network host \
	-v $PANDIR:/var/panoptes \
	gcr.io/panoptes-survey/panoptes-utils
```

Here we map all of $PANDIR to the corresponding directory inside the running container. Since the 
container had the module installed in development mode, this means that the code running in the container
now points to the file on the host machine.
