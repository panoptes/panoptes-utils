Docker Containers
=================

**image**: A pre-built and configured Docker application (i.e. virtualized OS environment with a running application). A Dockerfile will build an image. You download an image of the app. There is only one version of each image on your machine (although images support "tags", e.g. "latest", so you can have multiple tagged copies).  

**container**: A running instance of an image. You can run many copies of a single image.

This repository creates two seaparate Docker images which act as the base for the other PANOPTES
images.  The first image (`panoptes-base`) is just the base operating system and system utilities but none of the
PANOPTES software. The second image (`panoptes-utils`) builds off the first image but adds the contents
of this repository.

> :bulb: See [Development](#development) for tips on how to run the containers but still use local copies of your files.

There are two flavors for each image, which are tagged `amd64` and `arm32v7` (Raspberry Pi). A
[manifest](https://docs.docker.com/engine/reference/commandline/manifest/) file is created, which means
that you can simply pull `latest` and Docker will figure out which flavor you need.

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

The image contains an installed version of the `panoptes-utils` module as well as the system dependencies
required to run the various scripts and functions (see below). The default `CMD` is just a shell so
can run a machine with default options and get placed inside the virtual environment.

To run a docker image inside a container:

```bash
docker run --rm -it \
	--network host \
	gcr.io/panoptes-survey/panoptes-utils
```

> :warning: Note that we are running this with `network=host`, which opens up all network ports on
the host to the running container. As of April 2019 this still presents problems on the Mac.

For PANOPTES purposes, the `docker-compose.yaml` defines two containers each running `panoptes-utils` image.
The first container runs the configuration server (i.e. `scripts/run_config_server.py`) as a local web service and the second container runs the zeromq messaging hub (i.e. `scripts/run_messaging_hub.py`).

### Running Docker Containers for Development
<a name="development"></a>

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

### Building Docker Images

`scripts/build_containers.sh` builds:
* `cloudbuild-base.yaml` uses `Dockerfile` to create a `panoptes-base` image. (enabled with `--base`) 
* `cloudbuild-utils.yaml` uses `Dockerfile.utils.[amd64|rpi]` to create a `panoptes-utils` image.
  * Uses `conda-environment-[amd64|rpi.yaml` to create a conda environment called `panoptes-env`

`.travis.yaml` uses `panoptes-utils` image to run `scripts/testing/run_tests.sh` with the $TRAVIS_BUILD_DIR mapped to the working dir for the module.
