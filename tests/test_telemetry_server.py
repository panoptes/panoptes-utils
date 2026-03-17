from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from panoptes.utils.telemetry.server import TelemetryService, create_app, get_system_day_key


def _read_ndjson(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_health_and_ready(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 30, tzinfo=timezone(timedelta(hours=-7)))
    client = TestClient(create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now)))

    health_response = client.get("/health")
    ready_response = client.get("/ready")

    assert health_response.status_code == 200
    assert ready_response.status_code == 200
    assert ready_response.json()["ready"] is True
    assert ready_response.json()["run_active"] is False


def test_post_event_defaults_to_system_and_updates_current(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 15, tzinfo=timezone(timedelta(hours=-7)))
    system_dir = tmp_path / "system"
    client = TestClient(create_app(TelemetryService(system_dir, now_provider=lambda: fixed_now)))

    response = client.post("/event", json={"type": "weather", "data": {"sky": "clear"}})

    assert response.status_code == 200
    payload = response.json()
    assert payload["stream"] == "system"
    assert payload["seq"] == 1
    assert payload["ts"].endswith("Z")

    current_response = client.get("/current")
    assert current_response.status_code == 200
    assert current_response.json() == {
        "stream": "system",
        "current": {
            "weather": payload,
        },
    }

    output_path = system_dir / "system_20260317.ndjson"
    assert output_path.exists()
    assert _read_ndjson(output_path) == [payload]


def test_run_events_default_to_run_stream(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 45, tzinfo=timezone(timedelta(hours=-7)))
    run_dir = tmp_path / "run-001"
    client = TestClient(create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now)))

    start_response = client.post("/run/start", json={"run_dir": str(run_dir), "meta": {"run_id": "001"}})
    event_response = client.post("/event", json={"type": "status", "data": {"state": "running"}})

    assert start_response.status_code == 200
    assert event_response.status_code == 200
    assert event_response.json()["stream"] == "run"

    output_path = run_dir / "telemetry.ndjson"
    assert output_path.exists()
    assert _read_ndjson(output_path) == [event_response.json()]


def test_posting_run_stream_without_active_run_returns_conflict(tmp_path):
    fixed_now = datetime(2026, 3, 17, 13, 45, tzinfo=UTC)
    client = TestClient(create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now)))

    response = client.post("/event", json={"type": "status", "data": {"state": "idle"}, "stream": "run"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Run stream is unavailable because no run is active"


def test_current_returns_full_snapshot(tmp_path):
    fixed_now = datetime(2026, 3, 17, 14, 0, tzinfo=UTC)
    client = TestClient(create_app(TelemetryService(tmp_path / "system", now_provider=lambda: fixed_now)))

    first = client.post("/event", json={"type": "weather", "data": {"humidity": 12}}).json()
    second = client.post("/event", json={"type": "power", "data": {"battery": 97}}).json()

    current_response = client.get("/current")
    weather_response = client.get("/current/weather")

    assert current_response.status_code == 200
    assert current_response.json() == {
        "stream": "system",
        "current": {
            "weather": first,
            "power": second,
        },
    }
    assert weather_response.status_code == 200
    assert weather_response.json() == first


def test_system_rotation_uses_previous_date_before_noon():
    before_noon = datetime(2026, 3, 17, 11, 59, tzinfo=timezone(timedelta(hours=-7)))

    assert get_system_day_key(before_noon) == "20260316"


def test_system_rotation_uses_current_date_at_or_after_noon():
    at_noon = datetime(2026, 3, 17, 12, 0, tzinfo=timezone(timedelta(hours=-7)))
    after_noon = datetime(2026, 3, 17, 15, 30, tzinfo=timezone(timedelta(hours=-7)))

    assert get_system_day_key(at_noon) == "20260317"
    assert get_system_day_key(after_noon) == "20260317"
