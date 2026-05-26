# Configuration

PANOPTES uses a single YAML file as the source of truth for observatory configuration.
The file is human-editable and is the only place a user needs to look when setting up
or adjusting their unit.

This page covers the **file-based** configuration helpers provided by `panoptes-utils`:
typed Pydantic models and a file watcher.  For the legacy HTTP config server, see
[Config Server](config-server.md).

---

## Loading config

`load_config` reads one or more YAML files and returns a plain dict:

```python
from panoptes.utils.config import load_config

config = load_config("path/to/config.yaml")
print(config["location"]["latitude"])  # <Quantity 19.54 deg>
```

Multiple files are merged in order, with later files overriding earlier ones.
A `*_local.yaml` companion is automatically loaded when present (pass
`load_local=False` to skip this).

---

## Typed config models

`panoptes-utils` ships Pydantic v2 models for the config sections it owns.
Pass `model=` to `load_config` to get a validated instance instead of a raw dict:

```python
from panoptes.utils.config import load_config, UnitConfig

cfg = load_config("path/to/config.yaml", model=UnitConfig)

# Typed access — no dict key errors, IDE autocompletion works
print(cfg.pan_id)                  # 'PAN000'
print(cfg.location.latitude)       # <Quantity 19.54 deg>
print(cfg.location.timezone)       # 'US/Hawaii'
print(cfg.directories.base)        # '/home/panoptes'
print(cfg.earth_location)          # EarthLocation(...)
```

Models also accept raw strings for unit-bearing fields, so you can construct
them directly without going through YAML:

```python
from panoptes.utils.config.models import LocationConfig

loc = LocationConfig(
    latitude="19.54 deg",
    longitude="-155.58 deg",
    elevation="3400 m",
    timezone="US/Hawaii",
)
print(loc.latitude)   # <Quantity 19.54 deg>
```

### Available models

::: panoptes.utils.config.models.LocationConfig
    options:
      show_source: false

::: panoptes.utils.config.models.DirectoriesConfig
    options:
      show_source: false

::: panoptes.utils.config.models.DatabaseConfig
    options:
      show_source: false

::: panoptes.utils.config.models.UnitConfig
    options:
      show_source: false

### Extending for POCS

Hardware-specific config (mount, cameras, scheduler, …) lives in POCS.
`POCSConfig` will extend `UnitConfig` so the full config is validated in one shot:

```python
# In POCS (future)
from panoptes.utils.config.models import UnitConfig
from pydantic import BaseModel

class MountConfig(BaseModel): ...
class CameraConfig(BaseModel): ...

class POCSConfig(UnitConfig):
    mount: MountConfig | None = None
    cameras: CameraConfig | None = None
```

---

## Watching the config file

`ConfigWatcher` monitors a YAML file with
[watchdog](https://python-watchdog.readthedocs.io/) and fires callbacks whenever
values change.  Use it to let long-running processes react to config edits without
restarting.

```python
from panoptes.utils.config import ConfigWatcher

def on_location_change(config: dict) -> None:
    print("Location updated:", config["location"])

# Context manager — starts and stops the watcher automatically
with ConfigWatcher("path/to/config.yaml") as watcher:
    watcher.register("location", on_location_change)  # per top-level key
    watcher.register(None, lambda cfg: print("Config changed"))  # any change

    # ... run your application ...
```

Or manage the lifecycle manually:

```python
watcher = ConfigWatcher("path/to/config.yaml")
watcher.register("location", on_location_change)
watcher.start()

# ... later ...
watcher.stop()
```

Multiple callbacks can be registered for the same key.
`register(None, callback)` receives every change regardless of which key changed.
Each callback receives the **full** updated config dict.

### API reference

::: panoptes.utils.config.watcher.ConfigWatcher
    options:
      show_source: false

---

## Config file format

The config file is plain YAML.  Angle and distance values use
[astropy unit strings](https://docs.astropy.org/en/stable/units/):

```yaml
name: My PANOPTES Unit
pan_id: PAN001

location:
  name: Mauna Loa Observatory
  latitude: 19.54 deg
  longitude: -155.58 deg
  elevation: 3400.0 m
  horizon: 30 deg
  flat_horizon: -6 deg
  focus_horizon: -12 deg
  observe_horizon: -18 deg
  timezone: US/Hawaii
  gmt_offset: -600

directories:
  base: /home/panoptes
  images: images
  data: data

db:
  name: panoptes
  type: file
```

Site-specific overrides go in `config_local.yaml` alongside the main file — this
file is never committed to version control.
