=========
Changelog
=========

0.2.21dev
---------

Changed
^^^^^^^

* Bump PyYaml to latest for security warning. (#222)
* Config Server  

  * Better parsing of directories entry in config server. (#222)  
  * Make config server less noisy. (#222)  


0.2.20 - 2020-06-09
-------------------

Moving to python 3.8.

Changed
^^^^^^^

* **Breaking** Python minimum version changed to ``3.8``. (#217)
* Running pytest locally will generate coverage report in terminal. (#218)
* Lots of documentation. (#218)
* Removing the environment section from the readme. (#218)
* Config Server (#217)

  * Better logging.
  * Cleaning up doctests.
  * Removing all dynamic server items from this repo as they are not needed.
  * Wait for config_server to start.
  * Fixing starting within fixture.
  * Config items no longer assume any defaults for either directories or files. A config file name is always required and it should always be an absolute path. (#218)
  * Adding test file for config items. (#218)
  * ``panoptes-config-server`` re-worked and now includes ``run``, ``get``, and ``set`` subcomamnds. (#221)

* Testing (#218)

  * Log files are rotated for each testing run.
  * Fix env vars (mostly need to make sure the `export` option exists in the `env` file.
  * Pytest commands moved to `setup.cfg` instead of `run-tests.sh`
  * Remove old markers
  * Setting `--strict-markers` options.
  * Add `astrometry` marker for tests requiring solve and `theskyx` marker for running alongside TheSkyX.
  * Coverage reports generated in xml and output in terminal.

* Serializers update. (#217)

  * Make the parsing and serializing functions public.
  * Use pendulum for parsing times instead of astropy Time.
  * Better naming of public functions. (#218)


0.2.19 - 2020-06-04
-------------------

Straight past ``0.2.19``.


Changed
^^^^^^^

* Removed `bin/panoptes-config-server` and created an entry_point in ``setup.cfg``. (#212)
* Removed old developer items in favor of those in ``panoptes-pocs``. (#212)
* Consolidate docker files, consistent naming with other repos. (#210, #212)

0.2.17 - 2020-05-30
-------------------

`0.2.16` was released with an error and this is a hotfix.

Added
^^^^^

* Added CR2 file testing to GitHub Actions. (#125, #205)
* A `wait_for_events` generic utility, mostly pulled from POCS. (#92, #206)
  * Supports single `callback` that can be used for interrupting, custom logging, etc. (#208)

Changed
^^^^^^^

* Remove the `validate_collection` requirement from the database types, making any collection is now valid. (#204)
* Rearrange some of the `panoptes.utils.database` modules. (#204)

Removed
^^^^^^^

* Remove `error.InvalidCollection`. (#204)
* Unused items in `conftest.py`. (#204)

0.2.15 - 2020-05-26
-------------------

Changed
^^^^^^^

* Convert to `pyscaffold`_. (#198)

  * Proper namespace package `panoptes`.
  * Move items to `src` folder.
  * Fix version number.
  * Fix build.
  * Fix documentation #27.
  * Move all project config to `setup.cfg`.
  * Base Docker image is run by root only.
  * Added a `testing` Dockerfile and cleaned up `latest` and `develop`.

Removed
^^^^^^^

* **Breaking** Removing all zmq based messaging services. (#200)


0.2.14 - 2020-05-23
-------------------

Added
^^^^^

* Add snappy decompression for parquet; `pyarrow` instead of `fastparquet` (#193)
* Password-less sudo for panoptes user on dev docker image (#193)
* `get_metadata` has an optional progress bar. (#194)
* Add `bayer.get_stamp_slice` for getting a stamp slice while respecting the superpixel. This was removed awhile ago and has been re-added and improved. (#196)
  * Adjusting the offsets so the center pixel is always::

    G2 B
    R  G1

Bug fixes
^^^^^^^^^

* Fix time-based search (#193)
* Fix the build (#197)
  * Removed `versioneer` in favor of `setuptools-scm` for workin version numbers.
  * Removed the MANIFEST.in
  * Added a simple `pyproject.toml`.

Changed
^^^^^^^

* **Breaking** Only support getting stars directly from the WCS, not the footprint. (#194)
  * `get_stars_from_footprint` -> `get_stars_from_wcs`
  * Better logging
  * Consistent column names for dtypes
  * Vmag bin comes from sql.
  * Allow for different RA/Dec column names.
  * Better catalog match function.
* `sextractor` param changes. (#194)
* **Breaking** `panoptes.utils.logger` -> `panoptes.utils.logger` so we can `from panoptes.utils.logging import logger` (#197)
* **Breaking** The `panoptes.utils.data.assets` module was removed and the
    `Downloader` class is placed directly within the `scripts/download-data.py` file. (#197)
* The `panopes-utils` module is not installed in editable mode in the `latest` docker image. (#197)
  * Slight clean up of latest.Dockerfile

0.2.13 - 2020-05-14
-------------------

Bug fixes
^^^^^^^^^

* Fix some passing of options between `get_solve_field` and `solve_field` that was leading to double parameter issues. (#189)

Changed
^^^^^^^

* The `panoptes.utils.data` functions use static versions of the file rather than firestore. (#192)
* Updated development environment (#191)
* `get_metadata` filter the fields at the parquet level. (#194)

0.2.12 - 2020-04-29
-------------------

Quick release to get the `panoptes.utils.sources` into the package.

Bug fixes
^^^^^^^^^

* `panoptes.utils.sources` not included in package. (#187, #188)

Changed
^^^^^^^

* Ability to pass credentials to underlying google client functions. (#187)

0.2.11 - 2020-04-29
-------------------

Added
^^^^^

* Data
    * Added basic data access components for getting observation and image metadata. (#178, #181)
    * Added a `search_observations` function for searching by various criteria. (#181)
        * Uses anonymous credentials to connect to firestore.
        * Added a basic notebook demonstrating features.
    * Adding `holoviews` and `hvplot` as required dependencies.


Bug fixes
^^^^^^^^^

* FITS Utils fixes:
    * Fix docstring return types for some functions. (#173)
    * `fpack`/`funpack` and `get_solve_field` were not properly overwriting FITS files
        under certain conditions when an uncompressed file of the same name was present alongside
        the compressed version. (#175)
    * Properly pass `args` and `kwargs` to `astropy.io.fits.getdata`. (#180)

Changed
^^^^^^^

* Docker
    * Changed developer tag from `dev` to `develop`. (#174)
* FITS Utils changes (#173):
    * Uncompressed file is always used for solve because we were occasionally seeing odd errors as described in dstndstn/astrometry.net#182. (#173)
    * :warning: `get_solve_field` will `overwrite` by default.
    * Better log output for solving.
    * Better checking for solved file at end (via `is_celestial`).
    * Cleanup the cleanup of solve files, removing `remove_extras` option.
    * Pass `kwargs` to underlying `writeto` method for `write_fits`. Needed for, e.g. `overwrite`.
    * Allow additional options to be passed to solve field functions without having to override all options. (#180)
    * Changed default options in `get_solve_field` to use `scale-low` and `scale-high` instead of `radius` (which
        requires an `ra` and `dec`). (#180)
* Changed `bin/panoptes-dev` -> `bin/panoptes-develop` for naming consistency. (#175)
* Data
    * **BREAKING** The `panoptes.utils.data.py` has moved into the `panoptes.utils.data` namespace with the relevant existing `Downloader` class placed in the `assets.py` module. (#181)
    * Changed the `get_data` (and images and observations equivalent) to `get_metadata`. (#181)

Removed
^^^^^^^

FITS Utils removals (#173):
    * Removing unused and confusing `improve_wcs`.
    * PanLogger class moved to POCS. (#186)

0.2.10 - 2020-04-13
-------------------

Added
^^^^^

* `get_stars_from_footpr  int` can accept a `WCS` directly instead of just the output from `calc_footprint()`. (#164)
* Ability to create different tags for the docker image. The `develop` directory is now used to create a `develop` image and is provided along with `latest`. (#165)
* `get_rgb_backgrounds(return_separate-True)` will now return the `Background2D` objects. (#166)
* Added BigQuery pandas dependencies. (#168)
* Added a developer image at `panoptes-utils:dev`, which is also auto-built along with the `latest` in the cloudbuild. Offers a `jupyter-lab` instance along with a number of plotting modules. Can be easily started via `panoptes-dev`. (#170, #171)

Bug fixes
^^^^^^^^^

* `image_id_from_path` and `sequence_id_from_path` can recognize a zero in the `camera_id` and `None` when no match. (#163)
* Fixed the bigquery client param for star lookup. (#164)
* Unquote paths before id matching. (#169)
* Do WCS match for all unmatched sources, not just matched sources. (#172)

Changed
^^^^^^^

* Docker entrypoint no longer tries to activate service account if `$GOOGLE_APPLICATION_CREDENTIALS` is found. The python client libraries will recognize the env var so this means we can avoid installing `gcloud` utilities just to activate. (#165)
* The `sources` module does not require a BigQuery client to be passed but can start it's own. A warning is given if `$GOOGLE_APPLICATION_CREDENTIALS` is not found. (#167)
* `lookup_point_sources` updates: default vmag range expanded so less false positive matches [4,18). (#168)
* Removed TOC from changelog. (#170)
* Sextractor param changes: (#171)
  * Threshold for detection changed from 3 pixels to 10 pixels.
  * Seeing changed from 0.7 arcsec to 15.3 arcsec. (Isn't used.)
  * Removed `class_star` from sextractor results.


0.2.9 - 2020-03-27
------------------

Pointless version bump because of issue with [PyPi](https://github.com/pypa/packaging-problems/issues/74).

0.2.8 - 2020-03-27
------------------

Thanks first-time contributer @preethi524! :tada:

Changed
^^^^^^^

* Ability to return separate RGB backgrounds. (#162)
* Increase coverage. (#161)

0.2.7 - 2020-03-22 (hotfix)
---------------------------

Added
^^^^^

* Basic serialization of `Exception`. (#160)

Bug fixes
^^^^^^^^^

* Add `args` and `kwargs` to `get_rgb_background`. (#160)

0.2.6 - 2020-03-22
------------------

Added
^^^^^

* `get_rgb_background` added to the `bayer` module. (#158)
* `getwcs` thin-wrapper added to `fits` module. (#158)
* Added `sources` utils. (#158)

Bug fixes
^^^^^^^^^

* Changed scope of test data files to `function`. (#158)

Changed
^^^^^^^

* Docker
  * Change to `python:3.8-slim-buster` for base image. Only `amd64` support for now. (#155)
  * Simplified docker files. (#155)
  * Switching from Travis to GHA: (#155)
  * Travis builds docker image before testing.
  * Travis doesn't upload coverage.
  * Don't update module inside container during entrypoint.
  * Fixed user permissions for $HOME and $PANDIR. (#155)
  * The docker container only really likes it when user id `1000` is running the system.
  * Remove GCP Cloud SQL proxy support.
  * Installed `sextractor`. (#158)
  * Added `pandas`. (#158)
  * Default `panoptes` user has password `panoptes`. (#158)

Removed
^^^^^^^

* Docker (#155)
  * Remove anaconda
* Polar alignment utils (#156)


0.2.5 - 2020-03-18
------------------

Added
^^^^^

* Github Actions testing and coverage upload. (#145)
  * Log files for testing are created as an artifact.
* `PanLogger` helper class added. Mostly handles formatting but can also track handlers. (#145)

Bug fixes
^^^^^^^^^

* Fixed top-level namespace so we can have other `panoptes` repos. (#150, fixes #137)

Changed
^^^^^^^

* Data files for testing are copied before tests. Allows for reuse of unsolved fits file. (#144)
* Fix astrometry data file directories in Docker images. (#144)

Removed
^^^^^^^

* The docker image no longer updates `panoptes-utils` when using `run-tests.sh`. (#145)

0.2.4 - 2020-03-11
------------------

Changed
^^^^^^^

* Disallow zipped packages, which also interfere with namespace (#142)

Removed
^^^^^^^

* `photutils` dependency for rectangular apertures in the `show_stamps` method.

0.2.3 - 2020-03-08
------------------

Small point release to correct namespace and remove some bloat.

Changed
^^^^^^^

* Fixed top-level namespace so we can have other `panoptes` repos. (#137)

Removed
^^^^^^^

* Dependencies that will be deprecated soon and are causing bloat: `photutils`, `scikit-image`. (#138)

Changed
^^^^^^^

* Fixed top-level namespace so we can have other `panoptes` repos (#137, #150).

0.2.2 - 2020-03-05
------------------

Mostly some cleanup from the `v0.2.0` release based on integrating all the changes into POCS.

Bug fixes
^^^^^^^^^

* Misc bugs introduced as part of last release, including to `download-data.py` script.
* Custom exceptions now properly pass `kwargs` through to parent (#135).

Changed
^^^^^^^

* New script for downloading data, `scripts/download-data.py`. This helped resolve some issues with the relative imports introduced in `v0.2.0` and is cleaner. (#129)
* All dependencies are smashed into one "feature" in `setup.py` to make `pip-tools` work well. This will fix the docker image problems introduced in `v0.2.1`. (#136)

Removed
^^^^^^^

* The `get_root_logger` and associated tests (#134).

0.2.0 - 2020-03-04
------------------

First big overhaul of the repository. Pulls in features that were duplicated or scattered across [POCS](https://github.com/panoptes/POCS.git) and [PIAA](https://github.com/panoptes/PIAA.git). Removes a lot of code that wasn't being used or was otherwise clutter. Overhauls the logging system to use [`loguru`](https://github.com/Delgan/loguru) so things are simplified. Updates to documentation.

Added
^^^^^
* Config Server
* See the description in the [README](README.md)
* [Versioneer](https://github.com/warner/python-versioneer) for version strings (#123).
* Read the docs config (#123).

Bug fixes
^^^^^^^^^
* IERS Mirror (#65, #67)

Changed
^^^^^^^
* Docker updates
* See #68 and #75 for list.
* Logging:
* Switch to [`loguru`](https://github.com/Delgan/loguru). This simplifies our logging system. Also gives us access to the `trace` (lower than `debug`, good for hardware and other debug we don't need to see during operation) and `success` (higher than `info`) levels, which would be nice to start implementing. (#123)
* Consistent use of relative imports. (#123)
* Documentation updates. (#97, #119, #120, #123)
* Repo cleanup. (#97, #123)
* Using GitHub Actions for testing. (#100, #101)
* Using [`pip-tools`](https://github.com/jazzband/pip-tools) for dependency management.

0.1.0 - 2020-03-04
------------------

Changes and cleanup on the way to a (more) stable release. See `0.2.0` for list of changes.

0.0.8 - 2019-06-29
-------------------

Bringing things in line with updates to `POCS` for docker and `panoptes-utils` use.

Added
^^^^^

* Serial handlers move to panoptes-utils from POCS.
* Tests and coverage.
* `improve_wcs` (moved from PIAA).
* `~utils.fits.getdata` to match other fits convenience functions, allowing for fpack files.

Bug fixes
^^^^^^^^^

* Serialization fixes.
  * Use our serialization everywhere (e.g. messaging)
  * Closes #panoptes/POCS/issues/818
  * Closes #panoptes/POCS/issues/103

Changed
^^^^^^^

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


0.0.7 - 2019-05-26
-------------------

Added
^^^^^

* Added bayer utilities. :camera:
* Added Cloud SQL utilities. :cloud:

Changed
^^^^^^^

* **Breaking** Changed namespace so no underscores, i.e. `from panoptes.utils import time`.
* Docker updates:
  * Use slim python images and not anaconda on amd64.
  * Adding zsh as default shell along with some customizations.
  * Entrypoint script properly authenticates to google cloud if possible.
  * Added amd64 only build scripts.

0.0.6 - 2019-04-29
-------------------

Added
^^^^^

* Docker containers created:
  * `panoptes-base` for base OS and system packages, including astrometry.net and friends.
  * `panoptes-utils` for container containing base utilities.
  * Script for building containers in GCR.
* Consistent JSON and YAML serializers.
* Configuration Server (Flask/JSON microservice).

Changed
^^^^^^^

* **Minimum Python version is 3.6**
* Default PanDB type is changed to `memory`.
* Documentation updates.
* Bux fixes and code improvements.

0.0.5 - 2019-04-09
-------------------

Added
^^^^^

* Added a change log. Yay.

Changed
^^^^^^^

* Drop `orjson` and revert to `json` for the JSON serializers.


The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

.. _pyscaffold: https://pyscaffold.org/en/latest/index.html
