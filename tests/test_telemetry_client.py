from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from panoptes.utils.telemetry import TelemetryClient, TelemetryClientError
from panoptes.utils.telemetry.server import TelemetryService, create_app


def test_telemetry_client_ready_and_health(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 30, tzinfo=UTC)
    app = create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        assert client.health() == {"ok": True}
        assert client.ready()["ready"] is True
        assert client.ready()["run_active"] is False


def test_telemetry_client_posts_and_reads_current(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 35, tzinfo=UTC)
    app = create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)
        event = client.post_event("weather", {"sky": "clear"}, meta={"source": "client"})
        current = client.current()
        current_weather = client.current_event("weather")

        assert event["stream"] == "system"
        assert current["current"]["weather"] == event
        assert current_weather == event


def test_telemetry_client_manages_runs(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 40, tzinfo=UTC)
    run_dir = tmp_path / "run-002"
    app = create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        started = client.start_run(str(run_dir), run_id="002")
        event = client.post_event("status", {"state": "running"})
        stopped = client.stop_run()

        assert started["run_dir"] == str(run_dir)
        assert started["run_id"] == "002"
        assert event["stream"] == "run"
        assert event["meta"]["run_id"] == "002"
        assert stopped["run_dir"] == str(run_dir)


def test_telemetry_client_raises_useful_error(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 45, tzinfo=UTC)
    app = create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now))

    with TestClient(app) as test_client:
        client = TelemetryClient(base_url="http://testserver", session=test_client)

        with pytest.raises(TelemetryClientError) as error_info:
            client.post_event("status", {"state": "idle"}, stream="run")

        assert error_info.value.status_code == 409
        assert error_info.value.detail == "Run stream is unavailable because no run is active"
