PANOPTES Utilities
==================

<p align="center">
<img src="https://www.gitbook.com/cdn-cgi/image/width=256,dpr=2,height=40,fit=contain,format=auto/https%3A%2F%2F1730110767-files.gitbook.io%2F~%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252FDWxHUx4DyP5m2IEPanYp%252Flogo%252FKkSF3LQc9Zy10M3n5SQa%252F271B3C3C-4A2D-4679-884D-9892825C87E7.png%3Falt%3Dmedia%26token%3D6e7b448f-6f22-4afa-9c1c-2b3449b5f411" alt="PANOPTES Logo" />
</p>
<br>

[![GHA Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fpanoptes%2Fpanoptes-utils%2Fbadge%3Fref%3Dmain&style=flat)](https://actions-badge.atrox.dev/panoptes/panoptes-utils/goto?ref=main) 
[![codecov](https://codecov.io/gh/panoptes/panoptes-utils/graph/badge.svg?token=YCzESBa7rK)](https://codecov.io/gh/panoptes/panoptes-utils)
[![Documentation Status](https://img.shields.io/github/actions/workflow/status/panoptes/panoptes-utils/docs.yml?branch=main&label=docs)](https://panoptes.github.io/panoptes-utils//en/latest/?badge=latest) 
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

See the full documentation at: https://panoptes.github.io/panoptes-utils/

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

The `panoptes-utils` command provides subcommands for image processing, configuration management,
and telemetry. Use `panoptes-utils --help` or `panoptes-utils <subcommand> --help` for full
option details.

### `image` — Image processing

Convert and plate-solve astronomical images:

```bash
# Watch a directory and auto-process new files
panoptes-utils image watch <path>

# Convert a CR2 to FITS
panoptes-utils image cr2 to-fits <file.cr2>

# Plate-solve a FITS file
panoptes-utils image fits solve <file.fits>
```

### `config` — Configuration server

Requires the `config` extra (`pip install "panoptes-utils[config]"`).

Start a local key-value configuration server backed by a YAML file:

```bash
# Start the server
panoptes-utils config run --config-file <path-to-file.yaml>

# Read a value (returns entire config if no key given)
panoptes-utils config get location.elevation

# Update a value
panoptes-utils config set name "My Observatory"

# Stop the server
panoptes-utils config stop
```

| Variable | Description | Default |
|----------|-------------|---------|
| `PANOPTES_CONFIG_HOST` | Config server host address | `localhost` |
| `PANOPTES_CONFIG_PORT` | Config server port | `6563` |
| `PANOPTES_CONFIG_FILE` | YAML config file to load (CLI only) | — |

### `telemetry` — Telemetry server

Requires the `telemetry` extra (`pip install "panoptes-utils[telemetry]"`).

Start a telemetry server for recording and querying observatory events:

```bash
# Start the server
panoptes-utils telemetry run

# Display current readings (add --follow for live updates)
panoptes-utils telemetry current --follow

# Stop the server
panoptes-utils telemetry stop
```

| Variable | Description | Default |
|----------|-------------|---------|
| `PANOPTES_TELEMETRY_HOST` | Telemetry server host address | `localhost` |
| `PANOPTES_TELEMETRY_PORT` | Telemetry server port | `6562` |
| `PANOPTES_TELEMETRY_SITE_DIR` | Directory for rotated NDJSON site logs | `telemetry` |

The public telemetry model is intentionally simple: there is one telemetry feed,
and `start_run()` optionally activates a run context. When a run is active,
subsequent events are automatically associated with that run and stamped with
`meta["run_id"]`.

Example local workflow with Python:

```python
from panoptes.utils.telemetry import TelemetryClient

client = TelemetryClient()

print(client.ready())

# Before start_run(), events are recorded without any active run context.
client.post_event("weather", {"sky": "clear", "wind_mps": 2.1}, meta={"source": "demo"})

# start_run() activates the run context for subsequent events.
client.start_run(run_id="001")
event = client.post_event("status", {"state": "running"})
print(event["meta"]["run_id"])
client.stop_run()

# Or let the server create the next run automatically.
next_run = client.start_run()
print(next_run["run_id"], next_run["run_dir"])

print(client.current()["current"])

client.stop_run()
client.shutdown()
```

For server internals and HTTP API examples, see the
[Telemetry Server documentation](https://panoptes.github.io/panoptes-utils//en/latest/telemetry.html).

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
