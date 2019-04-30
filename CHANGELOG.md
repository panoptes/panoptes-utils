# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

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

