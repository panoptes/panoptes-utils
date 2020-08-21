PANOPTES Base Image
-------------------

This folder contains a [Dockerfile](https://docker.io) that builds a base
image that contains all necessary system dependencies for the `panoptes-utils` module.

The base image will install the necessary tools for working with the `panoptes-utils` 
library, such as [astrometry.net](https://astometry.net), `source-extractor`, `astropy` 
and friends, as well as various FITS libraries.  

The image itself is fairly large but should contain everything needed for running
various services.

> **Note: The base image should not be used directly for a service.**

## Image Details

Image name: `gcr.io/panoptes-exp/panoptes-base`

Tags: `latest`, `develop`

Platforms: `amd64` (`x86_64`) as well as `arm64` (`aarch64`). Other builds are 
possible but not provided by default.

Workdir: `$PANDIR` (default is `/var/panoptes`)

Entrypoint: None

Cmd: None