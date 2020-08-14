# Docker

The `panoptes-utils` repository serves as the base for a number of services that are running Docker. 

Terminology:

**image**: The "virtual machine" that has been built to run one specific service. 

**tag**: An `image` has a tag, typicaly `latest` and `develop`, although it could be anything. All images have tags and if left unspecified defaults to `latest`.

**container**: A running copy of a tagged `image`. There can be many containers running from a single image. They are each running their own copy and don't share between them (by default).

From the command line we typically `pull` images (either from `gcr.io` or from Docker Hub, which is the default with a command like `docker pull ubuntu`). 

All PANOPTES images are hosted on `gcr.io` at the `panoptes-exp` project. A valid
image would be `gcr.io/panoptes-exp/panoptes-utils:latest`.

## Images

### Base image

`gcr.io/panoptes-exp/panoptes-base:latest` is the base image and is available for `amd64` (`x86_64`) as well as `arm64` (`aarch64`). Other builds are possible but not provided by default.

**Note: The base image should not be used directly for a service.**

The base image will install all necessary tools for working with the `panoptes-utils` library, such as `astrometry.net`, `source-extractor`, `astropy` and friends, as well as various FITS libraries.  

This image runs as `PANUSER` with no `ENTRYPOINT` specified. The default `CMD` is a `/bin/zsh` and the `WORKDIR` is `PANDIR`.

### Utils image

`gcr.io/panoptes-exp/panoptes-utils:latest` is built on top of `panoptes-base` and merely installs the `panoptes-utils` module from `pip`.

This image runs as `PANUSER` with no `ENTRYPOINT` specified. The default `CMD` is a `/bin/zsh` and the `WORKDIR` is `PANDIR/panoptes-utils`.

## Develop and Testing Image

### Building local image

You can build a local copy of the images for testing. The easiest way is

```bash
docker/setup-local-environment.sh
``` 

This will create a `panoptes-utils:develop` image. Note that this uses the official
`gcr.io/panoptes-exp/panoptes-base:latest` image as the base. If you need to test
new system dependencies and need a new local base image, you can:

```bash
INCLUDE_BASE=true docker/setup-local-environment.sh
``` 

> Note that the `.git` folder is passed to the Docker build context when running locally.
This is because our `pyscaffold` package tool relies on `setuptools_scm` for version
numbers, which are ultimately based off the current code according to git.  This means
the local `develop` image will likely be much larger than the official `latest` image.

### Testing local image and code

After building the `develop` image (see above), you can run the tests inside a docker container via:

```bash
scripts/testing/test-software.sh
```
