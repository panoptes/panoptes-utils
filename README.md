PANOPTES Utilities
==================

<p align="center">
<img src="https://www.gitbook.com/cdn-cgi/image/width=256,dpr=2,height=40,fit=contain,format=auto/https%3A%2F%2F1730110767-files.gitbook.io%2F~%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252FDWxHUx4DyP5m2IEPanYp%252Flogo%252FKkSF3LQc9Zy10M3n5SQa%252F271B3C3C-4A2D-4679-884D-9892825C87E7.png%3Falt%3Dmedia%26token%3D6e7b448f-6f22-4afa-9c1c-2b3449b5f411" alt="PANOPTES Logo" />
</p>
<br>

[![GHA Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fpanoptes%2Fpanoptes-utils%2Fbadge%3Fref%3Ddevelop&style=flat)](https://actions-badge.atrox.dev/panoptes/panoptes-utils/goto?ref=develop) 
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/graph/badge.svg?token=YCzESBa7rK)](https://codecov.io/gh/panoptes/panoptes-utils)
[![Documentation Status](https://readthedocs.org/projects/panoptes-utils/badge/?version=latest)](https://panoptes-utils.readthedocs.io/en/latest/?badge=latest) 
[![PyPI version](https://badge.fury.io/py/panoptes-utils.svg)](https://badge.fury.io/py/panoptes-utils)

Utility functions for use within the [Project PANOPTES](https://projectpanoptes.org) ecosystem and for general
astronomical processing.

This library defines a number of modules that contain useful functions as well as a few services.

Install
-------

To install type:

```bash
pip install panoptes-utils
```

Full options for install:

```bash
pip install "panoptes-utils[config,docs,images,telemetry]"
```

See the full documentation at: https://panoptes-utils.readthedocs.io

Dependencies
------------

There are a few system dependencies depending on what functionality you will be using.

In particular, the plate solving requires `astrometry.net` and the appropriate index files.

Use the following on a debian-based system (e.g. Ubuntu) to easily install all dependencies:

```bash
apt-get update && apt-get install --no-install-recommends --yes \
  libffi-dev libssl-dev \
  astrometry.net astrometry-data-tycho2 \
  dcraw exiftool libcfitsio-dev libcfitsio-bin \
  libfreetype6-dev libpng-dev libjpeg-dev libffi-dev
```

Command Line
------------

The `panoptes-utils` command line tool is available for use with subcommands
corresponding to the modules in this library. Currently, the only implemented
subcommand is `image`, which includes commands for converting `cr2` files into
`jpg` and/or `fits` files as well as for plate-solving `fits` images.

The `panoptes-utils image watch <path>` command will watch the given path for
new files and convert them to `jpg` and/or `fits` files as they are added.

The telemetry server is also available under the main CLI as `panoptes-utils telemetry`.

See `panoptes-utils --help`, `panoptes-utils image --help`, and `panoptes-utils telemetry --help`
for details.


Config Server
-------------

There is a simple key-value configuration server available as part of the module.

After installing with the `config` option as above, type:

```bash
panoptes-config-server run --config-file <path-to-file.yaml>
```

### Environment Variables

The config server and client use the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PANOPTES_CONFIG_HOST` | The host address for the config server. | `localhost` |
| `PANOPTES_CONFIG_PORT` | The port number for the config server. | `6563` |
| `PANOPTES_CONFIG_FILE` | The YAML configuration file to load (used by CLI). | |
| `PANOPTES_DEBUG` | Enables verbose logging if set. | `False` |

Telemetry Server
----------------

After installing with the `telemetry` option as above, type:

```bash
panoptes-utils telemetry run
```

The telemetry server writes append-only NDJSON events to a rotated `site` stream and, when a run is
active, to a per-run `telemetry.ndjson` file. The site stream rotates on the local-day noon boundary.

Use `start_run` when you want subsequent telemetry to be associated with a specific observing run.
Before a run is active, events posted without an explicit `stream` are written to the `site` stream.
After `POST /run/start` or `TelemetryClient.start_run(...)`, the default event destination switches to
the `run` stream until the run is stopped. The active `run_id` is also stamped onto
subsequent run-scoped events as `meta.run_id`. If you do not provide a `run_id`,
the server uses the run directory name. Relative `run_dir` values are resolved
under the server's configured `site_dir`, and if you provide neither `run_dir`
nor `run_id`, the server creates the next numeric run directory under `site_dir`
(for example `001`, `002`, `003`).

Example local workflow with `httpie`:

```bash
# Start the server in one terminal.
panoptes-utils telemetry run

# Check readiness from another terminal.
http :6562/ready

# Record a site event.
http POST :6562/event type=weather data:='{"sky":"clear","wind_mps":2.1}'

# Start a run explicitly. From this point on, events without an explicit stream
# automatically go to the run stream and are stamped with meta.run_id=001.
http POST :6562/run/start run_id=001

# Or let the server derive the next numeric run under the configured site_dir.
http POST :6562/run/start

http POST :6562/event type=status data:='{"state":"running"}'

# Inspect the materialized current view keyed by event type.
http :6562/current

# Stop the server cleanly.
panoptes-utils telemetry stop
```

Example local workflow with Python:

```python
from panoptes.utils.telemetry import TelemetryClient

client = TelemetryClient()

print(client.ready())

# Before start_run(), the default stream is `site`.
client.post_event("weather", {"sky": "clear", "wind_mps": 2.1}, meta={"source": "demo"})

# start_run() activates the run stream and sets the default destination for
# subsequent post_event() calls to that run. The server also stamps
# each run event with meta["run_id"].
client.start_run(run_id="001")
event = client.post_event("status", {"state": "running"})
print(event["meta"]["run_id"])

# Or let the server create the next run automatically under site_dir.
next_run = client.start_run()
print(next_run["run_id"], next_run["run_dir"])

print(client.current()["current"])

client.stop_run()
client.shutdown()
```

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PANOPTES_TELEMETRY_HOST` | The host address for the telemetry server. | `localhost` |
| `PANOPTES_TELEMETRY_PORT` | The port number for the telemetry server. | `6562` |
| `PANOPTES_TELEMETRY_SITE_DIR` | Directory for rotated site NDJSON logs. | `telemetry/` |

### Development with UV

This project uses UV for fast Python package and environment management with modern PEP 735 dependency groups.

Prerequisites:
- Python 3.12+
- UV: https://docs.astral.sh/uv/ (install via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pipx install uv`).

Basic workflow:

- Create and sync a dev environment with all dependencies:
  ```bash
  # Install all optional extras and dev dependencies (recommended for development)
  uv sync --all-extras --group dev
  
  # Or install only base dependencies
  uv sync
  
  # Activate the virtual environment
  source .venv/bin/activate
  # or run commands without activating using `uv run ...`
  ```

- Install specific dependency groups as needed:
  ```bash
  # Install testing dependencies
  uv sync --group testing
  
  # Install linting tools
  uv sync --group lint
  
  # Install all dev dependencies (includes testing + lint)
  uv sync --group dev
  ```

- Install specific optional extras as needed (choose any):
  ```bash
  # Examples: config, images, docs, examples
  uv sync --extra config --extra images --extra docs
  
  # Or install all extras
  uv sync --all-extras
  ```

- Run tests:
  ```bash
  # All tests with coverage, using pytest options from pyproject.toml
  uv run pytest

  # Single test file
  uv run pytest tests/test_utils.py
  ```

- Lint / style checks:
  ```bash
  # Lint with Ruff
  uv run ruff check .
  
  # Auto-fix linting issues
  uv run ruff check --fix .
  
  # Format code with Ruff
  uv run ruff format .
  
  # Check formatting without making changes
  uv run ruff format --check .
  ```

- Build the package (wheel and sdist):
  ```bash
  uv build
  ```

- Run the CLI locally (Typer app):
  ```bash
  uv run panoptes-utils --help
  ```

- Versioning:
  Version is derived from git tags via setuptools-scm. To produce a new version, create and push a tag (e.g., `v0.1.0`).

#### [Testing]

To test the software, prefer running via UV so the right environment and options are used:

```bash
uv run pytest
```

By default all tests will be run. If you want to run one specific test, give the specific filename as an argument to `pytest`:

```bash
uv run pytest tests/test_mount.py
```
