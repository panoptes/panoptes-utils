from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from panoptes.utils.telemetry import TelemetryClient
from panoptes.utils.telemetry.server import TelemetryService, create_app


def test_telemetry_client_ready_and_health(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 30, tzinfo=UTC)
    app = create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        assert client.health() == {"ok": True}
        assert client.ready()["ready"] is True
        assert client.ready()["run_active"] is False


def test_telemetry_client_posts_and_reads_current(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 35, tzinfo=UTC)
    app = create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)
        event = client.post_event("weather", {"sky": "clear"}, meta={"source": "client"})
        current = client.current()
        current_weather = client.current_event("weather")

        assert current["current"]["weather"] == event
        assert current_weather == event


def test_telemetry_client_manages_runs(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 40, tzinfo=UTC)
    run_dir = tmp_path / "run-002"
    app = create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        started = client.start_run(str(run_dir), run_id="002")
        event = client.post_event("status", {"state": "running"})
        stopped = client.stop_run()

        assert started["run_dir"] == str(run_dir)
        assert started["run_id"] == "002"
        assert event["meta"]["run_id"] == "002"
        assert stopped["run_dir"] == str(run_dir)


def test_telemetry_client_can_start_run_without_arguments(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 42, tzinfo=UTC)
    site_dir = tmp_path / "site"
    (site_dir / "001").mkdir(parents=True)
    app = create_app(TelemetryService(site_dir, now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        started = client.start_run()

        assert started["run_id"] == "002"
        assert started["run_dir"] == str(site_dir / "002")


def test_telemetry_client_current_merges_site_and_run_context(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 45, tzinfo=UTC)
    app = create_app(TelemetryService(tmp_path / "site", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        site_weather = client.post_event("weather", {"sky": "clear"})
        client.start_run(run_id="001")
        run_status = client.post_event("status", {"state": "idle"})

        assert client.current() == {
            "current": {
                "weather": site_weather,
                "status": run_status,
            },
        }


# ---------------------------------------------------------------------------
# PanDB-compatible interface
# ---------------------------------------------------------------------------


def test_pandb_compat_insert_current_returns_seq(tmp_path):
    app = create_app(TelemetryService(tmp_path / "site"))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        obj_id = client.insert_current("weather", {"sky": "clear"})
        assert obj_id == "1"

        obj_id2 = client.insert_current("weather", {"sky": "cloudy"}, store_permanently=False)
        assert obj_id2 == "2"


def test_pandb_compat_insert_returns_seq_and_does_not_update_current(tmp_path):
    app = create_app(TelemetryService(tmp_path / "site"))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        obj_id = client.insert("weather", {"sky": "overcast"})
        assert obj_id == "1"
        # make_current=False means no current snapshot exists yet.
        assert client.get_current("weather") is None


def test_pandb_compat_get_current_returns_pandb_shape(tmp_path):
    app = create_app(TelemetryService(tmp_path / "site"))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        client.insert_current("environment", {"temp_c": 15.2})
        record = client.get_current("environment")

        assert record is not None
        assert record["data"] == {"temp_c": 15.2}
        assert record["type"] == "environment"
        assert "_id" in record
        assert "date" in record


def test_pandb_compat_get_current_returns_none_when_missing(tmp_path):
    app = create_app(TelemetryService(tmp_path / "site"))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        assert client.get_current("nonexistent") is None


def test_pandb_compat_find_returns_none(tmp_path):
    app = create_app(TelemetryService(tmp_path / "site"))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        obj_id = client.insert_current("weather", {"sky": "clear"})
        assert client.find("weather", obj_id) is None


def test_pandb_compat_clear_current_is_noop(tmp_path):
    app = create_app(TelemetryService(tmp_path / "site"))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        client.insert_current("weather", {"sky": "clear"})
        client.clear_current("weather")
        # Current snapshot is unchanged — clear_current is a no-op.
        assert client.get_current("weather") is not None
