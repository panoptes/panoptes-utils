# Migrating from `panoptes.utils.database` to the Telemetry Server

The `panoptes.utils.database` module (`PanDB` / `PanFileDB`) was the original
mechanism for recording observatory state — weather readings, environment
sensor data, system status, and similar time-series records. Since **v0.2.55**,
the [telemetry server](telemetry.md) provides a purpose-built replacement that
is simpler, more observable, and easier to consume from any tool or language.

This guide explains the differences, recommends when to use each, and walks
through migrating existing code and archived data.

---

## What is a "run"?

A **run** is the core concept that distinguishes the telemetry server from the
old database mechanism. It represents a single observation session — one night
of observing or a discrete target sequence — bounded by explicit `start_run()`
and `stop_run()` calls.

The server records telemetry continuously, but the run context controls *where*
events land and how they are tagged:

| Context | Storage file | Automatic label |
|---|---|---|
| No run active (site stream) | `telemetry/site_YYYYMMDD.ndjson` | — |
| Run active (run stream) | `telemetry/<run_id>/telemetry.ndjson` | `meta.run_id` |

Site-stream events (weather, environment) keep flowing even while a run is
active. The two streams are always independent, so you never lose ambient data
during an observation.

`PanDB` had no equivalent concept — all records landed in the same flat files
regardless of whether an observation was in progress.

---

## Comparison at a glance

| Aspect | `PanDB` / `PanFileDB` | Telemetry server |
|---|---|---|
| **Interface** | Python class methods | HTTP REST API + Python client |
| **Access** | In-process only | Any process or language |
| **Storage format** | JSON records (one per line) in `.json` files | Append-only NDJSON (`.ndjson`) per day / per run |
| **Current snapshot** | `current_<collection>.json` | `GET /current` (in-memory, always fresh) |
| **Run scoping** | None | Explicit `start_run()` / `stop_run()` lifecycle |
| **Observability** | Read files directly | `GET /current`, `panoptes-utils telemetry current --follow` |
| **Historical query** | Manual file parsing | Standard NDJSON tooling (`jq`, `grep`, Python) |
| **Port** | None | `localhost:6562` (default) |
| **Dependencies** | None beyond panoptes-utils | `fastapi`, `uvicorn`, `requests` (part of the `config` extra) |

---

## Why the telemetry server is preferred

### Decoupled service, any client

`PanDB` is tightly coupled to the Python process that instantiates it. The
telemetry server is a separate process that any code — Python, shell scripts,
external dashboards — can talk to over HTTP.

### Live `/current` endpoint

`PanFileDB` maintains a `current_<collection>.json` file that is overwritten on
every call. The telemetry server keeps an in-memory snapshot that is always
up-to-date and instantly readable at `GET /current` or
`GET /current/{event_type}` without touching the disk.

### Structured, standard file format

