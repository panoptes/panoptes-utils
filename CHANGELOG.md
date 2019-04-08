# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.5] - 2019-04-09
### Added
* Dockerfile and cloudbuild.yaml support amd64 and arm platforms
  * Script for building containers in GCR.

### Changed
* Drop `orjson` and revert to `json` for the JSON serializers.