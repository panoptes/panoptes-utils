# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.8] - 2019-06-29
Bringing things in line with updates to POCS for docker and panoptes-utils use.
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

### Bug fixes
* Serialization fixes.
    * Use our serialization everywhere (e.g. messaging)
    * Closes #panoptes/POCS/issues/818
    * Closes #panoptes/POCS/issues/103

### Added
* Serial handlers move to panoptes-utils from POCS.
* Tests and coverage.
* `improve_wcs` (moved from PIAA).
* `~utils.fits.getdata` to match other fits convenience functions, allowing for
fpack files.

## [0.0.7] - 2019-05-26
### Changed
* **Breaking** Changed namespace so no underscores, i.e. `from panoptes.utils import time`.
* Docker updates:
  * Use slim python images and not anaconda on amd64.
  * Adding zsh as default shell along with some customizations.
  * Entrypoint script properly authenticates to google cloud if possible.
  * Added amd64 only build scripts.

### Added
* Added bayer utilities. :camera:
* Added Cloud SQL utilities. :cloud:

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

