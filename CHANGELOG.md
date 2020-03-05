# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- [Changelog](#changelog)
  - [[Unreleased]](#unreleased)
    - [Changed](#changed)
  - [[0.2.0] - 2020-03-04](#020---2020-03-04)
    - [Added](#added)
    - [Bug fixes](#bug-fixes)
    - [Changed](#changed-1)
  - [[0.1.0] - 2020-03-04](#010---2020-03-04)
  - [[0.0.8] - 2019-06-29](#008---2019-06-29)
    - [Added](#added-1)
    - [Bug fixes](#bug-fixes-1)
    - [Changed](#changed-2)
  - [[0.0.7] - 2019-05-26](#007---2019-05-26)
    - [Added](#added-2)
    - [Changed](#changed-3)
  - [[0.0.6] - 2019-04-29](#006---2019-04-29)
    - [Added](#added-3)
    - [Changed](#changed-4)
  - [[0.0.5] - 2019-04-09](#005---2019-04-09)
    - [Added](#added-4)
    - [Changed](#changed-5)

## [Unreleased]

### Changed
* New script for downloading data, `scripts/download-data.py`. This helped resolve some issues with the relative imports introduced in `v0.2.0` and is cleaner. (#129)

## [0.2.0] - 2020-03-04

First big overhaul of the repository. Pulls in features that were duplicated or scattered across [POCS](https://github.com/panoptes/POCS.git) and [PIAA](https://github.com/panoptes/PIAA.git). Removes a lot of code that wasn't being used or was otherwise clutter. Overhauls the logging system to use [`loguru`](https://github.com/Delgan/loguru) so things are simplified. Updates to documentation.

### Added
* Config Server
  * See the description in the [README](README.md#id11)
* [Versioneer](https://github.com/warner/python-versioneer) for version strings (#123).
* Read the docs config (#123).

### Bug fixes
* IERS Mirror (#65, #67)

### Changed
* Docker updates
  * See #68 and #75 for list.
* Logging:
  * Switch to [`loguru`](https://github.com/Delgan/loguru). This simplifies our logging system. Also gives us access to the `trace` (lower than `debug`, good for hardware and other debug we don't need to see during operation) and `success` (higher than `info`) levels, which would be nice to start implementing. (#123)
* Consistent use of relative imports. (#123)
* Documentation updates. (#97, #119, #120, #123)
* Repo cleanup. (#97, #123)
* Using GitHub Actions for testing. (#100, #101)
* Using [`pip-tools`](https://github.com/jazzband/pip-tools) for dependency management.

## [0.1.0] - 2020-03-04

Changes and cleanup on the way to a (more) stable release. See `0.2.0` for list of changes.

## [0.0.8] - 2019-06-29

Bringing things in line with updates to `POCS` for docker and `panoptes-utils` use.

### Added

* Serial handlers move to panoptes-utils from POCS.
* Tests and coverage.
* `improve_wcs` (moved from PIAA).
* `~utils.fits.getdata` to match other fits convenience functions, allowing for fpack files.

### Bug fixes

* Serialization fixes.
  * Use our serialization everywhere (e.g. messaging)
  * Closes #panoptes/POCS/issues/818
  * Closes #panoptes/POCS/issues/103

### Changed

* Setup/Install:
  * Scripts are renamed to have `panoptes` prefix.
  * Scripts are installed as part of setup.
  * Script improments to make more robust and portable.
* Docker Updates:
  * Don't use anaconda.
* Testing:
  * Overhaul of config_server use in testing.
  * Testing config file is separated from any regular config files.
* Logging:
  * Silence some 3rd party logs.


## [0.0.7] - 2019-05-26

### Added

* Added bayer utilities. :camera:
* Added Cloud SQL utilities. :cloud:

### Changed

* **Breaking** Changed namespace so no underscores, i.e. `from panoptes.utils import time`.
* Docker updates:
  * Use slim python images and not anaconda on amd64.
  * Adding zsh as default shell along with some customizations.
  * Entrypoint script properly authenticates to google cloud if possible.
  * Added amd64 only build scripts.

## [0.0.6] - 2019-04-29

### Added

* Docker containers created:
  * `panoptes-base` for base OS and system packages, including astrometry.net and friends.
  * `panoptes-utils` for container containing base utilities.
  * Script for building containers in GCR.
* Consistent JSON and YAML serializers.
* Configuration Server (Flask/JSON microservice).

### Changed

* **Minimum Python version is 3.6**
* Default PanDB type is changed to `memory`.
* Documentation updates.
* Bux fixes and code improvements.

## [0.0.5] - 2019-04-09

### Added

* Added a change log :tada:

### Changed

* Drop `orjson` and revert to `json` for the JSON serializers.
