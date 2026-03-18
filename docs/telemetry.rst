================
Telemetry Server
================

The telemetry server provides a lightweight local HTTP API plus a Python client
for recording observatory telemetry.

Public telemetry model
----------------------

The public model is intentionally simple:

* There is one telemetry feed.
* ``start_run()`` activates an optional run context.
* While a run is active, new events are automatically associated with that run.
* Run-scoped events are stamped with ``meta.run_id``.

Internally, the server stores always-on site telemetry separately from
run-specific telemetry, but callers normally do not need to choose between
those storage targets explicitly.

CLI usage
---------

Start the telemetry server:

.. code-block:: bash

    panoptes-utils telemetry run

Stop it cleanly:

.. code-block:: bash

    panoptes-utils telemetry stop

Python client example
---------------------

.. code-block:: python

    from panoptes.utils.telemetry import TelemetryClient

    client = TelemetryClient()

    client.post_event("weather", {"sky": "clear"})
    client.start_run(run_id="001")
    client.post_event("status", {"state": "running"})
    print(client.current()["current"])
    client.stop_run()

HTTP API
--------

The server listens on ``localhost:6562`` by default.

Endpoints
~~~~~~~~~

* ``GET /health`` - liveness check
* ``GET /ready`` - readiness plus run-active status
* ``GET /run`` - active run metadata
* ``POST /run/start`` - start a run context
* ``POST /run/stop`` - stop the active run context
* ``POST /event`` - record an event in the current context
* ``GET /current`` - latest telemetry values keyed by event type
* ``GET /current/{event_type}`` - latest telemetry value for one type
* ``POST /shutdown`` - ask the server to exit

``httpie`` examples
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

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

``curl`` examples
~~~~~~~~~~~~~~~~~

.. code-block:: bash

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

Response shape
--------------

Successful event responses include:

* ``seq`` - monotonically increasing sequence number within the storage target
* ``ts`` - UTC timestamp
* ``type`` - event type
* ``data`` - event payload
* ``meta`` - caller metadata plus ``run_id`` when a run is active

Example response:

.. code-block:: json

    {
      "seq": 1,
      "ts": "2026-03-18T00:05:48.955Z",
      "type": "status",
      "data": {"state": "running"},
      "meta": {"run_id": "001"}
    }

Run handling
------------

``start_run()`` and ``POST /run/start`` accept optional ``run_dir`` and
``run_id`` values.

* If ``run_dir`` is relative, it is resolved under the configured site
  telemetry directory.
* If ``run_dir`` is omitted, the server uses ``site_dir/run_id``.
* If both ``run_dir`` and ``run_id`` are omitted, the server derives the next
  numeric run directory under the site telemetry directory (for example
  ``001``, ``002``, ``003``).

Environment variables
---------------------

=============================== ====================================== ============
Variable                        Description                            Default
=============================== ====================================== ============
``PANOPTES_TELEMETRY_HOST``     Host address for the telemetry server. ``localhost``
``PANOPTES_TELEMETRY_PORT``     Port number for the telemetry server.  ``6562``
``PANOPTES_TELEMETRY_SITE_DIR`` Directory for telemetry storage.       ``telemetry/``
=============================== ====================================== ============
