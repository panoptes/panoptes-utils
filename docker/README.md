# Docker

The `panoptes-utils` repository serves as the base for a number of services that are running Docker. 

Terminology:

**image**: The "virtual machine" that has been built with all the dependencies pre-installed.

**tag**: An `image` has a tag, typically `latest` and `develop`, although it could be anything. All images have tags and if left unspecified defaults to `latest`.

**container**: A running copy of a `tagged `image`. There can be many containers running from a single image. They are each running their own copy and don't share between them (by default).

From the command line we typically `pull` images from `gcr.io` (the default with a command like `docker pull ubuntu` is to pull from [DockerHub](https://hub.docker.com/)). 

All PANOPTES images are hosted on `gcr.io` at the `panoptes-exp` project. 

Image names for PANOPTES are thus: `<SERVER_URL>/<GOOGLE_PROJECT_ID>/<IMAGE_NAME>:<TAG>`.

A valid image would be `gcr.io/panoptes-exp/panoptes-utils:latest`.

## Images

### Base image

`gcr.io/panoptes-exp/panoptes-base:latest` is the base image and is available for `amd64` (`x86_64`) as well as `arm64` (`aarch64`). Other builds are possible but not provided by default.

**Note: The base image should not be used directly for a service.**

The base image will install all necessary tools for working with the `panoptes-utils` library, such as `astrometry.net`, `source-extractor`, `astropy` and friends, as well as various FITS libraries.  

This image runs as root with `ENTRYPOINT` passing the `CMD` to the `PANUSER` via `gosu`.  
See the `resources/docker/entrypoint.sh` for details.

The default `CMD` is a `zsh` with a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) 
activated (named `panoptes`) and the `WORKDIR` is `PANDIR`.

### Utils image

`gcr.io/panoptes-exp/panoptes-utils:latest` is built on top of `panoptes-base` and installs the `panoptes-utils` module 
(in editable mode) from the appropriate branch on Github.

## Develop and Testing Image

### Building local image

> Note: Make sure you have your ``$PANDIR`` environment variable set 
> to something like: ``PANDIR=/var/panoptes``

You can build a local copy of the images for testing. The easiest way is

```bash
INCLUDE_BASE=true scripts/setup-local-environment.sh
``` 

> Note that the `.git` folder is passed to the Docker build context when running locally.
This is because our `pyscaffold` package tool relies on `setuptools_scm` for version
numbers, which are ultimately based off the current code according to git.  This means
the local `develop` image will likely be much larger than the official `latest` image.
>
> In practice this doesn't matter because when you run the local image you usually want
> to mount the working directory anyway, e.g.
>
>     docker run -it --rm \
>         -v "${PANDIR}/panoptes-utils":/var/panoptes/panoptes-utils \
>         panoptes-utils:develop 

### Testing local image and code

After building the `develop` image (see above), you can run the tests inside a docker container via:

```bash
scripts/testing/test-software.sh
```
