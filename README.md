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

The `panoptes-utils` repository provides the base for the PANOPTES Docker images. The image
is public and can be obtained via `docker`:

```bash
docker pull gcr.io/panoptes-survey/panoptes-utils:latest
```

This Docker image contains the following system utilties:

	* `astrometry.net` (wide-field indexes by default)
	* `sextractor`
	* `dcraw`
	* `exiftools`
	* `zsh` (and `oh-my-zsh`) by default :)

#### Raspberry Pi

There is an `arm` build for the Raspberry Pi, which should work with the `latest` tag automatically.
If for some reason that is not working you can specify the `arm32v7` tag.

## Utils
<a href="#" name='utils'></a>

The utilities are divided up into sections. Some of the sections require optional
dependencies (e.g. the Google Cloud items). See [Install](#install) for details.
