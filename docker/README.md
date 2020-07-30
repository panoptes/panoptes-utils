# Docker

The `panoptes-utils` repository serves as the base for a number of services that are running Docker. 

## Base image

`gcr.io/panoptes-exp/panoptes-base:latest` is the base image and is available for `amd64` (`x86_64`) as well as `arm64` (`aarch64`). Other builds are possible but not provided by default.

**Note: The base image should not be used directly for a service.**

The base image will install all necessary tools for working with the `panoptes-utils` library, such as `astrometry.net`, `source-extractor`, `astropy` and friends, as well as various FITS libraries.  

This image runs as `PANUSER` with no `ENTRYPOINT` specified. The default `CMD` is a `/bin/zsh` and the `WORKDIR` is `PANDIR`.

## Utils image

`gcr.io/panoptes-exp/panoptes-utils:latest` is built on top of `panoptes-base` and merely installs the `panoptes-utils` module from `pip`.

This image runs as `PANUSER` with no `ENTRYPOINT` specified. The default `CMD` is a `/bin/zsh` and the `WORKDIR` is `PANDIR/panoptes-utils`.
