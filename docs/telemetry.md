# Telemetry Server

The telemetry server provides a lightweight local HTTP API plus a Python client
for recording observatory telemetry.

## What is a "run"?

A **run** represents a single observation session — typically one night's worth
of observing, or a discrete target sequence within a night. Concretely, it is
the period between calling `start_run()` and `stop_run()`.

The server always records telemetry, but the run context changes *where* events
are stored and how they are labelled:

* **Outside a run (site stream):** Events are written to a rotating daily file,
  `site_YYYYMMDD.ndjson`, and represent persistent, site-wide readings such as
  weather conditions and ambient environment data.
* **Inside a run (run stream):** Events are written to a dedicated per-run file,
  `<run_id>/telemetry.ndjson`, and are automatically stamped with
  `meta.run_id`. This keeps each night's observation data neatly isolated.

Only one run can be active at a time. Starting a run does not interrupt
site-stream recording; both streams are active concurrently while a run is open.

```python
client = TelemetryClient()

# Site-wide event — goes to site_YYYYMMDD.ndjson
client.post_event("weather", {"sky": "clear"})

# Start an observation run for tonight
client.start_run(run_id="20260520_M42")

# Run-scoped event — goes to 20260520_M42/telemetry.ndjson, tagged with run_id
client.post_event("status", {"state": "observing", "target": "M42"})

client.stop_run()
```

## Public telemetry model

The public model is intentionally simple:

* There is one telemetry feed.
* `start_run()` activates an optional run context.
* While a run is active, new events are automatically associated with that run.
* Run-scoped events are stamped with `meta.run_id`.

Internally, the server stores always-on site telemetry separately from
run-specific telemetry, but callers normally do not need to choose between
those storage targets explicitly.

## CLI usage

Start the telemetry server:

```bash
panoptes-utils telemetry run
```

Enable verbose server logging, including one debug log line per incoming event:

```bash
panoptes-utils telemetry run --verbose
```

Stop it cleanly:

```bash
panoptes-utils telemetry stop
```

Inspect the current reading:

```bash
panoptes-utils telemetry current
```

Follow live updates by polling for changes:

```bash
panoptes-utils telemetry current --follow
```

This uses a live Rich display that refreshes in place when the current reading
changes.

Fetch one event type only:

```bash
panoptes-utils telemetry current status
```

## Python client example

```python
from panoptes.utils.telemetry import TelemetryClient

client = TelemetryClient()

client.post_event("weather", {"sky": "clear"})
client.start_run(run_id="001")
client.post_event("status", {"state": "running"})
print(client.current())   # dict[str, TelemetryEvent]
client.stop_run()
```

## HTTP API

The server listens on `localhost:6562` by default.

### Endpoints

* `GET /health` - liveness check
* `GET /ready` - readiness plus run-active status
* `GET /run` - active run metadata
* `POST /run/start` - start a run context
* `POST /run/stop` - stop the active run context
* `POST /event` - record an event in the current context
* `GET /current` - latest telemetry values keyed by event type
* `GET /current/{event_type}` - latest telemetry value for one type
* `POST /shutdown` - ask the server to exit

### `httpie` examples

```bash
# Check readiness.
http :6562/ready

# Record telemetry before a run is active.
http POST :6562/event type=weather data:='{"sky":"clear","wind_mps":2.1}'

# Start a run explicitly.
http POST :6562/run/start run_id=001

# Or let the server derive the next numeric run automatically.
http POST :6562/run/start

# Events are now associated with the active run and stamped with meta.run_id.
http POST :6562/event type=status data:='{"state":"running"}'

# Inspect the materialized current view.
http :6562/current
```

### `curl` examples

```bash
curl -s http://localhost:6562/ready

curl -s \
  -X POST http://localhost:6562/event \
  -H 'Content-Type: application/json' \
  -d '{"type":"weather","data":{"sky":"clear","wind_mps":2.1}}'

curl -s \
  -X POST http://localhost:6562/run/start \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"001"}'

curl -s \
  -X POST http://localhost:6562/event \
  -H 'Content-Type: application/json' \
  -d '{"type":"status","data":{"state":"running"}}'
```

## Return types

`TelemetryClient` methods return typed Pydantic models rather than plain dicts:

| Method | Return type |
|---|---|
| `post_event(...)` | `TelemetryEvent` |
| `current_event(type)` | `TelemetryEvent` |
| `current()` | `dict[str, TelemetryEvent]` |
| `get_current(col)` | `PanDBRecord \| None` |

Both `TelemetryEvent` and `PanDBRecord` are frozen Pydantic v2 models.  They
support attribute access (`event.seq`, `event.data`) **and** dict-style access
(`event["seq"]`, `event.get("ts")`, `"seq" in event`) for backward
compatibility with code that treats responses as plain dicts.

```python
event = client.post_event("weather", {"sky": "clear"})

# Attribute access
print(event.seq, event.ts, event.type, event.data)

# Dict-style access (backward compatible)
print(event["seq"], event.get("ts"))
print("type" in event)  # True

# Serialization
print(event.model_dump())
print(event.model_dump_json())
```

`PanDBRecord` exposes `_id` (the sequence number), `type`, `date`, and `data` —
the same keys as a `PanFileDB` record — so existing code that reads
`record["_id"]` or `"_id" in record` continues to work unchanged.

```python
record = client.get_current("weather")
if record is not None:
    print(record["_id"], record["date"], record["data"])
```



Successful event responses include:

* `seq` - monotonically increasing sequence number within the storage target
* `ts` - UTC timestamp
* `type` - event type
* `data` - event payload
* `meta` - caller metadata plus `run_id` when a run is active

Example response:

```json
{
  "seq": 1,
  "ts": "2026-03-18T00:05:48.955Z",
  "type": "status",
  "data": {"state": "running"},
  "meta": {"run_id": "001"}
}
```

## Run handling

`start_run()` and `POST /run/start` accept optional `run_dir` and
`run_id` values.

* If `run_dir` is relative, it is resolved under the configured site
  telemetry directory.
* If `run_dir` is omitted, the server uses `site_dir/run_id`.
* If both `run_dir` and `run_id` are omitted, the server derives the next
  numeric run directory under the site telemetry directory (for example
  `001`, `002`, `003`).

## Environment variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `PANOPTES_TELEMETRY_HOST` | Host address for the telemetry server. | `localhost` |
| `PANOPTES_TELEMETRY_PORT` | Port number for the telemetry server. | `6562` |
| `PANOPTES_TELEMETRY_SITE_DIR` | Directory for telemetry storage. | `telemetry/` |