`PanFileDB` appends arbitrary JSON records to per-collection `.json` files.
These are not valid NDJSON and must be parsed line-by-line with custom code.
The telemetry server writes standard
[NDJSON](https://github.com/ndjson/ndjson-spec) — one valid JSON object per
line — which is directly consumable by `jq`, `pandas`, `DuckDB`, and many
other tools.

### Run-scoped telemetry

The telemetry server has an explicit observation run lifecycle. While a run is
active (between `start_run()` and `stop_run()`), every event is automatically
stamped with `meta.run_id` and written to a dedicated per-run file
(`<run_id>/telemetry.ndjson`), while site-wide events go to a rotated daily
file (`site_YYYYMMDD.ndjson`). `PanDB` has no concept of runs.

### Better observability

```bash
# Watch live telemetry in the terminal
panoptes-utils telemetry current --follow
```

No equivalent exists for `PanDB` without writing custom file-tailing code.

---

## When to keep using `PanDB`

`PanDB` (memory variant) is still used in the test suite as a lightweight
in-process store. If you are writing unit tests that need to store and retrieve
small records without running any services, `PanDB(db_type='memory')` is still
appropriate. For all production observing code, prefer the telemetry server.

---

## Migration guide

### Code changes

`TelemetryClient` implements the full `PanDB` interface — `insert_current`,
`insert`, `get_current`, `find`, and `clear_current` — so **most code only
needs to change one line**: how the "database" is instantiated.

=== "Old (PanDB)"

    ```python
    from panoptes.utils.database import PanDB

    db = PanDB(db_type='file', db_name='panoptes')
    ```

=== "New (TelemetryClient)"

    ```python
    from panoptes.utils.telemetry import TelemetryClient

    db = TelemetryClient()  # connects to localhost:6562
    ```

After that, all existing `db.insert_current(...)`, `db.get_current(...)`, and
`db.insert(...)` calls work unchanged. `get_current` returns a
[`TelemetryEvent`](telemetry.md#return-types) — a typed object that supports the
same dict-style access as a plain PanDB record (`record["_id"]`,
`record["data"]`, etc.) so no downstream code needs to change.

```python
# These calls work without modification after switching to TelemetryClient.
db.insert_current('weather', {'sky': 'clear', 'wind_mps': 2.1})

record = db.get_current('weather')
print(record['data'])  # {'sky': 'clear', 'wind_mps': 2.1}
print(record['_id'])   # sequence number as string
```

#### Differences to be aware of

| Method | PanDB behaviour | TelemetryClient behaviour |
|---|---|---|
| `insert_current(..., store_permanently=False)` | Skips the permanent file, only updates current snapshot | Skips the NDJSON file write, only updates the in-memory current snapshot — matching PanDB semantics |
| `find(col, obj_id)` | Returns the matching record | Always returns `None`; parse NDJSON files for historical queries |
| `clear_current(type)` | Deletes `current_<type>.json` | No-op; the server manages its own in-memory snapshot |

#### Observation run lifecycle

If your code uses POCS observation sequences, wrap each sequence in a run:

```python
db.start_run(run_id='20260520_001')
# ... record events during the run ...
db.stop_run()
```

All `insert_current()` calls between `start_run()` and `stop_run()` are written
to `<site_dir>/<run_id>/telemetry.ndjson` and automatically tagged with
`meta.run_id`.

#### Starting the server

Before any client calls, the server must be running:

```bash
panoptes-utils telemetry run --site-dir /data/panoptes/telemetry
```

Or from Python (e.g. in a startup script):

```python
from panoptes.utils.telemetry.server import telemetry_server

process = telemetry_server(site_dir='/data/panoptes/telemetry')
# process is a daemon Process; join or poll as needed
```

---

### Migrating archived `json_store` data

Use the built-in `panoptes-utils telemetry migrate` command to convert existing
`json_store` files into NDJSON telemetry files:

```bash
panoptes-utils telemetry migrate \
    --source json_store/panoptes \
    --dest telemetry/migrated
```

The command:

1. Discovers all `<collection>.json` files under `--source`.
2. Parses each newline-delimited record.
3. Groups records by the date in their `date` field.
4. Writes them as `site_YYYYMMDD.ndjson` files under `--dest`, using the
   telemetry envelope format (`seq`, `ts`, `type`, `data`, `meta`).

The `current_*.json` snapshot files are ignored — they are ephemeral state that
is redundant once historical records are available.

#### Output format

Each converted record follows the standard telemetry envelope:

```json
{"seq": 1, "ts": "2026-03-18T00:05:48.955Z", "type": "weather", "data": {"sky": "clear", "wind_mps": 2.1}, "meta": {"migrated_from": "PanFileDB", "original_id": "abc123"}}
```

#### Querying converted records with `jq`

```bash
# All weather records
jq 'select(.type == "weather")' telemetry/migrated/site_20260318.ndjson

# Most recent environment reading
jq -s 'map(select(.type == "environment")) | last' telemetry/migrated/site_*.ndjson
```

---

## File layout comparison

### Old (`PanFileDB`)

```
json_store/
└── panoptes/
    ├── weather.json             # append-only records, one JSON object per line
    ├── current_weather.json     # latest snapshot (overwritten on each insert)
    ├── environment.json
    └── current_environment.json
```

Each record in `<collection>.json`:

```json
{"_id": "uuid4", "type": "weather", "date": "2026-03-18T00:05:48.955398", "data": {"sky": "clear"}}
```

### New (telemetry server)

```
telemetry/
├── site_20260318.ndjson        # site-wide events, rotated daily at local noon
├── site_20260319.ndjson
└── 001/
    └── telemetry.ndjson        # run-scoped events for run "001"
```

Each line in an NDJSON file:

```json
{"seq": 1, "ts": "2026-03-18T00:05:48.955Z", "type": "weather", "data": {"sky": "clear"}, "meta": {}}
```

---

## FAQ

**Do I need to run the telemetry server all the time?**

Yes, the server must be running for client calls to succeed. It is a lightweight
uvicorn process with negligible CPU and memory overhead. Start it at system boot
alongside your main observatory process.

**What happens if I call `post_event()` when the server is not running?**

`TelemetryClient` raises a `requests.ConnectionError`. Wrap calls in a
try/except if the telemetry server is optional in your setup.

**Can I query historical data from the telemetry server?**

The server does not expose historical queries — it only serves the current
in-memory snapshot. For historical analysis, parse the NDJSON files directly
with `jq`, `pandas`, `DuckDB`, or any NDJSON-aware tool.

**Does the telemetry server replace the config store?**

No. The config store (`panoptes.utils.config.store`) manages configuration
key-value state and is the right place for settings. The telemetry server
is for time-series observational data.
