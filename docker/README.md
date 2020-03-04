Docker
======

- [Docker](#docker)
  - [PANOPTES Containers](#panoptes-containers)
      - [panoptes-base](#panoptes-base)
      - [panoptes-utils](#panoptes-utils)
  - [Getting Docker Images](#getting-docker-images)
  - [Running Docker Containers](#running-docker-containers)
  - [Building Docker Images](#building-docker-images)
  - [Definitions](#definitions)

## PANOPTES Containers

> See [Development](#development) for tips on how to run the containers but still use local copies of your files.

This repository creates two separate Docker images which act as the base for the other PANOPTES images.  The first image (`panoptes-base`) is just the base operating system and system utilities but none of the PANOPTES software. The second image (`panoptes-utils`) builds off the first image but adds the contents
of this repository.

There are two flavors for each image, which are tagged `amd64` and `arm32v7` (Raspberry Pi). A
[manifest](https://docs.docker.com/engine/reference/commandline/manifest/) file is created, which means
that you can simply pull `latest` and Docker will figure out which flavor you need.

> :warning: NOTE: The `arm32v7` images are outdated as of March 2020 and need to be updated. Use with caution.

Additionally, the `arm32v7` image builds and installs a modified Anconda environment called [Berryconda](https://github.com/jjhelmus/berryconda).

Both the `arm32v7` and the `amd64` create a specific conda environment called `panoptes` that is the base for all other environments in all PANOPTES images.

#### panoptes-base

Included in the image:

* astrometry.net (including wide- and narrow-field index files)
* sextractor
* dcraw, exiftool
* `zsh` (and `oh-my-zsh`) by default :)
* `jupyter-console`

Additionally, the `amd64` image is built off of the [continuumio/miniconda3](https://hub.docker.com/r/continuumio/miniconda3) image so is *not* running the system python. The `arm32v7` builds the anaconda environment as part of the `panoptes-utils`.

#### panoptes-utils

Included in the image:

* `panoptes-utils` module


## Getting Docker Images

The `panoptes-utils` repository provides the base for the PANOPTES Docker images. The image
is public and can be obtained via `docker`:

```bash
docker pull gcr.io/panoptes-exp/panoptes-utils:latest
```

## Running Docker Containers

The image contains an installed version of the `panoptes-utils` module as well as the system dependencies required to run the various scripts and functions (see [Services](../README.md#services)). The default `ENTRY_POINT` is just a shell so can run a machine with default options and get placed inside the virtual environment.

> Note that we are running this with `network=host`, which opens up all network ports on
the host to the running container. As of April 2019 this still presents problems on the Mac.

For PANOPTES purposes, the `docker-compose.yaml` defines two containers each running `panoptes-utils` image. The first container runs the configuration server (i.e. `scripts/run_config_server.py`) as a local web service and the second container runs the zeromq messaging hub (i.e. `scripts/run_messaging_hub.py`).

## Building Docker Images

`docker/build-image.sh` builds:
* `cloudbuild-base.yaml` uses `Dockerfile` to create a `panoptes-base` image.
* `cloudbuild-utils.yaml` uses `Dockerfile.utils.[amd64|rpi]` to create a `panoptes-utils` image.
  * Uses `conda-environment-[amd64|rpi].yaml` to create a conda environment called `panoptes-env`

`.travis.yaml` uses `panoptes-utils` image to run `scripts/testing/run_tests.sh` with the `$TRAVIS_BUILD_DIR` mapped to the working dir for the module.

## Definitions

**image**: A pre-built and configured Docker application (sort of like a virtualized OS environment with a running application). A Dockerfile will build an image. You download an image from a centralized server (e.g. Docker Hub or Google Cloud Registry). There is only one version of each image on your machine (although images support "tags", e.g. "latest", so you can have multiple tagged copies).

**container**: A running instance of an image. You can run many copies of a single image.